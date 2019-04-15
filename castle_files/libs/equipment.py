"""
В этом модуле определён класс для хранения элементов экипировки.
Класс хранит тип(первая буква кода вещи), код (без типа),
имя и статы вещи.
"""


class Equipment:
    def __init__(self, place, item_type, code, name, attack, defense, tier):
        self.place = place
        self.type = item_type
        self.code = code
        self.name = name
        self.attack = attack
        self.defense = defense
        self.tier = tier

    def to_json(self):
        return {
            "code": self.type + self.code,
            "name": self.name,
            "attack": self.attack,
            "defense": self.defense
        }

    def __eq__(self, other):
        # Шмотка равна другой при совпадении типа и кода (нужно ещё подумать потом)
        return self.type == other and self.code == other.code
