from email.policy import default
from tortoise import fields
from tortoise.models import Model

from functools import partial

from lib.constants import DEFAULT_TRIBE_COLOR

__all__ = [
    'GuildConfig',
    'TribeCategory',
    'Tribe',
]

_default_members = partial(list.copy, [])
_default_banner = partial(dict.copy, {'title': '', 'description': '', 'image': ''})


class GuildConfig(Model):
    """Guild configuration model
    Contains the configurations for TribalBot for the corresponding server
    """
    guild_id = fields.IntField(pk=True)
    tribes: fields.ReverseRelation['Tribe']
    categories: fields.ReverseRelation['TribeCategory']
    leaders_role = fields.IntField(null=True)
    urls = fields.BooleanField(null=True)
    
    class Meta:
        table = "guild_configs"
    
    def __str__(self) -> str:
        return f'Guild(guild_id={self.guild_id})'
    
    def __repr__(self) -> str:
        return self.__str__()


class LogEntry(Model):
    """Log entry model for tribes.
    Contains a series of entries for "events" around tribes, for example, tribe creation, leadership change, etc.
    """
    tribe = fields.ForeignKeyField('models.Tribe', related_name='log_entries', on_delete=fields.CASCADE)
    text = fields.TextField()
    created = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = 'log_entries'


class TribeCategory(Model):
    """A gategory a tribe can be a part of.
    Categories are related to tribes in a One To Many way.
    One tribe can have only one category, but a single category can be used by any number of tribes in a server
    Tribe categories are also related to GuildConfigs in a One to Many way, since they can only have one server but
    a server can have any number of categories
    """
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
    color = fields.IntField(default=DEFAULT_TRIBE_COLOR)
    log_entries: fields.ReverseRelation[LogEntry]
    
    class Meta:
        table = "tribes"

    def __str__(self) -> str:
        return f'Tribe(pk={self.pk}, guild_id={self.guild_config_id}, name={self.name}, leader={self.leader})'
    
    def __repr__(self) -> str:
        return self.__str__()
    
    
    