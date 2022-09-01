
import asyncio
from functools import wraps
from datetime import datetime, timedelta
from typing import Any, Callable, Hashable

from discord import Interaction
from discord.app_commands import Choice

from tribalbot.src.bot import TribalBot


class CacheEntry:
    def __init__(self, result: list[Any] | None = None): 
        self.dt = datetime.utcnow()
        self.result = result or []

global_cache = {}


def cache_autocomplete(name: str, keyf: Callable[[Interaction], Hashable] = lambda i: i.guild.id):
    def wrapper(coro):
        @wraps(coro)
        async def inner(interaction: Interaction, current: str) -> list[Choice]:
            key = keyf(interaction)
            cache: CacheEntry = global_cache.setdefault(name, {}).setdefault(key, CacheEntry())
            if cache.result and cache.dt + timedelta(minutes=2) > datetime.utcnow():
                return cache.result
            else:
                result = await coro(interaction, current)
                global_cache[name][key] = CacheEntry(result)
                return result
        return inner
    return wrapper
