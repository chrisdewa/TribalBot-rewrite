from discord.ext.commands import Cog

from discord.commands import ApplicationContext, slash_command, Option

from lib.bot import TribalBot
from lib.constants import guild_ids


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
        await ctx.respond('works', ephemeral=True)

def setup(bot: TribalBot):
    bot.add_cog(TribeCog(bot))
        