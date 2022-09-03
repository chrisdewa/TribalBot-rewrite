from discord.ext.commands import Cog
from discord import app_commands, Interaction, permissions, Role

from ..bot import TribalBot
from tribalbot.src.controllers.configs import create_new_category, get_guild_config, set_leaders_role

class ConfigurationsCog(Cog, description='Tribe and guild configuration commands'):
    def __init__(self, bot) -> None:
        self.bot: TribalBot = bot
        print(f'[+] {self.qualified_name} loaded')
    
    async def cog_unload(self) -> None:
        print(f'[-] {self.qualified_name} unloaded')
    
    @app_commands.command(name='set-leaders-role', description='Selects the leaders role. [Caution] Overwrites previous setting.')
    @app_commands.describe(role='The role to be assigned to all tribe leaders')
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True, manage_roles=True)
    async def set_leaders_role_cmd(
        self,
        itr: Interaction,
        role: Role,
    ):
        await set_leaders_role(itr.guild, role)
        await itr.response.send_message(f'Done! The new Leaders role is {role.mention}', ephemeral=True)

    
    @app_commands.command(name='category-create', description='Creates a new tribe category')
    @app_commands.describe(name='The name of the category')
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def category_create_command(
        self, 
        itr: Interaction,
        name: app_commands.Range[str, 5, 30],
    ):
        cat = await create_new_category(itr.guild, name=name)
        await itr.response.send_message(f'The category "{name}" was successfully created with id {cat.pk}', ephemeral=True)
    
    @app_commands.command(name='banner-url', description='Allows or disallows tribe banners with URLs')
    @app_commands.describe(setting='If True tribes can put URLs in their banners, incluing invites, the contrary if False')
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def banner_url_policy(
        self,
        itr: Interaction,
        setting: bool
    ):
        config = await get_guild_config(itr.guild)
        config.urls = setting
        await config.save()
        if setting:
            msg = 'Done! Tribes can put URLs in their banners'
        else:
            msg = 'Done! Tribes cannot put URLs in their banners'
        
        await itr.response.send_message(msg, ephemeral=True)
    
async def setup(bot: TribalBot):
    await bot.add_cog(ConfigurationsCog(bot))
        