from discord.ext.commands import Cog
from discord import app_commands, Interaction

from lib.bot import TribalBot


class TestCog(Cog, description='Test commands'):
    def __init__(self, bot) -> None:
        self.bot: TribalBot = bot
        print(f'[+] {self.qualified_name} loaded')
    
    async def cog_unload(self) -> None:
        print(f'[-] {self.qualified_name} unloaded')
    
    @app_commands.command(
        name='foo',
        description='Test command'
    )
    async def foo(
        self, 
        interaction: Interaction,
    ):
        await interaction.response.send_message('works', ephemeral=True)

async def setup(bot: TribalBot):
    await bot.add_cog(TestCog(bot))
        