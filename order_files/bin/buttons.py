from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# castles_unicode = {'🍁': '\uD83C\uDF41', '☘': '\u2618\uFE0F', '🖤': '\uD83D\uDDA4', '🐢': '\uD83D\uDC22',
#                    '🦇': '\uD83E\uDD87', '🌹': '\uD83C\uDF39', '🍆': '\uD83C\uDF46',
#                    '🦌Деф!🛡': '🦌'}
castles_unicode = {'🌑': '🌑', '☘': '☘', '☘️': '☘️', '🐉': '🐉', '🐢': '🐢',
                   '🐺': '🐺', '🦈': '🦈', '🥔': '🥔', '🦅': '🦅', '🦌': '🦌',
                   '🦌Деф!🛡': '🦌'}


def get_order_buttons(attack, defense):
    buttons = [
        [
            InlineKeyboardButton(url=u"https://t.me/share/url?url={}".format(castles_unicode.get(attack)),
                                 text=u"⚔️{}".format(castles_unicode.get(attack))),
            ],
    ]
    if defense == "Attack!":
        buttons.append([
            InlineKeyboardButton(url=u"https://t.me/share/url?url={}".format(castles_unicode.get(attack)),
                                 text=u"🛡️{}".format(castles_unicode.get(attack)))
        ])
    elif defense is not None:
        buttons.append([
            InlineKeyboardButton(url=u"https://t.me/share/url?url={}".format(castles_unicode.get('🦌')),
                                 text="🛡️{}".format(castles_unicode.get('🦌')))
        ])
    buttons.append([
        InlineKeyboardButton(url="t.me/ChatWarsBot", text="ChatWars")
    ])
    return InlineKeyboardMarkup(buttons)
