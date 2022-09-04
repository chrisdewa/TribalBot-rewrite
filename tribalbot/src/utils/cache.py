
import asyncio
from functools import wraps
from datetime import datetime, timedelta
from typing import Any, Callable, Hashable

from discord import Interaction
from discord.app_commands import Choice
from discord.ext import tasks

from tortoise.models import Model

# TODO: change for named tuple
class CacheEntry:
    def __init__(self, result: set[Model] | None = None): 
        self.dt = datetime.utcnow()
        self.result = result or set()
    
    @property
    def is_expired(self) -> bool:
        return self.dt + timedelta(minutes=2) < datetime.utcnow()


autocomplete_global_cache = {}

@tasks.loop(seconds=60)
async def clear_autocomplete_cache():
    to_del = []
    for name in autocomplete_global_cache:
        for k, v in autocomplete_global_cache[name].items():
            v: CacheEntry
            if v.is_expired:
                to_del.append((name, k))
    for k1,k2 in to_del:
        del autocomplete_global_cache[k1][k2]
    
def cached_model_autocomplete(
    name: str, 
    choice_factory: Callable[[set[Model]], list[Choice]],
    *,
    filter_by: str = 'name',
    keyf: Callable[[Interaction], Hashable] = lambda i: i.guild.id
):
    """decorator for autocomplete functions that make calls to the database

    Args:
        name (str): name under which the function will be cached
        choice_factory (callable -> list[Choice]): a callable that outputs the actual list of choices
        filter_by (str): the attribute name to filter by the data
            It will be compared to the current autocomplete value
        keyf (callable -> hashable): 
            a function that takes a single argument (interaction) and returns a hashable 
            to store the returned result
    Decorates:
        A coroutine that returns a set of Model types (like Tribe)
    """
    def wrapper(coro):
        @wraps(coro)
        async def inner(interaction: Interaction, current: str) -> list[Choice]:
            key = keyf(interaction)
            
            cache: CacheEntry = autocomplete_global_cache.setdefault(name, {}).setdefault(key, CacheEntry())
            if cache.result and not cache.is_expired:
                data =  cache.result
            else:
                data = await coro(interaction, current)
                autocomplete_global_cache[name][key] = CacheEntry(data)
                
            return choice_factory({
                item for item in data
                if getattr(item, filter_by, '').startswith(current)
            })
            
        return inner
    return wrapper
