import logging
from work_materials.pult_constants import castles as castles_const, times as times_const, tactics as tactics_const,\
    defense as defense_const, divisions as divisions_const

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

divisions = ['KYS', 'СКИ', 'ТЕСТ', '✅ВСЕ']
all_division_num = divisions.index('✅ВСЕ')
divisions_active = [False, False, False, True]
castles = ['🍆', '🍁', '☘', '🌹', '🐢', '🦇', '🖤']
times = ["⚠️", "58", "59", "30", "40", "45"]
tactics = ["/t\n🐢", "/t\n🌹","/t\n🦇","/t\n🍁", "/rand", ""]
defense = ["Деф дома 🖤", "/g_def", ""]

def build_pult(divisions, castles, times, defense, tactics):
    __pult_buttons = [
        [
            InlineKeyboardButton(divisions[0], callback_data="pd0"),
            InlineKeyboardButton(divisions[1], callback_data="pd1"),
            InlineKeyboardButton(divisions[2], callback_data="pd2"),
            InlineKeyboardButton(divisions[3], callback_data="pd3"),
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


def rebuild_pult(action, context):
    global castles
    if action == "default":
        for i in range (0, len(castles)):
            castles[i] = castles_const[i]
        for i in range (0, len(times)):
            times[i] = times_const[i]
        for i in range (0, len(tactics)):
            tactics[i] = tactics_const[i]
        new_markup = build_pult(divisions, castles, times, defense, tactics)
        return new_markup
    if action == "change_division":
        if context == all_division_num:
            for i in range (0, len(divisions) - 1):
                divisions[i] = divisions_const[i]
                divisions_active[i] = False
        else:
            if divisions_active[all_division_num]:
                divisions[all_division_num] = divisions_const[all_division_num]
                divisions_active[all_division_num] = False
        if divisions_active[context]:
            divisions[context] = divisions_const[context]
            divisions_active[context] = False
        else:
            divisions[context] = '✅' + divisions[context]
            divisions_active[context] = True
        new_markup = build_pult(divisions, castles, times, defense, tactics)
        return_value = [new_markup, divisions_active]
        return return_value
    if action == "change_target":
        for i in range (0, len(castles)):
            castles[i] = castles_const[i]
        castles[context] = '✅' + castles[context]
        new_markup = build_pult(divisions, castles, times, defense, tactics)
        return new_markup
    if action == "change_time":
        for i in range (0, len(times)):
            times[i] = times_const[i]
        times[context] = '✅' + times[context]
        new_markup = build_pult(divisions, castles, times, defense, tactics)
        return new_markup
    if action == "change_defense":
        for i in range (0, len(defense)):
            defense[i] = defense_const[i]
        defense[context] = '✅' + defense[context]
        new_markup = build_pult(divisions, castles, times, defense, tactics)
        return new_markup
    if action == "change_tactics":
        for i in range (0, len(tactics)):
            tactics[i] = tactics_const[i]
        tactics[context] = '✅' + tactics[context]
        new_markup = build_pult(divisions, castles, times, defense, tactics)
        return new_markup
