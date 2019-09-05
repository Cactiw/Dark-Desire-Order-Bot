from telegram.ext import BaseFilter
from castle_files.work_materials.filters.general_filters import filter_is_pm
from castle_files.work_materials.globals import dispatcher, SUPER_ADMIN_ID, DEFAULT_CASTLE_STATUS


class FilterTechnicalTower(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["🔭 Башня ТехМаг наук",
                                                          "🔭TechMag Science Tower"] and \
            user_data.get("status") == 'central_square'


filter_technical_tower = FilterTechnicalTower()


class FilterManuscript(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["📰Манускрипт", "📰Инструкция",
                                                          "📰Manuscript", "📰Instruction"] and \
            user_data.get("status") in ['technical_tower', DEFAULT_CASTLE_STATUS, "rp_off"]


filter_manuscript = FilterManuscript()


class FilterGuides(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["📓Гайды", "📓Guides"] and \
               user_data.get("status") == 'manuscript'


filter_guides = FilterGuides()


class FilterViewManuscriptCategory(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and \
            message.text in ["↔️Указатели", "👤Игроки", "👥Гильдии", "🖋Триггеры", "📦Сток", "🏠Профсоюзы",
                             "↔️Signs", "👤Players", "👥Guilds", "🖋Triggers", "📦Stock"] and \
            user_data.get("status") == 'manuscript'


filter_view_manuscript_category = FilterViewManuscriptCategory()


class FilterUpdateHistory(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and (message.text in ["🗂Архив объявлений", "🗂Announcements archive"] and
                                          user_data.get("status") == 'technical_tower') or \
            message.text in ["🗂Обновления", "🗂Updates"]


filter_update_history = FilterUpdateHistory()


class FilterMyCabinet(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text.startswith("💻Кабинет ботодела") and \
            user_data.get("status") == 'technical_tower' and message.from_user.id == SUPER_ADMIN_ID


filter_my_cabinet = FilterMyCabinet()


class FilterRequestChangeUpdateMessage(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text.startswith("📈Выкатить обнову") and \
            user_data.get("status") == 'my_cabinet' and message.from_user.id == SUPER_ADMIN_ID


filter_request_change_update_message = FilterRequestChangeUpdateMessage()


class FilterChangeUpdateMessage(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and user_data.get("status") == 'editing_update_message' and\
            message.from_user.id == SUPER_ADMIN_ID


filter_change_update_message = FilterChangeUpdateMessage()


class FilterRequestBotGuildMessageNotify(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text.startswith("📣Рассылка по гильдиям") and \
            user_data.get("status") == 'my_cabinet' and message.from_user.id == SUPER_ADMIN_ID


filter_request_bot_guild_message_notify = FilterRequestBotGuildMessageNotify()


class FilterSendBotGuildMessageNotify(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and user_data.get("status") == 'sending_bot_guild_message' and \
            message.from_user.id == SUPER_ADMIN_ID


filter_send_bot_guild_message_notify = FilterSendBotGuildMessageNotify()
