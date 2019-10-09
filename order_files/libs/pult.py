from order_files.work_materials.pult_constants import castles as castles_const, times as times_const, \
    tactics as tactics_const, defense as defense_const, divisions as divisions_const, pult_status_default, \
    potions as potions_const
from order_files.work_materials.globals import deferred_orders, moscow_tz, local_tz

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class Pult:
    pults = {}
    last_pult_id = 0
    variants = {}

    def __init__(self, chat_id, message_id, deferred_time=None, variant=None):
        self.id = message_id
        self.chat_id = chat_id
        self.status = pult_status_default.copy()
        self.divisions = divisions_const.copy()
        self.divisions[-1] = '✅' + self.divisions[-1]
        self.rangers_division_num = self.divisions.index("Луки")
        self.all_attackers_division_num = self.divisions.index('Все атакеры')
        self.all_division_num = self.divisions.index('✅ВСЕ')
        self.divisions_active = [False, False, False, False, False, False, True]
        self.castles = castles_const.copy()
        self.times = times_const.copy()
        self.potions = potions_const.copy()
        self.potions_active = [False, False]
        self.tactics = tactics_const.copy()
        self.defense = defense_const.copy()
        self.deferred_time = deferred_time
        self.variant = variant
        Pult.pults.update({self.id: self})
        if not self.variant:
            Pult.last_pult_id = self.id

    @staticmethod
    def get_pult(chat_id, message_id):
        return Pult.pults.get(message_id) or Pult(chat_id, message_id)

    def get_reply_markup(self):
        return rebuild_pult("None", self, None)

    @staticmethod
    def get_text():
        response = ""
        for order in deferred_orders:
            div_str = ""
            for i in range(len(divisions_const)):
                if order.divisions[i]:
                    div_str += " {0}".format(divisions_const[i])
            response += "{5}\n{0} -- {1}\n{2}{3}{6}{7}remove: /remove_order_{4}\n" \
                        "\n".format(local_tz.localize(order.time_set.replace(tzinfo=None)).astimezone(
                            tz=moscow_tz).replace(tzinfo=None).strftime("%d/%m/%y %H:%M:%S"),
                                    order.target, "🛡:{}\n".format(order.target if order.defense == "Attack!" else
                                                                   order.defense) if order.defense is not None else "",
                                    "Тактика: {}\n".format(order.tactics) if order.tactics != "" else "",
                                    order.deferred_id, div_str[1:],
                                    "⚗️ Атака\n" if order.potions[0] else "", "⚗️ Деф\n" if order.potions[1] else "",
                                    div_str[1:]
                                    )
        return response


def build_pult(divisions, castles, times, defense, tactics, potions, deferred_time=None, variant=None):
    __pult_buttons = [
        [
            InlineKeyboardButton(divisions[0], callback_data="pdv0"),
            InlineKeyboardButton(divisions[1], callback_data="pdv1"),
            InlineKeyboardButton(divisions[2], callback_data="pdv2"),
            InlineKeyboardButton(divisions[4], callback_data="pdv4"),  # Луки
        ],
        [
            InlineKeyboardButton(divisions[3], callback_data="pdv3"),
            InlineKeyboardButton(divisions[5], callback_data="pdv5"),
            InlineKeyboardButton(divisions[6], callback_data="pdv6"),

        ],
        [
            InlineKeyboardButton(castles[0], callback_data="pc0"),
            InlineKeyboardButton(castles[1], callback_data="pc1"),
            InlineKeyboardButton(castles[2], callback_data="pc2"),
        ],
        [
            InlineKeyboardButton(castles[3], callback_data="pc3"),
            InlineKeyboardButton(castles[4], callback_data="pc4"),
            InlineKeyboardButton(castles[5], callback_data="pc5"),
        ],
        [
            InlineKeyboardButton(castles[6], callback_data="pc6"),
        ],
        [
            InlineKeyboardButton(times[0], callback_data="pt0"),
            InlineKeyboardButton(times[1], callback_data="pt1"),
            InlineKeyboardButton(times[2], callback_data="pt2"),
            InlineKeyboardButton(times[3], callback_data="pt3"),
            InlineKeyboardButton(times[4], callback_data="pt4"),
            InlineKeyboardButton(times[5], callback_data="pt5"),
        ],
        [
            InlineKeyboardButton(potions[0], callback_data="pp0"),
            InlineKeyboardButton(potions[1], callback_data="pp1"),
        ],
        [
            InlineKeyboardButton(defense[1], callback_data="pds1"),
            InlineKeyboardButton(defense[0], callback_data="pds0"),
        ],
        [
            InlineKeyboardButton(tactics[0], callback_data="pdt0"),
            InlineKeyboardButton(tactics[1], callback_data="pdt1"),
            InlineKeyboardButton(tactics[2], callback_data="pdt2"),
            InlineKeyboardButton(tactics[3], callback_data="pdt3"),
            InlineKeyboardButton(tactics[4], callback_data="pdt4"),
        ],
        [
            InlineKeyboardButton("📢 SEND 📢", callback_data="ps")
        ]
    ]
    if deferred_time is not None or variant is not None:
        __pult_buttons.pop(5)
    PultMarkup = InlineKeyboardMarkup(__pult_buttons)
    return PultMarkup


