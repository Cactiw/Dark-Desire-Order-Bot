from telegram.ext import BaseFilter
from work_materials.globals import admin_ids


class FilterIsAdmin(BaseFilter):
    def filter(self, message):
        return message.from_user.id in admin_ids

filter_is_admin = FilterIsAdmin()