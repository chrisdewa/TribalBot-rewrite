import os

from dotenv import load_dotenv
load_dotenv()

__all__ = [
    'BOT_TOKEN',
    'DATABASE_URL',
]
BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
