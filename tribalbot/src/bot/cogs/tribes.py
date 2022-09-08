from typing import Literal, Optional

from discord.ext.commands import Cog
from discord import Interaction, app_commands
from discord.app_commands import Range

import validators.url as validate_url
from tribalbot.src.utils.autocomplete import autocomplete_leader_tribes

from tribalbot.src.utils.tribes import tribe_banner

from ..bot import TribalBot
from tribalbot.src.orm.models import *
from tribalbot.src.controllers.tribes import *
from tribalbot.src.constants import DEFAULT_TRIBE_COLOR
from tribalbot.src.utils.tribes import TribeMemberCollection
from tribalbot.src.utils.checks import guild_has_leaders_role
from tribalbot.src.utils.views import (
    ApplicationPaginatorView, 
    TribePaginatorView, 
    TribeBannerConfimationView
)
from tribalbot.src.utils.autocomplete import *

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

async def can_manage_tribe(interaction: Interaction, tribe: Tribe) -> Literal[True] | None:
    """Returns True if the interaction.user can manage the tribe and handles the response if they can't"""
    mid = interaction.user.id
    if mid not in tribe.staff:
        return await interaction.response.send_message(
            'You cannot manage this tribe',
            ephemeral=True
        )
    else:
        return True
        
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
        for tribe in tribes:
            await tribe.fetch_related('members')
        view = TribePaginatorView(owner=interaction.user, tribes=tribes)
        await view.send_menu(interaction, tribes)
    
    @app_commands.command(name='tribe-create', description='Creates a new tribe with you as the leader!')
    @app_commands.describe(name='The name of your tribe', 
                           category='The category for the tribe (optional)',
                           color='The decimal number of the color for your tribe')
    @app_commands.autocomplete(category=autocomplete_categories)
    @app_commands.guild_only()
    @guild_has_leaders_role()
    async def tribe_create_cmd(self, 
                               interaction: Interaction,
                               name: Range[str, 5, 30],
                               color: Range[int, 0, 16777215] = DEFAULT_TRIBE_COLOR,
                               category: Optional[str] = None):
        kw = {
            'guild': interaction.guild, 
            'name': name, 
            'color': color,
            'leader': interaction.user,
        }
        if category:
            cat = await get_tribe_category(interaction.guild, category)
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
        await interaction.followup.send(
            f"Success! You've founded tribe {tribe.name} with id: {tribe.pk}", 
            ephemeral=True
        )
    
    @app_commands.command(name='tribe-join', description='Creates a join application for target tribe')
    @app_commands.describe(name='The name of the tribe you want to join (Case Sensitive)')
    @app_commands.autocomplete(name=autocomplete_guild_tribes)
    @app_commands.guild_only()
    @guild_has_leaders_role()
    async def tribe_join_cmd(
        self, 
        interaction: Interaction,
        name: str,
    ):
        tribe = await get_tribe(interaction, name)
        if not tribe: return # get_tribe will notify by itself it the tribe is not existent
        
        tribes = await get_all_member_tribes(interaction.user)
        if tribe in tribes:
            return await interaction.response.send_message(
                'You are already part of this tribe',
                ephemeral=True
            )
        
        applications = {
            application.applicant
            for application in
            await get_tribe_applications(tribe)
        }
        
        if interaction.user.id in applications:
            return await interaction.response.send_message(
                'You already have an application to enter this tribe, wait for the tribe staff to accept or deny it',
                ephemeral=True
            )
        
        application = await create_tribe_join_application(tribe, interaction) # create an application
        
        if not application: # it might be unsuccessful if the user already has a tribe in the given category
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
        
        for u in (leader, manager): # we notify at least the tribe leader, but also the manager if it exists
            if u:
                await u.send(
                    embed=Embed(
                        title='New Tribe Join Application',
                        description=f'**Server:** {guild.name}\n'
                                    f'**Tribe:** {tribe.name}\n'
                                    f'**Applicant:** {applicant}\n'
                                    f'**Date:** of application: {application.pretty_dt}',
                        color=Color.random()
                    ).set_footer(text='Review applications from the server using /tribe-applications')
                )

        return await interaction.response.send_message(
            f"Done! you've created an application to enter \"{name}\", the tribe has been notified.",
            ephemeral=True
        )
    
    @app_commands.command(name='tribe-applications', description='Review Join applications to accept or deny')
    @app_commands.describe(name='The name of the tribe you want to manage (you must be a leader or manager)')
    @app_commands.autocomplete(name=autocomplete_manageable_tribes)
    @app_commands.guild_only()
    @guild_has_leaders_role()
    async def tribe_applications_cmd(
        self, 
        interaction: Interaction,
        name: str,
    ):
        
        tribe = await get_tribe(interaction, name)
        if not tribe or not await can_manage_tribe(interaction, tribe): 
            return
        
        applications = await get_tribe_applications(tribe)
        
        view = ApplicationPaginatorView(applications, tribe, interaction.user)
        await interaction.response.send_message(embed=view.embeds[0], view=view, ephemeral=True)
    
    @app_commands.command(name='my-tribes', description='Shows you the tribes you are a part of')
    @app_commands.guild_only()
    @guild_has_leaders_role()
    async def my_tribes_cmd(self, interaction: Interaction):
        
        tribes = await get_all_member_tribes(interaction.user)
        [await t.fetch_related("members") for t in tribes]
        await TribePaginatorView.send_menu(interaction, tribes)
        
    @app_commands.command(name='set-banner', description="Sets your tribe's banner")
    @app_commands.describe(name='The name of the target tribe')
    @app_commands.autocomplete(name=autocomplete_manageable_tribes)
    @app_commands.guild_only()
    @guild_has_leaders_role()
    async def set_tribe_banner_cmd(
        self,
        interaction: Interaction,
        name: str,
        color: Range[int, 0, 16777215] = None,
        description: Range[str, 0, 2000] = None,
        image: Optional[str] = None,
    ):
        if not any((color, description, image)):
            return await interaction.response.send_message(
                'You must select any of "color", "description" or "image"',
                ephemeral=True
            )
        
        tribe = await get_tribe(interaction, name)
        if not tribe or not await can_manage_tribe(interaction, tribe): 
            return
        
        banner = tribe.banner
        if color:
            banner['color'] = color
        if description: 
            banner['description'] = description
        if image:
            if validate_url(image):
                banner['image'] = image
            else:
                return await interaction.response.send_message(
                    content="Your image url is invalid, please corroborate it. "
                            "Also make sure that the url directs to an actual "
                            "image and not a website that contains an image like imgur or tenor",
                    ephemeral=True
                )
        
        view = TribeBannerConfimationView(tribe, interaction.user, **banner)
        
        await interaction.response.send_message(
            content='Please review the tribe banner and confirm or cancel the changes', 
            embed=view.banner_embed,
            view=view, 
            ephemeral=True
        )
        
        await view.wait()
        if view.confirmed:
            tribe.color = color
            banner.pop('color', None)
            tribe.banner = banner
            await tribe.save()
            await view.itn.response.edit_message(content='Done! changes applied', embed=None, view=view)
        else:
            await view.itn.response.edit_message(content='Changes cancelled', embed=None, view=view)

    @app_commands.command(name='banner', description="Displays a tribe banner")
    @app_commands.describe(name='The name of the target tribe')
    @app_commands.autocomplete(name=autocomplete_guild_tribes)
    @app_commands.guild_only()
    @guild_has_leaders_role()
    async def display_banner_cmd(
        self,
        interaction: Interaction,
        name: str,
    ):
        tribe = await get_tribe(interaction, name)
        if not tribe: return
        
        await tribe.fetch_related('members', 'guild_config')
        embed = tribe_banner(tribe, interaction.guild)
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name='tribe-kick', description="Kicks a member out of the tribe")
    @app_commands.describe(name='The name of the target tribe', member='The member to kick')
    @app_commands.autocomplete(name=autocomplete_manageable_tribes)
    @app_commands.guild_only()
    @guild_has_leaders_role()
    async def tribe_kick_cmd(
        self,
        interaction: Interaction,
        name: str,
        member: Member
    ):
        tribe = await get_tribe(interaction, name)
        if not tribe or not await can_manage_tribe(interaction, tribe): 
            return

        await tribe.fetch_related('members')
        
        if member.id == interaction.user.id:
            return await interaction.response.send_message(
                "Don't kick yourself out, just exit the tribe...",
                ephemeral=True
            )
        elif member.id not in [m.member_id for m in tribe.members]:
            return await interaction.response.send_message(
                f'{member.mention} is not a part of this tribe',
                ephemeral=True
            )
        
        
        for m in tribe.members:
            if m.member_id == member.id:
                await m.delete()
                break
        if member.id == tribe.manager:
            tribe.manager = None
        
        await tribe.save()
        
        await interaction.response.send_message(
            f'Done! {member.mention} has been kicked out the tribe',
            ephemeral=True
        )

    @app_commands.command(name='tribe-exit', description="Exits the target tribe")
    @app_commands.describe(name='The name of the tribe')
    @app_commands.autocomplete(name=autocomplete_user_tribes)
    @app_commands.guild_only()
    @guild_has_leaders_role()
    async def exit_tribe_command(
        self, 
        interaction: Interaction,
        name: str
    ):
        member = interaction.user
        tribe = await get_tribe(interaction, name)
        if not tribe: return 
        tribe_members = TribeMemberCollection(await tribe.members)
        
        if member.id == tribe.leader:
            await handle_leader_leave(tribe, members=tribe_members) # handle leader exiting tribe
        elif member.id in tribe_members.ids:
            await tribe_members.remove_member(member.id)
            if member.id == tribe.manager:
                tribe.manager = None
        else:
            return await interaction.response.send_message(
                f"You are not a part of **{tribe.name}**",
                ephemeral=True
            )
        await tribe.save()
        await interaction.response.send_message(
                f"Done! You are no longer a part of **{tribe.name}**",
                ephemeral=True
            )
        
    @app_commands.command(name='tribe-set-manager', description="Appoints the manager of the tribe. You must be a leader to use this.")
    @app_commands.describe(name='the name of a tribe you are a leader of', new_manager='The manager to appoint')
    @app_commands.autocomplete(name=autocomplete_leader_tribes)
    @app_commands.rename(new_manager='new-manager')
    @app_commands.guild_only()
    @guild_has_leaders_role()
    async def set_tribe_manager_command(
        self, 
        interaction: Interaction,
        name: str,
        new_manager: Member,
    ):
        respond = interaction.response.send_message
        
        tribe = await get_tribe(interaction, name)
        if not tribe: 
            return 
        elif tribe.leader != interaction.user.id:
            return await respond(
                'You are not the leader of this tribe',
                ephemeral=True
            )
        elif new_manager == interaction.user:
            return await respond(
                "You cannot be the leader and the tribe's manager, appoint someone else",
                ephemeral=True
            )
        members = TribeMemberCollection(await tribe.members)
        if new_manager.id not in members.ids:
            return await respond(
                f'{new_manager.mention} is not a part of this tribe',
                ephemeral=True
            )
        elif new_manager.id == tribe.manager:
            return await respond(
                f'{new_manager.mention} is already the manager of the tribe',
                ephemeral=True
            )
        
        tribe.manager = new_manager.id
        await tribe.save()
        
        await respond(
            f"Done! {new_manager.mention} is now the tribe's manager",
            ephemeral=True
        )

    @app_commands.command(
        name='tribe-transfer-leadership',
        description="Transfer the leadership of the tribe to a target member"
    )
    @app_commands.describe(
        name='The name of the tribe',
        new_leader='The new leader of the tribe'
    )
    @app_commands.rename(new_leader='new-leader')
    @app_commands.autocomplete(name=autocomplete_leader_tribes)
    @app_commands.guild_only()
    @guild_has_leaders_role()
    async def tribe_transfer_leadership_cmd(
        self,
        interaction: Interaction,
        name: str,
        new_leader: Member,
    ):
        respond = interaction.response.send_message
        
        tribe = await get_tribe(interaction, name)
        if not tribe: 
            return 
        elif tribe.leader != interaction.user.id:
            return await respond(
                'You are not the leader of this tribe',
                ephemeral=True
            )
        elif new_leader == interaction.user:
            return await respond(
                "You cannot target yourself with this command",
                ephemeral=True
            )
        members = TribeMemberCollection(await tribe.members)
        if new_leader.id not in members.ids:
            return await respond(
                f'Error: {new_leader.mention} is not a part of the tribe',
                ephemeral=True
            )
        await interaction.response.defer(ephemeral=True)
        
        tribe.leader = new_leader.id
        await members.remove_member(new_leader.id)
        
        await tribe.save()
        await TribeMember.create(tribe=tribe, member_id=interaction.user.id)
        
        try:
            await new_leader.send(
                embed=Embed(
                    description=f'You have been a pointed as the leader of **{tribe.name}** '
                                f'in the server **{interaction.guild}**',
                    color=Color.gold()
                )
            )
        except: # the new leader does not admint dm
            pass
        
        await interaction.followup.send(
            f"Done! you are no longer the leader of **{tribe.name}** and {new_leader.mention} is.",
            ephemeral=True
        )
        
    
async def setup(bot: TribalBot):
    await bot.add_cog(TribeCog(bot))
        