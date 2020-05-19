

from castle_files.work_materials.globals import moscow_tz, dispatcher

from castle_files.bin.stock_service import get_item_name_by_code

import time
import json
import random
import copy


class Quest:
    ALL_DAILY_QUESTS_REWARD = 100

    def __init__(self, id: int, quest_type: str, duration_type: str, description: str, objective, reward: int,
                 status: str, progress, started_time: time.time(), daily_unique=False, skip_selection: bool = False):
        self.id = id
        self.type = quest_type
        self.duration_type = duration_type
        self.description = description
        self.objective = objective
        self.reward = reward
        self.status = status
        self.progress = progress
        self.started_time = started_time
        self.daily_unique = daily_unique
        self.skip_selection = skip_selection
        self.player = None
        pass

    def start(self, player):
        self.player = player
        self.status = "Running"
        self.started_time = time.time()

    def update_progress(self, update_value):
        # This method should be reimplemented if quest structure is harder that just an int object
        if self.status != "Running":
            return
        self.progress += update_value
        self.try_complete()

    def to_dict(self):
        return {"id": self.id, "objective": self.objective, "status": self.status, "progress": self.progress,
                "started_time": self.started_time}

    @staticmethod
    def from_dict(d: dict):
        quest = copy.deepcopy(quests.get(d["id"]))
        for k, v in list(d.items()):
            try:
                setattr(quest, k, v)
            except AttributeError:
                pass
        return quest

    def complete(self):
        self.player.reputation += self.reward
        self.status = "Completed"
        self.player.update()
        dispatcher.bot.send_message(
            chat_id=self.player.id, text="Квест выполнен.\nПолучено: <b>{}</b>🔘".format(self.reward), parse_mode='HTML')

        if self.duration_type == "Daily":
            daily_quests: [Quest] = self.player.quests_info.get("daily_quests")
            if not daily_quests:
                return
            for quest in daily_quests:
                if quest.status != "Completed":
                    return
            self.player.reputation += self.ALL_DAILY_QUESTS_REWARD
            self.player.update()
            dispatcher.bot.send_message(chat_id=self.player.id, text="Все ежедневные квесты выполнены.\n"
                                        "Получено: <b>{}</b>🔘".format(self.ALL_DAILY_QUESTS_REWARD), parse_mode='HTML')

    def try_complete(self):
        if self.check_complete():
            self.complete()

    def check_complete(self) -> bool:
        """It is assumed that self.progress and self.objective are int objects.
        If not, then implement this method on your own."""
        try:
            return self.progress >= self.objective
        except Exception:
            raise NotImplemented

    def get_description(self):
        return ("✅" if self.status == "Completed" else "") + self.description.format(self.objective) + \
               " (<b>{} / {}</b>)".format(
            self.progress if self.progress <= self.objective else self.objective, self.objective)



class CollectResourceQuest(Quest):
    def __init__(self, id: int, resources: {str: int}, reward: int, status: str,
                 progress: {str: int}, started_time: time.time, objective_draft=None, daily_unique=False):
        self.objective_draft = objective_draft
        quest_type = "castle_collect_resource" if list(objective_draft["available_resources"])[0] in [
            "🌲Wood", "⛰Stone"] else "collect_resource"
        super(CollectResourceQuest, self).__init__(
            id=id, quest_type=quest_type, duration_type="Daily", description="Собрать в квестах ",
            objective=resources, reward=reward, status=status, progress=progress, started_time=started_time,
            daily_unique=daily_unique)

    def start(self, player):
        self.objective = {random.choice(self.objective_draft.get("available_resources")):
                          self.objective_draft.get("count")[0]}
        self.progress = {}
        super(CollectResourceQuest, self).start(player)

    def update_progress(self, update_value: {str: int}):
        if self.status != "Running":
            return
        for key, value in list(update_value.items()):
            print(key, value, self.objective)
            if key not in self.objective:
                continue
            old_value = self.progress.get(key) or 0
            self.progress.update({key: old_value + value})
        self.try_complete()


    def check_complete(self) -> bool:
        for key, need_value in list(self.objective.items()):
            have_value = self.progress.get(key) or 0
            if have_value < need_value:
                return False
        return True

    def get_description(self):
        text = ("✅" if self.status == "Completed" else "") + self.description
        for k, v in list(self.objective.items()):
            got_value = self.progress.get(k) or 0
            if got_value > v:
                got_value = v
            text += "<b>{}</b> x{} (<b>{} / {}</b>)\n".format(get_item_name_by_code(k), v, got_value, v)
        return text[:-1]


#
# class FeedbackRequestQuest(Quest):
#     def __init__(self, id: int, quest_type: str, objective, reward: int, status: str,
#                  progress: int, started_time: time.time):
#         super(FeedbackRequestQuest, self).__init__(
#             id, quest_type, "daily", "Обратиться к {}", objective, reward, status, progress, started_time)
#




quests = {
    1: CollectResourceQuest(id=1, resources={}, reward=25, status="Closed", progress={}, started_time=None,
                            objective_draft={"available_resources": ["01", "02", "03", "04", "06", "08", "20"],
                                             "count": [10, 50]}),
    2: Quest(id=2, quest_type="feedback_request_mid", duration_type="Daily", objective=1,
             description="Обратиться к миду <b>{}</b> раз", reward=25, status="Closed", progress=0, started_time=None,
             daily_unique=True),
    3: Quest(id=3, quest_type="feedback_request_duty", duration_type="Daily", objective=1,
             description="Обратиться к стражникам <b>{}</b> раз", reward=25, status="Closed", progress=0,
             started_time=None, daily_unique=True),
    4: Quest(id=4, quest_type="feedback_request_king", duration_type="Daily", objective=1,
             description="Попросить аудиенции у Короля", reward=25, status="Closed", progress=0,
             started_time=None, daily_unique=True, skip_selection=True),
    5: CollectResourceQuest(id=5, resources={}, reward=25, status="Closed", progress={}, started_time=None,
                            objective_draft={"available_resources": ["🌲Wood", "⛰Stone"],
                                             "count": [3, 15]}, daily_unique=True),
    6: Quest(id=6, quest_type="reports", duration_type="Daily", objective=3,
             description="Посетить <b>{}</b> битвы", reward=25, status="Closed", progress=0,
             started_time=None, daily_unique=True),
    7: Quest(id=7, quest_type="doc_statuses", duration_type="Daily", objective=3,
             description="/doc <b>{}</b> человека со статусом", reward=25, status="Closed", progress=0,
             started_time=None, daily_unique=True),
    8: Quest(id=8, quest_type="arena_win", duration_type="Daily", objective=3,
             description="Выиграть <b>{}</b> арены", reward=25, status="Closed", progress=0,
             started_time=None, daily_unique=True),

}
