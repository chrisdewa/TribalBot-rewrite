import asyncio

from discord import Interaction, app_commands
from discord.app_commands import Choice

from tribalbot.src.orm.models import TribeCategory, Tribe

__all__ = [
    'autocomplete_categories',
    'autocomplete_guild_tribes',
    'autocomplete_manageable_tribes',
    
]

async def autocomplete_categories(interaction: Interaction, current: str) -> list[app_commands.Choice]:
    """Autocomplete function for categories
    """
    guild = interaction.guild
    cats = await TribeCategory.filter(guild_config_guild_id=guild.id, name__istartswith=current)
    return [
        Choice(name=cat.name, value=cat.name)
        for cat in cats
    ]

async def autocomplete_guild_tribes(interaction: Interaction, current: str) -> list[app_commands.Choice]:
    """Autocomplete for guild tribes"""
    guild = interaction.guild

    tribes = await Tribe.filter(guild_config__guild_id=guild.id, name__startswith=current)
    return [
        Choice(name=tribe.name, value=tribe.name)
        for tribe in tribes
    ]

async def autocomplete_manageable_tribes(interaction: Interaction, current: str) -> list[app_commands.Choice]:
    """Auto complete for tribes where the user is a leader or manager"""
    guild = interaction.guild
    user = interaction.user
    coro1 = Tribe.filter(guild_config_id=guild.id, leader=user.id, name__istartswith=current)
    coro2 = Tribe.filter(guild_config_id=guild.id, manager=user.id, name__istartswith=current)
    tribes = set(
        tribe for sublist in
        await asyncio.gather(coro1, coro2)
        for tribe in sublist
    )
    
    return [
        Choice(name=tribe.name, value=tribe.name)
        for tribe in tribes
    ]