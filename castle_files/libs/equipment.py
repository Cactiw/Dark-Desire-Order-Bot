"""
В этом модуле определён класс для хранения элементов экипировки.
Класс хранит тип(первая буква кода вещи), код (без типа),
имя и статы вещи.
"""

from castle_files.libs.shop import Shop

from castle_files.work_materials.item_consts import items

import json
import re


class Equipment:
    quality = {"Fine": "E", "High": "D", "Great": "C", "Excellent": "B", "Masterpiece": "A",
               "Epic Fine": "SE", "Epic High": "SD", "Epic Great": "SC", "Epic Excellent": "SB",
               "Epic Masterpiece": "SA"}
    all_quality = ["No quality", "E", "D", "C", "B", "A", "CE", "CD", "CC", "CB", "CA"]
    emoji = {0: '', 1: '📕', 2: '📗', 3: '📘', 4: '📙', 5: '📒'}

    type_to_cw = {
        "main_hand": "weapon",
        "second_hand": "offhand",
        "head": "head",
        "gloves": "hands",
        "armor": "body",
        "boots": "feet",
        "cloaks": "coat"
    }

    types_to_guru = {
        "main_hand": "weapon",
        "second_hand": "shield",  # WHY?!
        "head": "helmet",
        "gloves": "gloves",
        "armor": "armor",
        "boots": "boots",
        "cloaks": "coat"
    }

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

        self.item = self.get_item()

        self.source_name = self.name

    def set_code(self, code):
        self.type = code[0]
        self.code = code[1:]
        quality = re.search("[a-z]+$", code)
        if quality is not None:
            self.quality = quality.group(0).upper()

    def get_item(self):
        lower_name = self.name.lower()
        for short_code, item in items.items():
            if lower_name == item[0].lower():
                return item
        return None

    @property
    def recipe_code(self):
        return "r" + (self.code if len(self.item) < len(list(items.values())[-1]) else self.item[-2])

    @property
    def part_code(self):
        return "k" + (self.code if len(self.item) < len(list(items.values())[-1]) else self.item[-1])

    def format_code(self) -> str:
        return self.type + self.code

    def get_tier_emoji(self) -> str:
        return self.emoji.get(self.tier)

    def get_clear_name(self) -> str:
        clear_name = re.search("(⚡?\\+?\\d*\\s)?(.+?)\\s", self.name + " ")
        return clear_name.group(2)

    def get_quality_type(self) -> str:
        """
        :return: Тип гуру, который подходит данной экипировке (так, как получается от АПИ ЧВ)
        """
        return self.types_to_guru.get(self.place)

    def get_quality_shops(self):
        shops = Shop.get_quality_shops(self.get_quality_type())
        return list(filter(lambda shop: self.name.lower() in map(lambda s: s.lower(), shop.get_offered_names()), shops))

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

    def get_expected_stats(self):
        if self.type == "u":
            # Пока статы таких предметов считать не умеем (заточки, не известно качество и тп)
            return 0, 0
        try:
            quality_bonus = self.all_quality.index(self.quality)
        except ValueError:
            quality_bonus = 0
        return self.attack + quality_bonus, self.defense + quality_bonus

    def format(self, mode=None) -> str:
        if mode == "guild":
            attack, defense = self.get_expected_stats()
            res = "<a href=\"t.me/share/url?url=/g_withdraw {} 1\">{}{}{}{}</a>" \
                  "\n".format(self.type + self.code,
                              "✨" if self.condition == 'reinforced' else "🔩" if self.condition == "broken"
                              else "", self.name, " {} ".format(self.quality) if self.quality else "",
                              "{}{}".format(" +{}⚔️ ".format(attack) if attack != 0 else "",
                                            "+{}🛡 ".format(defense) if defense != 0 else "") if attack and defense else
                              "</a> || <a href=\"t.me/share/url?url=/g_i {}\">(⚔️🛡Inspect)".format(self.format_code()))
        else:
            res = "{}<b>{}</b>{}<code>{}{}</code>" \
                  "\n".format("✨" if self.condition == 'reinforced' else "🔩" if self.condition == "broken"
                              else "", self.name, " {} ".format(self.quality) if self.quality else "",
                              " +{}⚔️ ".format(self.attack) if self.attack != 0 else "",
                              "+{}🛡 ".format(self.defense) if self.defense != 0 else "")
        return res

    def __eq__(self, other):
        # Шмотка равна другой при совпадении типа и кода (нужно ещё подумать потом)
        return self.type == other and self.code == other.code
