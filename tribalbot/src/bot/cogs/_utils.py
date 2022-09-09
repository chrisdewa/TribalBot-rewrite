"""
Small concrete helpers specific to cogs
"""

from discord import Interaction

from tribalbot.src.orm.models import Tribe
from tribalbot.src.controllers.tribes import get_tribe_by_name


async def get_tribe(interaction: Interaction, tribe_name) -> Tribe | None:
    """Returns the tribe or handles the response to the user in case it doesn't exist"""
    tribe = await get_tribe_by_name(interaction.guild, tribe_name)
    if not tribe:
        return await interaction.response.send_message(
            f'There\'s no tribe with the name "{tribe_name}"',
            ephemeral=True
        )
    else:
        return tribe
