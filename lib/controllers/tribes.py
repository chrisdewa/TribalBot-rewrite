
from typing import Optional
from discord import Guild, Member

from lib.orm.models import LogEntry, Tribe, GuildConfig

async def create_new_tribe(
    guild: Guild,
    name: str, 
    color: int, 
    leader: Member,
    author: Optional[Member] = None,
    # TODO: add categories
) -> Tribe:
    """Creates a new tribe with the passed parameters
    It also creates a log entry for the tribe's creation

    Args:
        guild (discord.Guild): the guild of the tribe
        name (str): name of the tribe
        color (int): color of the tribe
        leader (int): the ID of the tribe leader
        author (Optional[author]): the user that called this command, defaults to tribe leader

    Returns:
        Tribe: the newly created tribe
    """
    author = author or leader
    
    guild_config, _ = await GuildConfig.get_or_create(guild_id=guild.id)
    tribe = await Tribe.create(
        guild_config=guild_config, 
        name=name,
        color=color,
        leader=leader.id
    )
    await LogEntry.create(tribe=tribe, 
                          text=f'Tribe was created with name "{tribe.name}" and id "{tribe.pk}" by user "{author}"'
                          )
    return tribe

async def get_guild_tribes(guild: Guild) -> set[Tribe]:
    """Returns a set of tribes from a given guild

    Args:
        guild (discord.Guild): the target guild

    Returns:
        set[Tribe]
    """
    tribes = await Tribe.filter(guild_config=guild.id)
    return set(tribes)

async def get_member_tribes(member: Member) -> set[Tribe]:
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
    guild_id = member.guild.id
    tribes = (
        await Tribe.filter(guild_config=guild_id, leader=member.id) +
        await Tribe.filter(guild_config=guild_id, members__contains=member.id)
    )
    return set(tribes)

