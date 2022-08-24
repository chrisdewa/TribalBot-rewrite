import os

from dotenv import load_dotenv
load_dotenv()

__all__ = [
    'DEV_MODE',
    'BOT_TOKEN',
    'DATABASE_URL',
    'guild_ids',
    'DEFAULT_TRIBE_COLOR',
]

DEFAULT_TRIBE_COLOR = 16711680

DEV_MODE = os.getenv('DEV_MODE', False)  # defines amongs other things if commands should be synced for a single server (development server)
if DEV_MODE:
    print('[!] Bot running in development mode')
BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

guild_ids = None if DEV_MODE else [716844885457764435] # if DEV_MODE is not enabled commands will be available globally