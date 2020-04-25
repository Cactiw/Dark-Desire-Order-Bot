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

    def set_from_json(self, equipment_list: dict):
        self.set_code(equipment_list.get("code"))
        self.name = equipment_list.get("name")
        self.attack = equipment_list.get("attack")
        self.defense = equipment_list.get("defense")
        self.quality = equipment_list.get("quality")
        self.condition = equipment_list.get("condition")

    def format(self) -> str:
        return "{}<b>{}</b>{}<code>{}</code><code>{}</code>" \
                    "\n".format("✨" if self.condition == 'reinforced' else "🔩" if self.condition == "broken"
                                else "", self.name, " {} ".format(self.quality) if self.quality else "",
                                " +{}⚔️ ".format(self.attack) if self.attack != 0 else "",
                                "+{}🛡 ".format(self.defense) if self.defense != 0 else "")

    def __eq__(self, other):
        # Шмотка равна другой при совпадении типа и кода (нужно ещё подумать потом)
        return self.type == other and self.code == other.code
