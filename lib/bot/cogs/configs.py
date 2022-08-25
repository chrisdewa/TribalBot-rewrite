from discord.ext.commands import Cog
from discord import app_commands, Interaction

from lib.bot import TribalBot
from lib.controllers.configs import create_new_category

class ConfigurationsCog(Cog, description='Tribe and guild configuration commands'):
    def __init__(self, bot) -> None:
        self.bot: TribalBot = bot
        print(f'[+] {self.qualified_name} loaded')
    
    async def cog_unload(self) -> None:
        print(f'[-] {self.qualified_name} unloaded')
    
    @app_commands.command(name='category-create', description='Creates a new tribe category')
    @app_commands.describe(name='The name of the category')
    async def category_create_command(
        self, 
        interaction: Interaction,
        name: app_commands.Range[str, 5, 30],
    ):
        cat = await create_new_category(interaction.guild, name=name)
        await interaction.response.send_message(f'The category "{name}" was successfully created with id {cat.pk}', ephemeral=True)

async def setup(bot: TribalBot):
    await bot.add_cog(ConfigurationsCog(bot))
        