

from castle_files.work_materials.globals import moscow_tz, dispatcher

import time
import json
import random
import copy



class Quest:
    def __init__(self, id: int, quest_type: str, duration_type: str, description: str, objective, reward: int,
                 status: str, progress, started_time: time.time()):
        self.id = id
        self.type = quest_type
        self.duration_type = duration_type
        self.description = description
        self.objective = objective
        self.reward = reward
        self.status = status
        self.progress = progress
        self.started_time = started_time
        self.player = None
        pass

    def start(self):
        self.status = "Running"
        self.started_time = time.time()

    def update_progress(self, update_value):
        # This method should be reimplemented if quest structure is harder that just an int object
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

    def try_complete(self):
        if self.check_complete():
            self.complete()

    def check_complete(self):
        raise NotImplemented


class CollectResourceQuest(Quest):
    def __init__(self, id: int, resources: {str: int}, reward: int, status: str,
                 progress: {str: int}, started_time: time.time, objective_draft=None):
        self.objective_draft = objective_draft
        super(CollectResourceQuest, self).__init__(
            id=id, quest_type="collect_resource", duration_type="Daily", description="Собрать из квестов",
            objective=resources, reward=reward, status=status, progress=progress, started_time=started_time)

    def start(self):
        self.objective = {random.choice(self.objective_draft.get("available_resources")):
                          self.objective_draft.get("count")[0]}
        self.progress = {}
        super(CollectResourceQuest, self).start()

    def update_progress(self, update_value: {str: int}):
        if self.status != "Running":
            return
        for key, value in list(update_value.items()):
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


class FeedbackRequestQuest(Quest):
    pass



quests = {
    1: CollectResourceQuest(id=1, resources={}, reward=25, status="Closed", progress={}, started_time=None,
                            objective_draft={"available_resources": ["01", "02", "03", "04", "06", "08", "20"],
                                             "count": [10, 50]})
}
