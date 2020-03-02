"""
Здесь находится класс Голосование (Vote) и все методы для работы с ним.
"""

from castle_files.work_materials.globals import conn, moscow_tz, classes_list

import json
import datetime

cursor = conn.cursor()


class Vote:
    active_votes = []
    def __init__(self, vote_id, name, text, variants, choices, started=None, duration=None, classes=None):
        self.id = vote_id
        self.name = name
        self.text = text
        self.variants = variants
        self.choices = choices
        self.started = started
        self.duration = duration
        self.classes = classes

    @staticmethod
    def fill_active_votes():
        cursor = conn.cursor()
        Vote.active_votes.clear()
        request = "select id from votes"
        cursor.execute(request)
        vote_ids = cursor.fetchall()
        for vote_id in vote_ids:
            vote = Vote.get_vote(vote_id)
            if vote.check_active():
                Vote.active_votes.append(vote)
        cursor.close()

    def get_choice(self, player_id):
        for i, ch in enumerate(self.choices):
            if player_id in ch:
                return i
        return None

    def check_player_class_suitable(self, player) -> bool:
        return self.classes is None or len(self.classes) == 0 or (
                player.game_class is not None and self.classes[classes_list.index(player.game_class)] is True)

    def check_active(self) -> bool:
        if self.started is None:
            return False
        return self.started + self.duration > datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)

    @staticmethod
    def get_vote(vote_id):
        cursor = conn.cursor()
        request = "select name, text, variants, choices, started, duration, classes from votes where id = %s"
        cursor.execute(request, (vote_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        name, text, variants, choices, started, duration, classes = row
        cursor.close()
        return Vote(vote_id, name, text, variants, choices=list(choices.values()), started=started, duration=duration,
                    classes=classes)

    def update(self):
        request = "update votes set name = %s, text = %s, variants = %s, choices = %s, started = %s, duration = %s, " \
                  "classes = %s where id = %s"
        choices = {}
        for i, ch in enumerate(self.choices):
            choices.update({i: ch})
        choices = json.dumps(choices)
        cursor.execute(request, (self.name, self.text, self.variants, choices, self.started, self.duration,
                                 self.classes, self.id))
        Vote.fill_active_votes()

