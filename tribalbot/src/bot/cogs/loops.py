from discord import Member, RawMemberRemoveEvent
from discord import app_commands, Interaction
from discord.ext.commands import Cog
from discord.ext import tasks
from discord.ext.tasks import Loop

from ..bot import TribalBot
from ._utils import notify_new_tribe_leader
from tribalbot.src.orm.models import Tribe, GuildConfig
from tribalbot.src.utils.cache import clear_autocomplete_cache
from tribalbot.src.utils.tribes import TribeMemberCollection
from tribalbot.src.controllers.tribes import get_all_member_tribes, handle_leader_leave


class MonitorCog(Cog, description='Tribe Monitors'):
    def __init__(self, bot) -> None:
        self.bot: TribalBot = bot
        self.__loops: list[Loop] = []
        self.__loops.append(clear_autocomplete_cache)
        print(f'[+] {self.qualified_name} loaded')
    
    def register_loop(self, loop):
        self.__loops.append(loop)
        return loop
        
    async def cog_unload(self) -> None:
        print(f'[-] {self.qualified_name} unloaded')
    
    async def cog_load(self) -> None:
        for loop in self.__loops:
            await loop.start()
    
            
    @register_loop
    @tasks.loop(minutes=5)
    async def tribe_monitor(self):
        await self.bot.wait_until_ready()
        async for guild_config in GuildConfig.all():
            guild = self.bot.get_guild(guild_config.pk)
            if not guild: # the guild removed the bot
                await guild_config.delete() 
            else:
                tribes = await guild_config.tribes
                for tribe in tribes:
                    leader = guild.get_member(tribe.leader)
                    members = TribeMemberCollection(await tribe.members)
                    manager = tribe.manager
                    save_tribe = False
                    # first check members
                    for mid in members.ids: # each member id
                        member = guild.get_member(mid)
                        if not member:
                            await members.remove_member(mid)
                            if member == manager:
                                tribe.manager = None
                                save_tribe = True
                                
                    # check leader
                    if not leader:
                        await handle_leader_leave(tribe, members=members)
                        save_tribe = False
                        
                    if save_tribe: # only triggers if there's a leader and absent manager
                        await tribe.save()
    
    @Cog.listener('on_member_remove')
    async def remobe_member_from_tribes(self, member: Member):
        """
        Activates when a member leaves a server. 
        Scans tribes the member belonged to and clears it of them
        """
        tribes = await get_all_member_tribes(member)
        for tribe in tribes:
            members = TribeMemberCollection(await tribe.members)
            save_tribe = False
            if member.id == tribe.leader:
                result = await handle_leader_leave(tribe, members=members)
                if result and (new_leader := member.guild.get_member(tribe.leader)):
                    # so far handle_leader_leave does not check if the new leader is actually in the server...
                    await notify_new_tribe_leader(new_leader, tribe)
            else:
                await members.remove_member(member.id)
                if member.id == tribe.manager:
                    tribe.manager = None
                    save_tribe = True
                    
            if save_tribe:
                await tribe.save()
        

async def setup(bot: TribalBot):
    await bot.add_cog(MonitorCog(bot))
        