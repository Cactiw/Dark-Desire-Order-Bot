import datetime
from .drop_data_constants import *


# ReiRose LTD 2019


def count_next_daytime():
    next_daytime = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None, hour=1, minute=0, second=0,
                                                               microsecond=0)
    now = datetime.datetime.now().replace(tzinfo=None, hour=0)
    while next_daytime < now:
        next_daytime += datetime.timedelta(hours=2)
    if next_daytime.hour == 1 or next_daytime.hour == 3 or next_daytime.hour == 5 or\
       next_daytime.hour == 7 or next_daytime.hour == 9:
        time = '0' + str(next_daytime.hour)
    else:
        time = str(next_daytime.hour)
    return time


def qdrop(tier):
    text = "Сейчас в квестах можно найти:\n"
    try:
        daytime = daytime_table[count_next_daytime()]
        for quest in drop[tier]:
            text += '   <b>{}</b>:\n'.format(quest)
            for item in drop[tier][quest][daytime]:
                text += '      {};\n'.format(item)
            text += '\n'
        return text
    except KeyError:
        return 'KeyError'


def drop_table(bot, update):
    um = update.message
    try:
        tier = um.text[um.text.index(' ')+1:].lower()
        drop_tier = avalible_tiers[tier]
    except ValueError:
        drop_tier = 'Null'
    except KeyError:
        drop_tier = 'Null'
    text = qdrop(drop_tier)
    if text != 'KeyError':
        bot.sendMessage(chat_id=um.chat_id,
                        text=text,
                        parse_mode='HTML')
    else:
        bot.sendMessage(chat_id=um.chat_id,
                        text='Использование команды:\n'
                             '/drop <code>{T2/T3/T4}</code>',
                        parse_mode='HTML')
