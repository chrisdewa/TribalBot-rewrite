from email.policy import default
from tortoise import fields
from tortoise.models import Model

from functools import partial

__all__ = [
    'GuildConfig',
    'TribeCategory',
    'Tribe',
]

_default_members = partial(list.copy, [])
_default_banner = partial(dict.copy, {'title': '', 'description': '', 'image': ''})


class GuildConfig(Model):
    guild_id = fields.IntField(pk=True)
    

class TribeCategory(Model):
    guild_config = fields.ForeignKeyField('models.GuildConfig', related_name='categories', on_delete=fields.CASCADE)
    name = fields.CharField(max_length=30)


class Tribe(Model):
    guild_config = fields.ForeignKeyField('models.GuildConfig', related_name='tribes', on_delete=fields.CASCADE)
    name = fields.CharField(max_length=30)
    leader = fields.IntField()
    manager = fields.IntField(null=True)
    members = fields.JSONField(default=_default_members)
    banner = fields.JSONField(default=_default_banner)
    created = fields.DatetimeField(auto_now_add=True)
    category = fields.ForeignKeyField('models.TribeCategory', related_name='tribes', on_delete=fields.CASCADE, null=True)
    color = fields.IntField(default=16711680)
    

    
    
    