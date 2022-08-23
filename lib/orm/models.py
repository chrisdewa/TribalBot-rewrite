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
    tribes: fields.ReverseRelation['Tribe']
    categories: fields.ReverseRelation['TribeCategory']
    leaders_role = fields.IntField(default=None)
    urls = fields.BooleanField(default=False)
    
    class Meta:
        table = "guild_configs"


class LogEntry(Model):
    tribe = fields.ForeignKeyField('models.Tribe', related_name='log_entries', on_delete=fields.CASCADE)
    text = fields.TextField()
    created = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = 'log_entries'


class TribeCategory(Model):
    guild_config = fields.ForeignKeyField('models.GuildConfig', related_name='categories', on_delete=fields.CASCADE)
    name = fields.CharField(max_length=30)
    tribes: fields.ReverseRelation['Tribe']
    
    class Meta:
        table = "tribe_categories"

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
    log_entries: fields.ReverseRelation[LogEntry]

    
    class Meta:
        table = "tribes"

    
    
    