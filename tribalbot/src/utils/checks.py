from discord import Interaction, app_commands, Embed, Color

from ..controllers.configs import get_guild_config

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
        role = guild.get_role(guild_config.leaders_role) if guild_config.leaders_role else None
        if not role:
            await interaction.response.send_message(
                'The command failed because the leaders role is not configured, talk to your server admins', 
                ephemeral=True
            )
            return False
        
        elif role >= guild.me.top_role:
            await interaction.response.send_message(
                "The bot's top role is below the (or is) leaders role. Talk to your server admins",
                embed=Embed(color=Color.orange()).set_image(url='https://i.imgur.com/cVZUuzA.gif'),
                ephemeral=True,
            )
            return False
        else:
            return True
        
    return app_commands.check(predicate)