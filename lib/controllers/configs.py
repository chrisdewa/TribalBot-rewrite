
from discord import Guild
from lib.orm.models import GuildConfig, TribeCategory

async def get_guild_config(guild: Guild) -> GuildConfig:
    guild_config, _ = await GuildConfig.get_or_create(guild_id=guild.id)
    return guild_config

async def create_new_category(guild: Guild, name: str) -> TribeCategory:
    guild_config = await get_guild_config(guild)
    same_categories = await TribeCategory.filter(guild_config=guild_config, name__iexact=name)
    if same_categories:
        raise ValueError(f'Tribe category with name "{name}" already exists')
    return await TribeCategory.create(guild_config=guild_config, name=name)
