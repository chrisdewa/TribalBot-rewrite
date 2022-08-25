
from typing import Optional

from discord import Guild, Member, app_commands, Interaction

from lib.orm.models import LogEntry, Tribe, TribeCategory
from .configs import get_guild_config


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
    tribes = set(
        await Tribe.filter(guild_config=guild_config, leader=member.id) +
        await Tribe.filter(guild_config=guild_config, members__contains=member.id)
    )
    return tribes

async def autocomplete_categories(interaction: Interaction, current: str):
    guild = interaction.guild
    guild_config = await get_guild_config(guild)
    cats = await TribeCategory.filter(guild_config=guild_config, name__istartswith=current)
    return [
        app_commands.Choice(name=cat.name, value=cat.name)
        for cat in cats
    ]

async def get_tribe_category(guild: Guild, name: str):
    guild_config = await get_guild_config(guild)
    return await TribeCategory.get_or_none(guild_config=guild_config, name=name)
