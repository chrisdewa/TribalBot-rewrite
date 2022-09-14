"""
Small concrete helpers specific to cogs
"""

from discord import Interaction, Member, Embed, Color

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

async def notify_new_tribe_leader(new_leader: Member, tribe: Tribe):
    try:
        await new_leader.send(embed=Embed(
            title='Tribe Notificaction',
            description=f'You have been appointed as the new leader of '
                        f'**{tribe.name}** in the server "**{new_leader.guild.name}**" '
                        f'because the old leader was forced to leave by a server admin.',
            color=Color.purple()
        ))
    except: pass # new leader is not accepting dms