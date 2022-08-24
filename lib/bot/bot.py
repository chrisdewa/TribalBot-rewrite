"""
Contains most of the bot setups
Loads cogs, prepares, starts and closes the database.
"""
from pathlib import Path

from discord import Bot

from lib.constants import BOT_TOKEN as TOKEN
from lib.orm.config import *


class TribalBot(Bot):
    def __init__(self, *args, **options):
        super().__init__(*args, **options)

    async def on_ready(self):
        print(
            f'TribalBot logged in:\n'
            f'USERNAME: {self.user.name}\n'
            f'ID: {self.user.id}\n'
            f'{"="*30}'
        )
    
    def load_cogs(self):
        cogs = Path(__file__).parent / 'cogs' # absolute location of the cogs module
        base_path = 'lib.bot.cogs.'
        
        for cog in cogs.glob('*.py'): # iterate over the python files in the cogs directory
            if not cog.name.startswith('_'): # skip those starting with lower dash
                self.load_extension(base_path + cog.name[:-3]) # join the base path with the 
                                                               # name of the cog without the extension
    
    def run(self) -> None:
        print('[!] Starting bot')
        print('[!] Loading cogs')
        self.load_cogs()
        print('[!] initializing database')
        self.loop.run_until_complete(init_db())
        try:
            print('[!] running bot')
            self.loop.run_until_complete(self.start(TOKEN))
        except KeyboardInterrupt:
            print('[!] Closing bot')
            self.loop.run_until_complete(self.close())
        finally:
            print('[!] Closing database')
            self.loop.run_until_complete(close_db())