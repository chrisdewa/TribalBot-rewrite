from discord import Interaction, app_commands

def is_chrisdewa():
    """Allows an app command to run only if the user is ChrisDewa#4552"""
    def predicate(interaction: Interaction) -> bool:
        return interaction.user.id == 365957462333063170
    return app_commands.check(predicate)
