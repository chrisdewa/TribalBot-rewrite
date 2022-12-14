"""
Contains most of the bot setups
Loads cogs, prepares, starts and closes the database.
"""
import asyncio
from pathlib import Path

import discord
from discord.ext.commands import Bot
from discord import Interaction
from discord.app_commands import AppCommandError
from discord.app_commands.errors import CommandNotFound
# from discord import app_commands

from tribalbot.src.constants import guild_id, DEV_MODE
from tribalbot.src.orm.config import *
from tribalbot.src.utils.misc import separator

_allowed_errors = (
    CommandNotFound,
)

class TribalBot(Bot):
    def __init__(self, *args, **options):
        # Init the bot with default intents since there won't be prefixed commands
        intents = discord.Intents.default()
        intents.members = True
        intents.typing = False
        
        super().__init__(
            *args, 
            command_prefix='?', 
            intents=intents,
            **options
        )
        tree = self.tree
        
        #@tree.error
        async def on_app_command_error(interaction: Interaction, error: AppCommandError):
            if interaction.response.is_done(): # an error message has already been delivered to the user
                return
            else:
                await interaction.response.send_message(
                    f'The command failed because `{error}`', ephemeral=True
                )
                if not isinstance(error, _allowed_errors):
                    raise error
    
    async def setup_hook(self) -> None:
        await init_db()
        await self.load_cogs()
        
        
        if DEV_MODE:
            guild = discord.Object(id=guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
    
    async def __aexit__(self, *_, **__) -> None: # we're not using any args or kwargs
        if not self.is_closed():
            await self.close()
        await close_db()
    
    async def on_ready(self):
        separator()
        print(
            f'TribalBot logged in:\n'
            f'USERNAME: {self.user.name}\n'
            f'ID: {self.user.id}'
        )
        separator()
    
    async def load_cogs(self):
        cogs = Path(__file__).parent / 'cogs' # absolute location of the cogs module
        base_path = 'tribalbot.src.bot.cogs.'
        print('[!] Loading cogs')
        for cog in cogs.glob('*.py'): # iterate over the python files in the cogs directory
            if not cog.name.startswith('_'): # skip those starting with lower dash
                await self.load_extension(base_path + cog.name[:-3]) # join the base path with the 
                                                                     # name of the cog without the extension
    
  