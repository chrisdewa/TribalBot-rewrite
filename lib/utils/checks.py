from discord import Interaction, app_commands

from lib.controllers.configs import get_guild_config
from lib.orm.models import GuildConfig

def is_chrisdewa():
    """Allows an app command to run only if the user is ChrisDewa#4552"""
    def predicate(interaction: Interaction) -> bool:
        return interaction.user.id == 365957462333063170
    return app_commands.check(predicate)

def guild_has_leaders_role():
    """Blocks commands unless the server admins have set up the leader's role"""
    async def predicate(interaction: Interaction) -> bool:
        guild = interaction.guild
        if not guild: return False
        guild_config = await get_guild_config(guild)
        if not guild_config.leaders_role or not guild.get_role(guild_config.leaders_role):
            await interaction.response.send_message(
                'The command failed because the leaders role is not configured, talk to your server admins', 
                ephemeral=True
            )
            return False
        else:
            return True
        
    return app_commands.check(predicate)