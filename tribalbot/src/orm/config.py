from tortoise import Tortoise

from tribalbot.src.constants import DATABASE_URL

__all__ = ['init_db', 'close_db']

TORTOISE_ORM = {
    "connections": {"default": DATABASE_URL},
    "apps": {
        "models": {
            "models": [ "tribalbot.src.orm.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}

async def init_db():
    """Set's up tortoise orm. 
    `Tortoise.generate_schemas` should only be called when a change is made to the database.
    """
    print('[!] initializing database')
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()

async def close_db():
    print('[-] closing the database')
    await Tortoise.close_connections() 
