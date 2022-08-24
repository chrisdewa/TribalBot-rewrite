from discord.ext.commands import Cog

from discord import Guild, Interaction, app_commands

from lib.bot import TribalBot
# from lib.constants import DEFAULT_TRIBE_COLOR, guild_id
from lib.orm.models import *
from lib.controllers.tribes import *
    
class TribeCog(Cog, name='TribeCog', description='Cog for tribe commands'):
    def __init__(self, bot) -> None:
        self.bot: TribalBot = bot
        print(f'>> {self.qualified_name} Cog loaded')
    
    def cog_unload(self) -> None:
        print(f'>> {self.qualified_name} Cog unloaded')
    
    @app_commands.command(name='list-tribes', description="Returns a list of the server's tribes")
    async def list_tribes(self, interaction: Interaction):
        tribes = await get_guild_tribes(interaction.guild)
        await interaction.response.send_message(f'Server tribes: {tribes}')
        

async def setup(bot: TribalBot):
    await bot.add_cog(TribeCog(bot))
        