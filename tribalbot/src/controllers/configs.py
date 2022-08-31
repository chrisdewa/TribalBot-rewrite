
from discord import Guild, Role
from tribalbot.src.orm.models import GuildConfig, TribeCategory

async def get_guild_config(guild: Guild) -> GuildConfig:
    guild_config, _ = await GuildConfig.get_or_create(guild_id=guild.id)
    return guild_config

async def create_new_category(guild: Guild, name: str) -> TribeCategory:
    guild_config = await get_guild_config(guild)
    same_categories = await TribeCategory.filter(guild_config=guild_config, name__iexact=name)
    if same_categories:
        raise ValueError(f'Tribe category with name "{name}" already exists')
    return await TribeCategory.create(guild_config=guild_config, name=name)

async def set_leaders_role(guild: Guild, role: Role) -> None:
    """sets up the leaders role in the guild configurations

    Args:
        guild (Guild): the guild to alter
        role (Role): the role to set
    """
    guild_config = await get_guild_config(guild)
    guild_config.leaders_role = role.id
    await guild_config.save()
    