def rebuild_pult(action, pult, context):
    if action == "None":
        return build_pult(pult.divisions, pult.castles, pult.times, pult.defense, pult.tactics, pult.potions,
                          deferred_time=pult.deferred_time)
    if action in ["default", "default_deferred", "default_variant"]:
        variant = None
        if "variant" in action:
            variant = True
        for i in range(0, len(pult.divisions) - 1):
            pult.divisions[i] = divisions_const[i]
            pult.divisions_active[i] = False
        for i in range(0, len(pult.castles)):
            pult.castles[i] = castles_const[i]
        for i in range(0, len(pult.times)):
            pult.times[i] = times_const[i]
        for i in range(0, len(pult.defense)):
            pult.defense[i] = defense_const[i]
        for i in range(0, len(pult.tactics)):
            pult.tactics[i] = tactics_const[i]
        deferred_time = None
        if action == "default_deferred":
            deferred_time = 1
        new_markup = build_pult(pult.divisions, pult.castles, pult.times, pult.defense, pult.tactics, pult.potions,
                                deferred_time=deferred_time, variant=variant)
        return new_markup
    if action == "change_division":
        if context in [pult.all_division_num, pult.all_attackers_division_num, pult.rangers_division_num]:
            for i in range(len(pult.divisions)):
                pult.divisions[i] = divisions_const[i]
                pult.divisions_active[i] = False
        else:
            for i in [pult.all_division_num, pult.all_attackers_division_num, pult.rangers_division_num]:
                pult.divisions[i] = divisions_const[i]
                pult.divisions_active[i] = False
        if pult.divisions_active[context]:
            pult.divisions[context] = divisions_const[context]
            pult.divisions_active[context] = False
        else:
            pult.divisions[context] = '✅' + pult.divisions[context]
            pult.divisions_active[context] = True
        new_markup = build_pult(pult.divisions, pult.castles, pult.times, pult.defense, pult.tactics, pult.potions,
                                deferred_time=pult.deferred_time, variant=pult.variant)
        return_value = [new_markup, pult.divisions_active]
        return return_value
    if action == "change_target":
        for i in range (0, len(pult.castles)):
            pult.castles[i] = castles_const[i]
        pult.castles[context] = '✅' + pult.castles[context]
        new_markup = build_pult(pult.divisions, pult.castles, pult.times, pult.defense, pult.tactics, pult.potions,
                                deferred_time=pult.deferred_time, variant=pult.variant)
        return new_markup
    if action == "change_time":
        for i in range (0, len(pult.times)):
            pult.times[i] = times_const[i]
        pult.times[context] = '✅' + pult.times[context]
        new_markup = build_pult(pult.divisions, pult.castles, pult.times, pult.defense, pult.tactics, pult.potions,
                                deferred_time=pult.deferred_time, variant=pult.variant)
        return new_markup
    if action == "change_defense":
        for i in range (0, len(pult.defense)):
            pult.defense[i] = defense_const[i]
        pult.defense[context] = '✅' + pult.defense[context]
        new_markup = build_pult(pult.divisions, pult.castles, pult.times, pult.defense, pult.tactics, pult.potions,
                                deferred_time=pult.deferred_time, variant=pult.variant)
        return new_markup
    if action == "change_tactics":
        for i in range (0, len(pult.tactics)):
            pult.tactics[i] = tactics_const[i]
        if context == pult.status.get("tactics"):
            pass
        else:
            pult.tactics[context] = '✅' + pult.tactics[context]
        new_markup = build_pult(pult.divisions, pult.castles, pult.times, pult.defense, pult.tactics, pult.potions,
                                deferred_time=pult.deferred_time, variant=pult.variant)
        return new_markup
    if action == "change_potions":
        if pult.potions[context].startswith('✅'):
            pult.potions[context] = pult.potions[context][1:]
        else:
            pult.potions[context] = '✅' + pult.potions[context]
        pult.potions_active[context] = not pult.potions_active[context]
        return build_pult(pult.divisions, pult.castles, pult.times, pult.defense, pult.tactics, pult.potions,
                          deferred_time=pult.deferred_time, variant=pult.variant)

