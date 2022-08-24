
from discord import Guild, Member, ApplicationContext

from lib.orm.models import LogEntry, Tribe, GuildConfig

async def create_new_tribe(
    ctx: ApplicationContext, 
    name: str, 
    color: int, 
    leader: int
    # TODO: add categories
) -> Tribe:    
    guild_config, _ = await GuildConfig.get_or_create(guild_id=ctx.guild.id)
    tribe = await Tribe.create(
        guild_config=guild_config, 
        name=name,
        color=color,
        leader=leader
    )
    await LogEntry.create(tribe=tribe, 
                          text=f'Tribe was created with name "{tribe.name}" and id "{tribe.pk}" by user "{ctx.author}"'
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

