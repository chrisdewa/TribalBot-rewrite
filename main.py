from lib.bot import TribalBot
from lib.constants import BOT_TOKEN


bot = TribalBot()

if __name__ == '__main__':
    bot.run(BOT_TOKEN) # fires up the bot

