
import asyncio
from functools import wraps
from datetime import datetime, timedelta
from typing import Any, Callable, Hashable

from discord import Interaction
from discord.app_commands import Choice
from discord.ext import tasks


# TODO: change for named tuple
class CacheEntry:
    def __init__(self, result: list[Any] | None = None): 
        self.dt = datetime.utcnow()
        self.result = result or []
    
    @property
    def is_expired(self) -> bool:
        return self.dt + timedelta(minutes=2) < datetime.utcnow()


autocomplete_global_cache = {}

@tasks.loop(seconds=60)
async def clear_autocomplete_cache():
    for name in autocomplete_global_cache:
        for k, v in autocomplete_global_cache[name]:
            v: CacheEntry
            if v.is_expired:
                del autocomplete_global_cache[name][k]
    
def cache_autocomplete(name: str, keyf: Callable[[Interaction], Hashable] = lambda i: i.guild.id):
    """decorator for autocomplete functions that make calls to the database

    Args:
        name (str): name under which the function will be cached
        keyf (callable -> hashable): 
            a function that takes a single argument (interaction) and returns a hashable 
            to store the returned result
    """
    def wrapper(coro):
        @wraps(coro)
        async def inner(interaction: Interaction, current: str) -> list[Choice]:
            key = keyf(interaction)
            
            cache: CacheEntry = autocomplete_global_cache.setdefault(name, {}).setdefault(key, CacheEntry())
            if cache.result and not cache.is_expired:
                return cache.result
            else:
                result = await coro(interaction, current)
                autocomplete_global_cache[name][key] = CacheEntry(result)
                return result
        return inner
    return wrapper
