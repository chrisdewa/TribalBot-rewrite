from discord.utils import format_dt

from tortoise import fields

class CreatedMixin:
    created = fields.DatetimeField(auto_now_add=True)
    
    @property
    def pretty_dt(self) -> str:
        """Outputs the datetime of creation in a long date format for discord"""
        return format_dt(self.created, 'F')