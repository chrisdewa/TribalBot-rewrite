
from discord import Guild, Member

from lib.orm.models import Tribe, GuildConfig

async def get_guild_tribes(guild: Guild) -> set[Tribe]:
    tribes = await Tribe.filter(guild_config=guild.id)
    return set(tribes)

async def get_member_tribes(member: Member) -> set[Tribe]:
    guild_id = member.guild.id
    tribes = (
        await Tribe.filter(guild_config=guild_id, leader=member.id) +
        await Tribe.filter(guild_config=guild_id, members__contains=member.id)
    )
    return set(tribes)

