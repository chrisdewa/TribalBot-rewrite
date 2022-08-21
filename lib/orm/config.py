from tortoise import Tortoise

from lib.constants import DATABASE_URL

__all__ = ['init_db', 'close_db']

TORTOISE_ORM = {
    "connections": {"default": DATABASE_URL},
    "apps": {
        "models": {
            "models": [ "lib.orm.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}

async def init_db():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()

close_db = Tortoise.close_connections
