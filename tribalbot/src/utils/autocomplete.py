import asyncio
from typing import Iterable

from discord import Interaction, app_commands
from discord.app_commands import Choice

from tribalbot.src.orm.models import TribeCategory, Tribe
from .cache import cached_model_autocomplete

__all__ = [
    'autocomplete_categories',
    'autocomplete_guild_tribes',
    'autocomplete_manageable_tribes',
]

def _choices_from_tribes(tribes: Iterable[Tribe]) -> list[Choice]:
    """Returns a list of choices from a tribe iterable"""
    return [
        Choice(name=tribe.name, value=tribe.name)
        for tribe in tribes
    ]

def _choices_from_categories(categories: Iterable[TribeCategory]) -> list[Choice]:
    return [
        Choice(name=cat.name, value=cat.name)
        for cat in categories
    ] 

@cached_model_autocomplete('categories', _choices_from_categories)
async def autocomplete_categories(interaction: Interaction, current: str) -> list[Choice]:
    """Autocomplete function for categories
    """
    guild = interaction.guild
    cats = await TribeCategory.filter(guild_config_id=guild.id)
    return cats
    
    
@cached_model_autocomplete('tribes', _choices_from_tribes)
async def autocomplete_guild_tribes(interaction: Interaction, current: str) -> list[Choice]:
    """Autocomplete for guild tribes"""
    guild = interaction.guild

    tribes = await Tribe.filter(guild_config_id=guild.id)
    return tribes

def _guild_n_user_filter(interaction: Interaction) -> tuple[int, int]:
    """returns a tuple with the interaction guild and user ids"""
    return interaction.guild.id, interaction.user.id

@cached_model_autocomplete(
    'manageable-tribes',
    _choices_from_tribes,
    keyf=_guild_n_user_filter
)
async def autocomplete_manageable_tribes(interaction: Interaction, current: str) -> list[Choice]:
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
    
    return tribes

@cached_model_autocomplete('leader-tribes', _guild_n_user_filter)
async def autocomplete_leader_tribes(interaction: Interaction, current: str) -> list[Choice]:
    """autocomplete for tribes quere the user is a leader of the tribe"""
    tribes = set(await Tribe.filter(guild_config_id=interaction.guild.id, leader=interaction.user.id))
    return tribes
    
