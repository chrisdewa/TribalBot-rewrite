from discord import Bot

from lib.constants import TOKEN
from lib.orm.config import init_db, close_db

class TribalBot(Bot):
    def __init__(self, description=None, *args, **options):
        super().__init__(description, *args, **options)

    def on_ready(self):
        print(
            'TribalBot logged in:', f'USERNAME: {self.user.name}', f'ID: {self.user.id}', '='*30, sep='\n'
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