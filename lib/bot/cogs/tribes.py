from typing import Optional

from discord.ext.commands import Cog
from discord import Guild, Interaction, app_commands

from lib.bot import TribalBot
# from lib.constants import DEFAULT_TRIBE_COLOR, guild_id
from lib.orm.models import *
from lib.controllers.tribes import *
from lib.constants import DEFAULT_TRIBE_COLOR
    
class TribeCog(Cog, description='Cog for tribe commands'):
    def __init__(self, bot) -> None:
        self.bot: TribalBot = bot
        print(f'[+] {self.qualified_name} loaded')
    
    async def cog_unload(self) -> None:
        print(f'[-] {self.qualified_name} unloaded')
    
    @app_commands.command(name='tribe-list', description="Returns a list of the server's tribes")
    async def tribe_list(self, interaction: Interaction):
        tribes = await get_all_guild_tribes(interaction.guild)
        await interaction.response.send_message(f'Server tribes: {tribes}')
    
    @app_commands.command(name='tribe-create', description='Creates a new tribe with you as the leader!')
    @app_commands.describe(name='The name of your tribe', 
                           category='The category for the tribe (optional)',
                           color='The decimal number of the color for your tribe')
    @app_commands.autocomplete(category=autocomplete_categories)
    async def tribe_create_cmd(self, 
                               interaction: Interaction,
                               name: app_commands.Range[str, 5, 30],
                               color: app_commands.Range[int, 0, 16777215] = DEFAULT_TRIBE_COLOR,
                               category: Optional[str] = None,
                               ):
        kw = dict(
            guild=interaction.guild, 
            name=name, 
            color=color,
            leader=interaction.user,
        )
        if category:
            cat = await get_tribe_category(interaction.guild, name)
            kw['category'] = cat
            
        tribes = await get_all_member_tribes(interaction.user)
        cats = [await t.category for t in tribes]
        
        if category in cats:
            return await interaction.response.send_message(
                "You're already a member of a tribe in the selected category (or the default category)",
                ephemeral=True
            )
        
        tribe = await create_new_tribe(**kw)
        await interaction.response.send_message(f"Success! You've founded tribe {tribe.name} with id: {tribe.pk}")
        
        

async def setup(bot: TribalBot):
    await bot.add_cog(TribeCog(bot))
        