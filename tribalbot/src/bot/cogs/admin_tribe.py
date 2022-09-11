from discord.ext.commands import Cog
from discord import app_commands, Interaction

from ..bot import TribalBot
from tribalbot.src.utils.tribes import *
from tribalbot.src.controllers.tribes import handle_leader_leave

from ._utils import get_tribe



class AdminTribeCog(Cog, description='Tribe Commands for Admins'):
    def __init__(self, bot) -> None:
        self.bot: TribalBot = bot
        print(f'[+] {self.qualified_name} loaded')
    
    async def cog_unload(self) -> None:
        print(f'[-] {self.qualified_name} unloaded')
    
    @app_commands.command(
        tribe_name='tribe-force-disband',
        description='Disolves the target tribe. Requieres Manage Server permission'
    )
    @app_commands.describe(tribe_name='The trib eyou want to disolve')
    @app_commands.rename(tribe_name='tribe-name')
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def tribe_force_disband_cmd(
        self, 
        interaction: Interaction,
        tribe_name: str
    ):
        tribe = await get_tribe(interaction, tribe_name)
        if not tribe: return
        
        
        leader = interaction.guild.get_member(tribe.leader)
        manager = interaction.guild.get_member(tribe.manager)
        embed = Embed(
                title='Tribe Deleted by an Admin',
                description=f'Your tribe has been deleted by an admin. Details below.',
                color=Color.from_rgb(0,0,0)
            ) \
                .add_field(name='Tribe', value=tribe.name) \
                .add_field(name='Server', value=interaction.guild.name)
                
        
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
            
        
        for m in (leader, manager):
            if m:
                try:
                    await m.send(embed=embed)
                except: pass # members don't support dms

        await tribe.delete()
        
        await interaction.response.send_message(
            f'Done! the tribe "**{tribe.name}**" has been deleted.',
            ephemeral=True
        )
        
    @app_commands.command(name='tribe-force-kick')
    @app_commands.describe(tribe_name='The target tribe', member='the target member')
    @app_commands.rename(tribe_name='tribe-name')
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def force_kick_cmd(
        self, 
        interaction: Interaction, 
        tribe_name: str,
        member: Member
    ):
        tribe = await get_tribe(interaction, tribe_name)
        if not tribe: return
        
        members = TribeMemberCollection(await tribe.members)
        
        save_tribe = True
        if tribe.leader == member.id:
            result = await handle_leader_leave(tribe, members)
            if result:
                new_leader = interaction.guild.get_member(tribe.leader)
                
                try:
                    await new_leader.send(embed=Embed(
                        title='Tribe Notificaction',
                        description=f'You have been appointed as the new leader of '
                                    f'**{tribe.name}** in the server "**{interaction.guild.name}**" '
                                    f'because the old leader was forced to leave by a server admin.',
                        color=Color.purple()
                    ))
                except: pass # new leader is not accepting dms
                
                return await interaction.response.send_message(
                    f'Done! {member.mention} has been kicked from "**{tribe.name}**" '
                    f'and {new_leader.mention} was appointed as the new leader',
                    ephemeral=True
                )
        elif member.id in members.ids:
            await members.remove_member(member.id)
            if member.id == tribe.manager:
                tribe.manager = None

        else:
            save_tribe = False
        
        if save_tribe:
            try:
                await member.send(embed=Embed(
                    title='An admin kicked you from a tribe',
                    description=f'Server: **{interaction.guild.name}**\n'
                                f'Tribe: **{tribe.name}**',
                    color=Color.red()
                ))
            except: pass # member does not allow dms
            await tribe.save()
        
        return await interaction.response.send_message(
            f'{member.mention} is not part of the tribe "**{tribe.name}**"',
            ephemeral=True
        )
        
        

async def setup(bot: TribalBot):
    await bot.add_cog(AdminTribeCog(bot))
        