from telegram.ext import BaseFilter
from castle_files.bin.trigger import triggers_in, global_triggers_in
from castle_files.work_materials.filters.general_filters import filter_is_pm


class FilterIsTrigger(BaseFilter):
    def filter(self, message):
        local_triggers = triggers_in.get(message.chat_id)
        return not filter_is_pm and ((local_triggers is not None and message.text.lower() in local_triggers) or
                                     message.text.lower() in global_triggers_in)


filter_is_trigger = FilterIsTrigger()
