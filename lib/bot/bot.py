"""
Contains most of the bot setups
Loads cogs, prepares, starts and closes the database.
"""
import asyncio
from pathlib import Path

import discord
from discord.ext.commands import Bot
# from discord import app_commands

from lib.constants import BOT_TOKEN as TOKEN, guild_id, DEV_MODE
from lib.orm.config import *


class TribalBot(Bot):
    def __init__(self, *args, **options):
        # Init the bot with default intents since there won't be prefixed commands
        super().__init__(*args, 
                         command_prefix='?', 
                         intents=discord.Intents.default(),
                         **options
                         )
    
    async def setup_hook(self) -> None:
        print('[!] initializing database')
        await init_db()
        
        print('[!] Loading cogs')
        await self.load_cogs()
        
        if DEV_MODE:
            print('[!] bot in development mode')
            guild = discord.Object(id=guild_id)
            self.tree.copy_global_to(guild=guild)
            
            await self.tree.sync(guild=guild)
    
    async def __aexit__(self, *_, **__) -> None: # we're not using any args or kwargs
        if not self.is_closed():
            await self.close()
        await close_db()
    
    
    @classmethod
    def go(cls):
        """Starts up the bot"""
        async def runner():
            async with cls() as bot:
                print('[!] Starting bot up')
                await bot.start(TOKEN)
                
        asyncio.run(runner())
            
    async def on_ready(self):
        print(
            f'{"="*30}\n',
            f'TribalBot logged in:\n'
            f'USERNAME: {self.user.name}\n'
            f'ID: {self.user.id}\n'
            f'{"="*30}'
        )
    
    async def load_cogs(self):
        cogs = Path(__file__).parent / 'cogs' # absolute location of the cogs module
        base_path = 'lib.bot.cogs.'
        
        for cog in cogs.glob('*.py'): # iterate over the python files in the cogs directory
            if not cog.name.startswith('_'): # skip those starting with lower dash
                await self.load_extension(base_path + cog.name[:-3]) # join the base path with the 
                                                                     # name of the cog without the extension
    
  