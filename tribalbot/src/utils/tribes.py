from discord import Embed, Color, Member, Guild

from tribalbot.src.orm.models import Tribe

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

