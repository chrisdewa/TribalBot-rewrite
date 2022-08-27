from typing import Optional

from discord.ext.commands import Cog
from discord import Interaction, app_commands

from lib.bot import TribalBot
from lib.orm.models import *
from lib.controllers.tribes import *
from lib.constants import DEFAULT_TRIBE_COLOR
from lib.utils.checks import guild_has_leaders_role

class TribeCog(Cog, description='Cog for tribe commands'):
    def __init__(self, bot) -> None:
        self.bot: TribalBot = bot
        print(f'[+] {self.qualified_name} loaded')
    
    async def cog_unload(self) -> None:
        print(f'[-] {self.qualified_name} unloaded')
    
    @app_commands.command(name='tribe-list', description="Returns a list of the server's tribes")
    @app_commands.guild_only()
    async def tribe_list(self, interaction: Interaction):
        tribes = await get_all_guild_tribes(interaction.guild)
        await interaction.response.send_message(f'Server tribes: {tribes}')
    
    @app_commands.command(name='tribe-create', description='Creates a new tribe with you as the leader!')
    @app_commands.describe(name='The name of your tribe', 
                           category='The category for the tribe (optional)',
                           color='The decimal number of the color for your tribe')
    @app_commands.autocomplete(category=autocomplete_categories)
    @app_commands.guild_only()
    @guild_has_leaders_role()
    async def tribe_create_cmd(self, 
                               interaction: Interaction,
                               name: app_commands.Range[str, 5, 30],
                               color: app_commands.Range[int, 0, 16777215] = DEFAULT_TRIBE_COLOR,
                               category: Optional[str] = None):
        kw = {
            'guild': interaction.guild, 
            'name': name, 
            'color': color,
            'leader': interaction.user,
        }
        if category:
            cat = await get_tribe_category(interaction.guild, name)
            if not cat:
                return await interaction.response.send_message(
                    f'There\'s no category with name "{category}", try a different category',
                    ephemeral=True
                )
            kw['category'] = cat
            
        tribes = await get_all_member_tribes(interaction.user)
        cats = [await t.category for t in tribes]
        
        if category in cats:
            return await interaction.response.send_message(
                "You're already a member of a tribe in the selected category (or the default category)",
                ephemeral=True
            )
        await interaction.response.defer(ephemeral=True)
        
        tribe = await create_new_tribe(**kw)
        guild_config: GuildConfig = await tribe.guild_config
        role_id = guild_config.leaders_role
        role = interaction.guild.get_role(role_id)
        await interaction.user.add_roles(role)
        
        await interaction.response.send_message(
            f"Success! You've founded tribe {tribe.name} with id: {tribe.pk}", 
            ephemeral=True
        )
    
    @app_commands.command(name='tribe-join', description='Creates a join application for target tribe')
    @app_commands.describe(name='The name of the tribe you want to join (Case Sensitive)')
    @app_commands.autocomplete(name=autocomplete_tribes)
    @app_commands.guild_only()
    @guild_has_leaders_role()
    async def tribe_join_cmd(
        self, 
        interaction: Interaction,
        name: str,
    ):
        tribe = await get_tribe_by_name(interaction.guild, name)
        if not tribe:
            return await interaction.response.send_message(
                f'There\'s no tribe with the name "{name}"',
                ephemeral=True
            )
        
        application = await create_tribe_join_application(tribe, interaction)
        
        if not application:
            cat = await tribe.category
            cat = cat.name if cat else 'Default'
            return await interaction.response.send_message(
                f"Application error: You are already a member of a tribe in this tribe's category ({cat})",
                ephemeral=True
            )
        
        guild = interaction.guild
        applicant = interaction.user
        leader = guild.get_member(tribe.leader)
        manager = guild.get_member(tribe.manager) if tribe.manager else None
        
        for u in (leader, manager):
            if u:
                await u.send(embed=Embed(
                    title='New Tribe Join Application',
                    description=f'**Server:** {guild.name}\n'
                                f'**Tribe:** {tribe.name}\n'
                                f'**Applicant:** {applicant}\n'
                                f'**Date:** of application: {application.pretty_dt}',
                    color=Color.random()
                ))
        
        return await interaction.response.send_message(
            f"Done! you've created an application to enter \"{name}\", the tribe has been notified.",
            ephemeral=True
        )
        
        
async def setup(bot: TribalBot):
    await bot.add_cog(TribeCog(bot))
        