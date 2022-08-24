from discord.ext.commands import Cog

from discord import Guild
from discord.commands import ApplicationContext, slash_command, Option

from lib.bot import TribalBot
from lib.constants import DEFAULT_TRIBE_COLOR, guild_ids
from lib.orm.models import *
from lib.controllers.tribes import *
    
class TribeCog(Cog, name='TribeCog', description='Cog for tribe commands'):
    def __init__(self, bot) -> None:
        self.bot: TribalBot = bot
        print(f'>> {self.qualified_name} Cog loaded')
    
    def cog_unload(self) -> None:
        print(f'>> {self.qualified_name} Cog unloaded')
    
    @slash_command(
        guild_ids=guild_ids,
        name='list-tribes',
        description='Lists tribes in the server by name',
    )
    async def list_tribes(
        self, 
        ctx: ApplicationContext,
    ):
        # TODO: make sure there's a guild
        tribes = await get_guild_tribes(ctx.guild)
        await ctx.respond(str(tribes), ephemeral=True)
    
    @slash_command(
        guild_ids=guild_ids,
        name='create-tribe',
        description='Creates a new tribe with you as the leader!'
    )
    async def create_tribe_command(
        self,
        ctx: ApplicationContext,
        name: Option(
            str, 
            description='The name of the tribe. Must be under 30 characters', 
            max_length=30
            # TODO: add category with autocomplete
        ),
        color: Option(
            int,
            description='The color of your tribe, has to be a number from 0 to 16777215',
            min_value=0,
            max_value=16777215,
            optional=True,
            default=DEFAULT_TRIBE_COLOR
        )
    ):
        tribe = await create_new_tribe(ctx=ctx, name=name, color=color, leader=ctx.author.id)
        print(tribe)
        await ctx.respond(f'Tribe created with id: {tribe.pk}')
        

def setup(bot: TribalBot):
    bot.add_cog(TribeCog(bot))
        