from discord.ext.commands import Cog

from discord.commands import ApplicationContext, slash_command, Option

from lib.bot import TribalBot
from lib.constants import guild_ids


class TestCog(Cog, name='Test', description='Test commands'):
    def __init__(self, bot) -> None:
        self.bot: TribalBot = bot
        print(f'>> {self.qualified_name} Cog loaded')
    
    def cog_unload(self) -> None:
        print(f'>> {self.qualified_name} Cog unloaded')
    
    @slash_command(
        guild_ids=guild_ids,
        name='foo',
        description='Test command'
    )
    async def foo(
        self, 
        ctx: ApplicationContext,
    ):
        await ctx.respond('works', ephemeral=True)

def setup(bot: TribalBot):
    bot.add_cog(TestCog(bot))
        