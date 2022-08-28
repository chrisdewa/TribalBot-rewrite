from typing import Optional
from functools import cached_property

import discord
from discord import ui, Interaction, Embed, Color, Member, Guild

from lib.orm.models import Tribe, TribeJoinApplication
from lib.controllers.tribes import accept_applicant
from lib.controllers.errors import InvalidMember, BadTribeCategory


class ApplicationPaginatorView(discord.ui.View):
    def __init__(self, 
                 applications: list[TribeJoinApplication], 
                 tribe: Tribe,
                 owner: Member, 
                 head=0, 
                 timeout=120
                ):
        super().__init__(timeout=timeout)
        self.closed = False
        self.applications = applications
        self.tribe = tribe
        self.owner = owner
        self.head = head

        self.invalid_applications = []

    async def interaction_check(self, itr: Interaction) -> bool:
        if itr.user == self.owner:
            return True

        await itr.response.send_message(
            "This menu belongs to someone else", ephemeral=True
        )
        return False

    @property
    def guild(self) -> Guild:
        return self.owner.guild

    @property
    def embeds(self) -> list[Embed]:
        
        embeds = []
        for application in self.applications:
            applicant = self.guild.get_member(application.applicant)
            if applicant:
                embed = Embed(
                    title='Tribe Join Application',
                    description=f'Tribe: {self.tribe.name}'
                                f'Applicant: {applicant}'
                                f'Application date: {application.pretty_dt}'
                )
                embeds.append(embed)
            else:
                self.applications.remove(application)
                self.invalid_applications.append(application)
        
        return embeds
        
    
    @property
    def index(self) -> int:
        return self.head % len(self.embeds)

    @ui.button(custom_id="Back", emoji="◀️", row=0)
    async def _back(self, itr: discord.Interaction, button: ui.Button):
        self.head -= 1
        await itr.response.edit_message(embed=self.embeds[self.index], view=self)

    @ui.button(custom_id="approve", emoji='✅', row=0)
    async def _approve(self, itr: Interaction, button: ui.Button):
        application = self.applications[self.head]
        applicant = itr.guild.get_member(application.applicant)
        await accept_applicant(applicant, application)
        self.applications.remove(application)
        self.head += 1
        await itr.response.edit_message(embed=self.embeds[self.index], view=self)
        await itr.response.send_message(
            f'Member {applicant} approved into the tribe!', ephemeral=True
        )
    
    @ui.button(custom_id="deny", emoji='🚫', row=0)
    async def _deny(self, itr: Interaction, button: ui.Button):
        application = self.applications[self.head]
        applicant = itr.guild.get_member(application.applicant)
        await application.delete()
        self.applications.remove(application)
        self.head += 1
        await itr.response.edit_message(embed=self.embeds[self.index], view=self)
        await itr.response.send_message(
            f'Member {applicant} approved into the tribe!', ephemeral=True
        )

    @ui.button(custom_id="Next", emoji="▶️", row=0)
    async def _next(self, itr: discord.Interaction, button: ui.Button):
        self.head += 1
        await itr.response.edit_message(embed=self.embeds[self.index], view=self)
    
    @ui.button(custom_id="Close", emoji="❌", row=1)
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
    

    
    
    

        