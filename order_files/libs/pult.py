from order_files.work_materials.pult_constants import castles as castles_const, times as times_const, \
    tactics as tactics_const, defense as defense_const, divisions as divisions_const, pult_status_default

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class Pult:
    pults = {}

    def __init__(self, message_id, deferred_time=None):
        self.id = message_id
        self.status = pult_status_default.copy()
        self.divisions = divisions_const.copy()
        self.divisions[-1] = '✅' + self.divisions[-1]
        self.all_division_num = self.divisions.index('✅ВСЕ')
        self.divisions_active = [False, False, False, True]
        self.castles = castles_const.copy()
        self.times = times_const.copy()
        self.tactics = tactics_const.copy()
        self.defense = defense_const.copy()
        self.deferred_time = deferred_time
        print(self.deferred_time)
        Pult.pults.update({self.id: self})

    @staticmethod
    def get_pult(message_id):
        return Pult.pults.get(message_id) or Pult(message_id)


def build_pult(divisions, castles, times, defense, tactics):
    __pult_buttons = [
        [
            InlineKeyboardButton(divisions[0], callback_data="pdv0"),
            InlineKeyboardButton(divisions[1], callback_data="pdv1"),
            InlineKeyboardButton(divisions[2], callback_data="pdv2"),
            InlineKeyboardButton(divisions[3], callback_data="pdv3"),
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
            InlineKeyboardButton(defense[0], callback_data="pds0"),
            InlineKeyboardButton(defense[1], callback_data="pds1"),
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

    PultMarkup = InlineKeyboardMarkup(__pult_buttons)
    return PultMarkup


def rebuild_pult(action, pult, context):
    if action == "default":
        for i in range(0, len(pult.divisions) - 1):
            pult.divisions[i] = divisions_const[i]
            pult.divisions_active[i] = False
        for i in range (0, len(pult.castles)):
            pult.castles[i] = castles_const[i]
        for i in range (0, len(pult.times)):
            pult.times[i] = times_const[i]
        for i in range (0, len(pult.defense)):
            pult.defense[i] = defense_const[i]
        for i in range (0, len(pult.tactics)):
            pult.tactics[i] = tactics_const[i]
        new_markup = build_pult(pult.divisions, pult.castles, pult.times, pult.defense, pult.tactics)
        return new_markup
    if action == "change_division":
        if context == pult.all_division_num:
            for i in range (0, len(pult.divisions) - 1):
                pult.divisions[i] = divisions_const[i]
                pult.divisions_active[i] = False
        else:
            if pult.divisions_active[pult.all_division_num]:
                pult.divisions[pult.all_division_num] = divisions_const[pult.all_division_num]
                pult.divisions_active[pult.all_division_num] = False
        if pult.divisions_active[context]:
            pult.divisions[context] = divisions_const[context]
            pult.divisions_active[context] = False
        else:
            pult.divisions[context] = '✅' + pult.divisions[context]
            pult.divisions_active[context] = True
        new_markup = build_pult(pult.divisions, pult.castles, pult.times, pult.defense, pult.tactics)
        return_value = [new_markup, pult.divisions_active]
        return return_value
    if action == "change_target":
        for i in range (0, len(pult.castles)):
            pult.castles[i] = castles_const[i]
        pult.castles[context] = '✅' + pult.castles[context]
        new_markup = build_pult(pult.divisions, pult.castles, pult.times, pult.defense, pult.tactics)
        return new_markup
    if action == "change_time":
        for i in range (0, len(pult.times)):
            pult.times[i] = times_const[i]
        pult.times[context] = '✅' + pult.times[context]
        new_markup = build_pult(pult.divisions, pult.castles, pult.times, pult.defense, pult.tactics)
        return new_markup
    if action == "change_defense":
        for i in range (0, len(pult.defense)):
            pult.defense[i] = defense_const[i]
        pult.defense[context] = '✅' + pult.defense[context]
        new_markup = build_pult(pult.divisions, pult.castles, pult.times, pult.defense, pult.tactics)
        return new_markup
    if action == "change_tactics":
        for i in range (0, len(pult.tactics)):
            pult.tactics[i] = tactics_const[i]
        pult.tactics[context] = '✅' + pult.tactics[context]
        new_markup = build_pult(pult.divisions, pult.castles, pult.times, pult.defense, pult.tactics)
        return new_markup
