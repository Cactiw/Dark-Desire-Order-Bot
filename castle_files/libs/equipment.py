"""
В этом модуле определён класс для хранения элементов экипировки.
Класс хранит тип(первая буква кода вещи), код (без типа),
имя и статы вещи.
"""
import json


class Equipment:
    quality = {"Fine": "E", "High": "D", "Great": "C", "Excellent": "B", "Masterpiece": "A"}

    def __init__(self, place, item_type, code, name, attack, defense, tier, condition=None, quality=None):
        self.place = place
        self.type = item_type
        self.code = code
        self.name = name
        self.attack = attack
        self.defense = defense
        self.tier = tier
        self.condition = condition
        self.quality = quality

        self.source_name = self.name

    def set_code(self, code):
        self.type = code[0]
        self.code = code[1:]

    def to_json(self):
        dictionary = {
            "code": self.type + self.code,
            "name": self.name,
            "attack": self.attack,
            "defense": self.defense,
            "quality": self.quality,
            "condition": self.condition
        }
        return json.dumps(dictionary)

    def __eq__(self, other):
        # Шмотка равна другой при совпадении типа и кода (нужно ещё подумать потом)
        return self.type == other and self.code == other.code
