import os

from dotenv import load_dotenv
load_dotenv()

__all__ = [
    'DEV_MODE',
    'BOT_TOKEN',
    'DATABASE_URL',
    'guild_ids',
]

DEV_MODE = os.getenv('DEV_MODE', False)
BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

guild_ids = None if DEV_MODE else [716844885457764435]