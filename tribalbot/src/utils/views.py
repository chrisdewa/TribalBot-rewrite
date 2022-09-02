from typing import Optional
from functools import cached_property

import discord
from discord import ui, Interaction, Embed, Color, Member, Guild

from tribalbot.src.orm.models import Tribe, TribeJoinApplication
from tribalbot.src.controllers.tribes import accept_applicant
from tribalbot.src.controllers.errors import InvalidMember, BadTribeCategory
from tribalbot.src.utils.tribes import get_tribe_embed


class DisableButtonsMixin:
    async def disable_buttons(self, itr: Optional[Interaction] = None):
        for child in self.children:
            if isinstance(child, ui.Button):
                child.disabled = True
        if itr: 
            await itr.response.edit_message(view=self)

class BaseInteractionCheckMixin:
    async def interaction_check(self, itr: Interaction) -> bool:
        owner = getattr(self, 'owner', None)
        if owner:
            if itr.user == owner:
                return True

            await itr.response.send_message(
                "This menu belongs to someone else", ephemeral=True
            )
            return False
        
        return True



class TribeBannerConfimationView(BaseInteractionCheckMixin, DisableButtonsMixin, ui.View):
    def __init__(
        self, 
        tribe: Tribe, 
        owner: Member, 
        color: Optional[int] = None,
        description: Optional[str] = None,
        image: Optional[str] = None,
        timeout=120
    ) -> None:
        super().__init__(timeout=timeout)
        self.tribe = tribe
        self.color = color
        self.description = description
        self.image = image
        self.owner = owner
        self.confirmed = False
    
    @cached_property
    def banner_embed(self) -> Embed:
        embed = Embed(title=self.tribe.name)
        
        if self.description:
            embed.description = self.description
        if self.image:
            embed.set_image(url=self.image)
            embed.set_footer(
                text='If the image  does not display correctly '
                     'check that the image url directs to an actual '
                     'image, not a website with an image (imgur)'
            )
        if self.color:
            embed.colour = self.color
        
        return embed
    
    @ui.button(custom_id="confirm", label='Confirm', style=discord.ButtonStyle.green)
    async def confirm_btn(self, interaction: Interaction, btn: ui.Button):
        self.confirmed = True
        await self.disable_buttons()
        
        self.stop()

    @ui.button(custom_id="cancel", label='Cancel', style=discord.ButtonStyle.red)
    async def cancel_btn(self, interaction: Interaction, btn: ui.Button):
        await self.disable_buttons()
        
        self.stop()
        

class ApplicationPaginatorView(BaseInteractionCheckMixin, DisableButtonsMixin, ui.View):
    def __init__(
        self, 
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
        

    @property
    def guild(self) -> Guild:
        return self.owner.guild

    @property
    def embeds(self) -> list[Embed]:
        
        default = [Embed(
            title='There are no applications',
            color=Color.random(),
        )]
        
        embeds = []
        for application in self.applications:
            applicant = self.guild.get_member(application.applicant)
            if applicant:
                embed = Embed(
                    title='Tribe Join Application',
                    description=f'Tribe: {self.tribe.name}\n'
                                f'Applicant: {applicant}\n'
                                f'Application date: {application.pretty_dt}',
                    color=Color.random()
                )
                embeds.append(embed)
            else:
                self.applications.remove(application)
                self.invalid_applications.append(application)
        
        return embeds or default
        
    
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
        msg = None
        
        try:
            await accept_applicant(applicant, application)
        except BadTribeCategory as err:
            self.invalid_applications.append(application)
            msg = str(err)
            
        msg = msg or f'Member {applicant} approved into the tribe!'
        self.applications.remove(application)
        embed = Embed(
            title=f'Member Accepted',
            description=f'Member {applicant} was accepted into the tribe',
            color=Color.green()
        )
        
        await itr.response.edit_message(embed=embed, view=self)
    
    @ui.button(custom_id="deny", emoji='🚫', row=0)
    async def _deny(self, itr: Interaction, button: ui.Button):
        application = self.applications[self.head]
        applicant = itr.guild.get_member(application.applicant)
        await application.delete()
        self.applications.remove(application)
        itr.channel.send()
        embed = Embed(
            title=f'Member Denied',
            description=f'Member {applicant if applicant else ""} application was denied',
            color=Color.red()
        )
        await itr.response.edit_message(embed=embed, view=self)
        

    @ui.button(custom_id="Next", emoji="▶️", row=0)
    async def _next(self, itr: discord.Interaction, button: ui.Button):
        self.head += 1
        await itr.response.edit_message(embed=self.embeds[self.index], view=self)
    
    @ui.button(custom_id="Close", emoji="❌", row=1)
    async def _close(self, itr: discord.Interaction, _):
        self.closed = True
        await self.disable_buttons(itr)
        self.stop()        
    
    
class TribePaginatorView(
    BaseInteractionCheckMixin, 
    DisableButtonsMixin, 
    ui.View
):
    def __init__(
        self, *, 
        owner: Member, 
        tribes: list[Tribe],
        head=0, 
        timeout: Optional[float] = 180
    ):
        super().__init__(timeout=timeout)
        self.owner = owner
        self.tribes = tribes
        self.head = head
    
    @cached_property
    def embeds(self) -> list[Embed]:
        guild = self.owner.guild
        return [
            get_tribe_embed(tribe, guild)
            for tribe in self.tribes
        ]
    
    @property
    def index(self) -> int:
        return self.head % len(self.embeds)

    @ui.button(custom_id="Back", emoji="◀️", row=0)
    async def _back(self, itr: discord.Interaction, button: ui.Button):
        self.head -= 1
        await itr.response.edit_message(embed=self.embeds[self.index], view=self)
    
    
    @ui.button(custom_id="Next", emoji="▶️", row=0)
    async def _next(self, itr: discord.Interaction, button: ui.Button):
        self.head += 1
        await itr.response.edit_message(embed=self.embeds[self.index], view=self)
    
    @ui.button(custom_id="Close", emoji="❌", row=1)
    async def _close(self, itr: discord.Interaction, _):
        self.closed = True
        await self.disable_buttons(itr)
        self.stop()
    
    @classmethod
    async def send_menu(cls, interaction: Interaction, tribes: list[Tribe]):
        if len(tribes) > 1:
            view = cls(owner=interaction.user, tribes=tribes)
            await interaction.response.send_message(embed=view.embeds[0], view=view)
        elif len(tribes) == 1:
            await interaction.response.send_message(embed=get_tribe_embed(tribes.pop(), interaction.guild))
        else:
            await interaction.response.send_message('You are not part of any tribes yet', ephemeral=True)
            
        
    
    

    

        