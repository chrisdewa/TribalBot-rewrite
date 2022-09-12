from discord.ext.commands import Cog
from discord import app_commands, Interaction
from discord.ext import tasks
from discord.ext.tasks import Loop

from ..bot import TribalBot
from tribalbot.src.orm.models import Tribe, GuildConfig
from tribalbot.src.utils.cache import clear_autocomplete_cache
from tribalbot.src.utils.tribes import TribeMemberCollection
from tribalbot.src.controllers.tribes import handle_leader_leave


class GeneralLoopCog(Cog, description='Tribe related Loops'):
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
    @tasks.loop(minutes=1)
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
                    

async def setup(bot: TribalBot):
    await bot.add_cog(GeneralLoopCog(bot))
        