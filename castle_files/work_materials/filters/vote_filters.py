"""
Здесь назодятся фильтры для работы с голосованиями
"""
from telegram.ext import BaseFilter

from castle_files.work_materials.globals import dispatcher

from castle_files.work_materials.filters.general_filters import filter_is_pm


# Добавление текста голосования
class FilterAddVoteText(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and user_data.get("status") == 'creating_vote_text'


filter_add_vote_text = FilterAddVoteText()


# Добавление варинта ответа в голосовании
class FilterAddVoteVariant(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and user_data.get("status") == 'creating_vote_variants'


filter_add_vote_variant = FilterAddVoteVariant()


# Информация о голосовании
class FilterViewVote(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and message.text.startswith("/view_vote_")


filter_view_vote = FilterViewVote()


# Запрос на изменение длительности голосования
class FilterRequestEditVoteDuration(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and message.text.startswith("/change_vote_duration_")


filter_request_edit_vote_duration = FilterRequestEditVoteDuration()


# Изменение длительноти голосования
class FilterEditVoteDuration(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and user_data.get("status") == 'editing_vote_duration'


filter_edit_vote_duration = FilterEditVoteDuration()


# Изменение классов голосования
class FilterEditVoteClasses(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and message.text.startswith("/set_vote_classes_")


filter_edit_vote_classes = FilterEditVoteClasses()


# Начало голосования
class FilterStartVote(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and message.text.startswith("/start_vote_")


filter_start_vote = FilterStartVote()


# Проголосовать
class FilterVote(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and message.text.startswith("/vote_")


filter_vote = FilterVote()


# Результаты голосования
class FilterVoteResults(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and message.text.startswith("/vote_results")


filter_vote_results = FilterVoteResults()






