
import asyncio
from typing import Optional

from discord import Guild, Member, app_commands, Interaction, Embed, Color

from lib.orm.models import LogEntry, Tribe, TribeCategory, TribeJoinApplication
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
        leader=leader.id
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
    guild_config = await get_guild_config(guild)
    tribes = await Tribe.filter(guild_config=guild_config)
    return set(tribes)

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
    guild_config = await get_guild_config(member.guild)
    tribes = set(await asyncio.gather(
        Tribe.filter(guild_config=guild_config, leader=member.id),
        Tribe.filter(guild_config=guild_config, members__contains=member.id)
    ))
    
    return tribes

async def autocomplete_categories(interaction: Interaction, current: str) -> list[app_commands.Choice]:
    """Autocomplete function for categories
    """
    guild = interaction.guild
    guild_config = await get_guild_config(guild)
    cats = await TribeCategory.filter(guild_config=guild_config, name__istartswith=current)
    return [
        app_commands.Choice(name=cat.name, value=cat.name)
        for cat in cats
    ]

async def autocomplete_tribes(interaction: Interaction, current: str) -> list[app_commands.Choice]:
    """Autocomplete for guild tribes"""
    guild = interaction.guild
    guild_config = await get_guild_config(guild)
    tribes = await Tribe.filter(guild_config=guild_config, name__startswith=current)
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
    guild_config = await get_guild_config(guild)
    return await TribeCategory.get_or_none(guild_config=guild_config, name=name)


async def get_tribe_by_name(guild: Guild, name: str) -> Tribe | None:
    """Returns a Tribe for param guild with param name (case sensitivie)

    Args:
        guild (Guild): guild of the tribe
        name (str): case sensitive name of the tribe

    Returns:
        Tribe | None: the tribe if found
    """
    guild_config = await get_guild_config(guild)
    tribe = await Tribe.get_or_none(guild_config=guild_config, name=name)
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
    if cat in await get_member_categories(applicant):
        return
    else:
        application =  await TribeJoinApplication.create(tribe=tribe, applicant=applicant.id)
                
        return application
     

async def accept_applicant(applicant: Member, application: TribeJoinApplication):
    """
    Allows a member into a tribe. 
    Only works under these conditions:
        - the member doesn't have other tribes in the same category
    
    """
    tribe = await application.tribe
    
    cats = await get_member_categories(applicant)
    if tribe.category not in cats:
        tribe.members.append(applicant.id)
        await tribe.save()
        await application.delete()
    else:
        raise BadTribeCategory('Member is already a part of another tribe in this category')
    