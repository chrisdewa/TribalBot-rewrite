
from discord import Guild, Member

from lib.orm.models import Tribe, GuildConfig

async def get_guild_tribes(guild: Guild) -> list[Tribe]:
    guild_config, _ = await GuildConfig.get_or_create(guild_id=guild.id)
    tribes = await guild_config.tribes.all()
    return tribes

async def get_member_tribes(member: Member) -> list[Tribe]:
    guild = member.guild
    guild_config, _ = await GuildConfig.get_or_create(guild_id=guild.id)
    tribes = (
        await Tribe.filter(guild_config=guild_config, leader=member.id) +
        await Tribe.filter(guild_config=guild_config, members__contains=member.id)
    )
    return tribes

