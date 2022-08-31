from tribalbot.src.bot import TribalBot
from tribalbot.src.constants import BOT_TOKEN


bot = TribalBot()

if __name__ == '__main__':
    bot.run(BOT_TOKEN) # fires up the bot

