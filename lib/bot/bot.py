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
    
    def run(self) -> None:
        print('[!] Starting bot')
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