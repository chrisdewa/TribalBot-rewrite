from discord import Embed, Color, Member, Guild

from tribalbot.src.orm.models import Tribe
from tribalbot.src.utils.misc import contains_urls

def get_tribe_embed(tribe: Tribe, guild: Guild) -> Embed:
    """Outputs an embed describing the tribe and its members"""
    embed = Embed(
        title=tribe.name,
        color=tribe.color,
    )
    
    leader = guild.get_member(tribe.leader)
    embed.add_field(name='Leader', value=f'{leader}')
    
    if tribe.manager:
        embed.add_field(name='Manager', value=f'{guild.get_member(tribe.manager) or tribe.manager}', inline=False)
    members = ''
    for tm in tribe.members:
        mid = tm.member_id
        m = guild.get_member(mid) or mid
        members += f'{m or mid}\n'
    if members:
        embed.add_field(name='Members', value=members or 'None yet')

    if img := tribe.banner.get('image'):
        embed.set_thumbnail(url=img)
    
    return embed


def tribe_banner(tribe: Tribe, guild: Guild):
    embed = Embed(
        title=tribe.name,
        color=tribe.color,
        description=tribe.banner.get('description') or 'description empty'
    )
    
    if contains_urls(embed.description) and tribe.guild_config.urls is False:
        embed.description = 'Guild Settings disallow urls which the banner description contains. Talk to the server admins.'
    
    if image := tribe.banner.get('image'):
        embed.set_image(url=image)
    
    leader = guild.get_member(tribe.leader)
    
    embed.add_field(
        name='Leader', 
        value=leader or 'The leader is no longer part of the server... '
                        'ask the admins to appoint a new leader'
        )
    members = [m for mid in tribe.members if (m:=guild.get_member(mid.member_id))]
    embed.add_field(
        name='Members',
        value=str(len(members) + (1 if leader else 0)) # if the leader is part of the guild count it, if not, just skip it
    )
    
    return embed
    
        