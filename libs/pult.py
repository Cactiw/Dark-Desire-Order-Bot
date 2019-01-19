import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

castles =       ['🍆', '🍁', '☘', '🌹', '🐢', '🦇', '🖤']
castles_const = ['🍆', '🍁', '☘', '🌹', '🐢', '🦇', '🖤']


def build_pult(castles):
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
            InlineKeyboardButton("📢 SEND 📢", callback_data="ps")
        ]
    ]

    PultMarkup = InlineKeyboardMarkup(__pult_buttons)
    return PultMarkup


def rebuild_pult(action, context):
    global castles
    if action == "change_target":
        logging.info("castles = {0}".format(castles))
        for i in range (0, len(castles)):
            castles[i] = castles_const[i]
        logging.info("castles = {0}".format(castles))
        castles[context] = '✅' + castles[context]
        #logging.info("castles = {0}".format(castles))
        new_markup = build_pult(castles)
        return new_markup