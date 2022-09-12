
import asyncio
import random
from typing import Optional

from discord import Guild, Member, app_commands, Interaction, Embed, Color

from tribalbot.src.orm.models import LogEntry, Tribe, TribeCategory, TribeJoinApplication, TribeMember
from tribalbot.src.constants import DATABASE_URL
from tribalbot.src.utils.tribes import TribeMemberCollection

from .configs import get_guild_config
from .errors import BadTribeCategory, InvalidMember


async def create_new_tribe(
    guild: Guild,
    name: str, 
    color: int, 
    leader: Member,
    author: Optional[Member] = None,
    category: Optional[str] = None
) -> Tribe:
    """Creates a new tribe with the passed parameters
    It also creates a log entry for the tribe's creation

    Args:
        guild (discord.Guild): the guild of the tribe
        name (str): name of the tribe
        color (int): color of the tribe
        leader (discord.Member): the ID of the tribe leader
        author (Optional[discord.Member]): the user that called this command, defaults to tribe leader
        category (str): The name of the category for the tribe

    Returns:
        Tribe: the newly created tribe
    """
    author = author or leader
    
    guild_config = await get_guild_config(guild)
    
    tribe = await Tribe.create(
        guild_config=guild_config, 
        name=name,
        color=color,
        leader=leader.id,
        category=category
    )
    
    await LogEntry.create(
        tribe=tribe, 
        text=f'Tribe was created with name "{tribe.name}" and id "{tribe.pk}" by user "{author}"'
    )
    
    return tribe

async def get_all_guild_tribes(guild: Guild) -> set[Tribe]:
    """Returns a set of tribes from a given guild

    Args:
        guild (discord.Guild): the target guild

    Returns:
        set[Tribe]
    """
    tribes = await Tribe.filter(guild_config__guild_id=guild.id)
    return set(tribes)

async def query_member_in_tribes(member: Member) -> set[Tribe]:
    """Returns all the tribes a member belongs to"""
    guild = member.guild
    
    memberships = await TribeMember.filter(member_id=member.id, tribe__guild_config__guild_id=guild.id)
    return {await m.tribe for m in memberships}
    
async def get_all_member_tribes(member: Member) -> set[Tribe]:
    """Returns a set of tribes a given member belongs to.
    It will only return tribes from the member's object guild.
    The following criteria are considered:
        - The member is a leader
        - The member is part of the tribe's members

    Args:
        member (discord.Member): the target member

    Returns:
        set[Tribe]
    """
    # guild_config = await get_guild_config(member.guild)
    guild = member.guild
    
    tribes = set(
        tribe for result in 
        await asyncio.gather(
            Tribe.filter(guild_config__guild_id=guild.id, leader=member.id),
            query_member_in_tribes(member)
        )
        for tribe in result
    )
    
    return tribes
    

async def get_tribe_category(guild: Guild, name: str) -> TribeCategory | None:
    """Returns a tribe category by name

    Args:
        guild (Guild): The guild the category belongs to
        name (str): the name of the category (Case Sensitive)

    Returns:
        TribeCategory | None: Returns None if no tribe was found
    """
    return await TribeCategory.get_or_none(guild_config_id=guild.id, name=name)


async def get_tribe_by_name(guild: Guild, name: str) -> Tribe | None:
    """Returns a Tribe for param guild with param name (case sensitivie)

    Args:
        guild (Guild): guild of the tribe
        name (str): case sensitive name of the tribe

    Returns:
        Tribe | None: the tribe if found
    """

    tribe = await Tribe.get_or_none(guild_config_id=guild.id, name=name)
    return tribe

async def get_member_categories(member: Member) -> set[TribeCategory]:
    tribes = await get_all_member_tribes(member)
    cats = {await tribe.category for tribe in tribes}
    return cats

async def create_tribe_join_application(tribe: Tribe, interaction: Interaction) -> TribeJoinApplication | None:
    """Creates a join application in the target tribe for the applicant (interaction.user)
    Also creates a log entry in the tribe and notifies the tribe leader and manager
    
    returns:
        TribeJoinApplication | None: the application of the member to the target tribe
    """
    applicant: Member = interaction.user
    
    cat = await tribe.category
    member_cats = await get_member_categories(applicant)
    if cat in member_cats:
        return
    else:
        application =  await TribeJoinApplication.create(tribe=tribe, applicant=applicant.id)
        return application
    
async def get_tribe_applications(tribe: Tribe) -> list[TribeJoinApplication]:
    """Returns all current tribe applications"""
    return await tribe.join_applications

async def accept_applicant(applicant: Member, application: TribeJoinApplication):
    """
    Allows a member into a tribe. 
    Only works under these conditions:
        - the member doesn't have other tribes in the same category
    
    """
    tribe = await application.tribe
    
    cats = await get_member_categories(applicant)
    if tribe.category not in cats:
        await TribeMember.create(tribe=tribe, member_id=applicant.id)
        await application.delete()
    else:
        raise BadTribeCategory('Member is already a part of another tribe in this category')


async def parse_tribe_members(tribe: Tribe, guild: Guild) -> set[Member]:
    """Returns a set of discord.Member from the tribe's members
    Only returns those members that are currently part of the server"""
    return {
        member for tm in await tribe.members
        if (member := guild.get_member(tm.member_id))
    }

async def prune_tribe_members(tribe: Tribe, guild: Guild) -> set[int]:
    """remove the tribe members that are no longer part of the guild"""
    members = await tribe.members
    to_prune = []
    prunned = set()
    for tm in members:
        if not guild.get_member(tm.member_id):
            to_prune.append(tm.delete())
            prunned.add(tm.member_id)
    await asyncio.gather(*to_prune)
    return prunned
    

async def handle_leader_leave(
    tribe: Tribe, 
    *, 
    members: TribeMemberCollection | None = None, 
    new_leader: int | None = None
) -> bool:
    """This handles a tribe leader that is leaving the tribe
    Works if the leader was forced to leave by an admin or 
    if the leader exits the tribe without disbanding or 
    appointing a successor
    
    Args:
        tribe (Tribe): the target tribe
        members (TribeMembersCollection | None): a collection of the tribe members if any
        new_leader (int | None): an optional new leader id
            - if the new_leader id is a member from the tribe 
                it will be removed as a member
            - if not supplied the manager will take the charge of leader
            - if there's no manager, a new leader will be randomly selected
                from the tribes members
            - if there's no members left the tribe is deleted
    Returns:
        bool:
            True: if the tribe still exists
            False: if the tribe was deleted
    """
    members = members or TribeMemberCollection(await tribe.members)
    if new_leader:
        if new_leader in members.ids: # the new leader is part of the tribe members
            await members.remove_member(new_leader) # we first remove the leader from the members
            if new_leader == tribe.manager:
                tribe.manager = None
                
    else:
        if members.ids: # there are members in this tribe
            if tribe.manager: # there's a manager so let's pick them
                new_leader = tribe.manager
                tribe.manager = None
                await members.remove_member(new_leader)
            else: # there isn't a manager so let's pick at random from the tribe members
                new_leader = random.choice(members.ids)
                await members.remove_member(new_leader)
            
        else: # there are no more users in this tribe, we delete it and return False
            await tribe.delete()
            return False
        
    # if we haven't returned then we have a new leader 
    tribe.leader = new_leader
    await tribe.save() # all other changes have already been made
    
    return True    

    
