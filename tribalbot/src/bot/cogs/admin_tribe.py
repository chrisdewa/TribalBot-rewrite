from discord.ext.commands import Cog
from discord import app_commands, Interaction

from ..bot import TribalBot
from tribalbot.src.utils.tribes import *

from ._utils import get_tribe


class AdminTribeCog(Cog, description='Tribe Commands for Admins'):
    def __init__(self, bot) -> None:
        self.bot: TribalBot = bot
        print(f'[+] {self.qualified_name} loaded')
    
    async def cog_unload(self) -> None:
        print(f'[-] {self.qualified_name} unloaded')
    
    @app_commands.command(
        name='tribe-force-disband',
        description='Disolves the target tribe. Requieres Manage Server permission'
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def foo(
        self, 
        interaction: Interaction,
        name: str
    ):
        tribe = await get_tribe(interaction, name)
        if not tribe: return
        
        
        leader = interaction.guild.get_member(tribe.leader)
        manager = interaction.guild.get_member(tribe.manager)
        embed = Embed(
                title='Tribe Deleted by an Admin',
                description=f'Your tribe has been deleted by an admin. Details below.',
                color=Color.from_rgb(0,0,0)
            ) \
                .add_field(name='Tribe', value=tribe.name) \
                .add_field(name='Server', value=interaction.guild.name)
                
        
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
            
        
        for m in (leader, manager):
            if m:
                try:
                    await m.send(embed=embed)
                except: pass # members don't support dms

        await tribe.delete()
        
        await interaction.response.send_message(
            f'Done! the tribe "**{tribe.name}**" has been deleted.',
            ephemeral=True
        )
        

async def setup(bot: TribalBot):
    await bot.add_cog(AdminTribeCog(bot))
        