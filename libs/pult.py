import logging
from work_materials.globals import castles as castles_const, times as times_const

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

castles = ['🍆', '🍁', '☘', '🌹', '🐢', '🦇', '🖤']
times = ["⚠️", "58", "59", "30", "40", "45"]

def build_pult(castles, times):
    __pult_buttons = [
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
            InlineKeyboardButton("📢 SEND 📢", callback_data="ps")
        ]
    ]

    PultMarkup = InlineKeyboardMarkup(__pult_buttons)
    return PultMarkup


def rebuild_pult(action, context):
    global castles
    if action == "change_target":
        for i in range (0, len(castles)):
            castles[i] = castles_const[i]
        castles[context] = '✅' + castles[context]
        new_markup = build_pult(castles, times)
        return new_markup
    if action == "change_time":
        for i in range (0, len(times)):
            times[i] = times_const[i]
        times[context] = '✅' + times[context]
        new_markup = build_pult(castles, times)
        return new_markup
