"""
Здесь находится класс Голосование (Vote) и все методы для работы с ним.
"""

from castle_files.work_materials.globals import conn

import json

cursor = conn.cursor()


class Vote:
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
    def get_vote(vote_id):
        request = "select name, text, variants, choices, started, duration, classes from votes where id = %s"
        cursor.execute(request, (vote_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        name, text, variants, choices, started, duration, classes = row
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

