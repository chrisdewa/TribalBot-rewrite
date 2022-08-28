from typing import Optional

import discord
from discord import ui, Interaction, Embed, Color, Member

from lib.orm.models import TribeJoinApplication


class ApplicationPaginatorView(discord.ui.View):
    def __init__(self, embeds: list[Embed], owner: Member, head=0, timeout=120):
        super().__init__(timeout=timeout)
        self.closed = False
        self.owner = owner
        self.embeds = embeds
        self.head = head

    async def interaction_check(self, itr: Interaction) -> bool:
        if itr.user == self.owner:
            return True

        await itr.response.send_message(
            "This menu belongs to someone else", ephemeral=True
        )
        return False
    
    @property
    def index(self) -> int:
        return self.head % len(self.embeds)

    @discord.ui.button(custom_id="Back", emoji="◀️", row=0)
    async def _back(self, itr: discord.Interaction, button: ui.Button):
        self.head -= 1
        await itr.response.edit_message(embed=self.embeds[self.index], view=self)

    @discord.ui.button(custom_id="Next", emoji="▶️", row=0)
    async def _next(self, itr: discord.Interaction, button: ui.Button):
        self.head += 1
        await itr.response.edit_message(embed=self.embeds[self.index], view=self)
    
    # TODO: add accept and deny buttons

    @discord.ui.button(custom_id="Close", emoji="❌", row=1)
    async def _close(self, itr: discord.Interaction, _):
        self.closed = True
        await self.disable_buttons(itr)
        self.stop()
    
    async def disable_buttons(self, itr: Optional[Interaction] = None):
        for button in self.children:
            button: ui.Button
            button.disabled = True
        if itr: 
            await itr.response.edit_message(view=self)
    

    
    
    

        