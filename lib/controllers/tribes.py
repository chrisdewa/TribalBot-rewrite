
import asyncio
from typing import Optional

from discord import Guild, Member, app_commands, Interaction, Embed, Color

from lib.orm.models import LogEntry, Tribe, TribeCategory, TribeJoinApplication, TribeMember
from lib.constants import DATABASE_URL

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

def member_can_manage_tribe(member: Member, tribe: Tribe) -> bool:
    """Returns true if the member can manage the target tribe"""
    mid = member.id
    return tribe.leader == mid or tribe.manager == mid

# TODO: cache autocompletes


async def autocomplete_categories(interaction: Interaction, current: str) -> list[app_commands.Choice]:
    """Autocomplete function for categories
    """
    guild = interaction.guild
    cats = await TribeCategory.filter(guild_config_guild_id=guild.id, name__istartswith=current)
    return [
        app_commands.Choice(name=cat.name, value=cat.name)
        for cat in cats
    ]

async def autocomplete_guild_tribes(interaction: Interaction, current: str) -> list[app_commands.Choice]:
    """Autocomplete for guild tribes"""
    guild = interaction.guild
    # guild_config = await get_guild_config(guild)
    tribes = await Tribe.filter(guild_config__guild_id=guild.id, name__startswith=current)
    return [
        app_commands.Choice(name=tribe.name, value=tribe.name)
        for tribe in tribes
    ]

async def autocomplete_manageable_tribes(interaction: Interaction, current: str) -> list[app_commands.Choice]:
    """Auto complete for tribes where the user is a leader or manager"""
    guild = interaction.guild
    user = interaction.user
    coro1 = Tribe.filter(guild_config_id=guild.id, leader=user.id)
    coro2 = Tribe.filter(guild_config_id=guild.id, manager=user.id)
    tribes = set(
        tribe for sublist in
        await asyncio.gather(coro1, coro2)
        for tribe in sublist
    )
    
    return [
        app_commands.Choice(name=tribe.name, value=tribe.name)
        for tribe in tribes
    ]
    

async def get_tribe_category(guild: Guild, name: str) -> TribeCategory | None:
    """Returns a tribe category by name

    Args:
        guild (Guild): The guild the category belongs to
        name (str): the name of the category (Case Sensitive)

    Returns:
        TribeCategory | None: Returns None if no tribe was found
    """
    # guild_config = await get_guild_config(guild)
    return await TribeCategory.get_or_none(guild_config__guild_id=guild.id, name=name)


async def get_tribe_by_name(guild: Guild, name: str) -> Tribe | None:
    """Returns a Tribe for param guild with param name (case sensitivie)

    Args:
        guild (Guild): guild of the tribe
        name (str): case sensitive name of the tribe

    Returns:
        Tribe | None: the tribe if found
    """
    # guild_config = await get_guild_config(guild)
    tribe = await Tribe.get_or_none(guild_config__guild_id=guild.id, name=name)
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
    