from castle_files.work_materials.drop_data_constants import *
from castle_files.work_materials.globals import moscow_tz

import datetime


# ReiRose LTD 2019


def count_next_daytime():
    next_daytime = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None, hour=1, minute=0, second=0,
                                                               microsecond=0)
    now = datetime.datetime.now().replace(tzinfo=None)
    while next_daytime < now:
        next_daytime += datetime.timedelta(hours=2)
    if next_daytime.hour == 1 or next_daytime.hour == 3 or next_daytime.hour == 5 or\
       next_daytime.hour == 7 or next_daytime.hour == 9:
        time = '0' + str(next_daytime.hour)
    else:
        time = str(next_daytime.hour)
    return time


def qdrop(tier):
    if tier == 'cloaks':
        text = "Сейчас падает из <i>Tier 3</i> (30-42 уровни):\n\n"
    else:
        text = "Сейчас падает из <i>{}</i>:\n\n".format(tier)
    daytime = daytime_table[count_next_daytime()]
    for quest in drop[tier]:
        text += '   <b>{}</b>: '.format(quest)
        for item in drop[tier][quest][daytime]:
            text += '{}; '.format(item)
        text += '\n\n'
    return text


def drop_table(bot, update):
    um = update.message
    if um.text[:5] == '/drop':
        try:
            tier = um.text[um.text.index(' ')+1:].lower()
            drop_tier = avalible_tiers[tier]
        except ValueError:
            drop_tier = 'Null'
        except KeyError:
            drop_tier = 'Null'
        text = qdrop(drop_tier)
        if text == 'KeyError':
            bot.sendMessage(chat_id=um.chat_id,
                            text='Использование команды:\n'
                                 '/drop <code>{T2/cloaks/T3/T4}</code>\n'
                                 'ИЛИ\n'
                                 '/d2 | /d3 | /d4 | /dc',
                            parse_mode='HTML')
        else:
            bot.sendMessage(chat_id=um.chat_id,
                            text=text,
                            parse_mode='HTML')
    if um.text == '/d2' or um.text == '/d3' or um.text or um.text == '/d4'\
            or um.text == '/dc':
        drop_tier = avalible_tiers[um.text.lower()[:3]]
        text = qdrop(drop_tier)
        bot.sendMessage(chat_id=um.chat_id,
                        text=text,
                        parse_mode='HTML')


def search_drop(item):
    search_res = [[], [], [], []]
    t = 0
    text = ""
    for tier in drop:
        for quest in drop[tier]:
            for daytime in drop[tier][quest]:
                for i in drop[tier][quest][daytime]:
                    if item.lower() in i.lower():
                        search_res[t].append("{} {} {}\n".format(daytime_to_string[daytime], quest, i))
                    else:
                        pass
        t += 1
    for tier in search_res:
        if not tier:
            pass
        else:
            for res in tier:
                text += res
        text += "\n"
    return text


# ̶
def send_search_bot(bot, update):
    um = update.message
    bot.sendChatAction(um.chat_id, "TYPING")
    search_query = um.text[um.text.index(' ')+1:]
    if len(search_query) >= 3:
        text = search_drop(search_query)
        if len(text) > 250:
            bot.sendMessage(um.chat_id,
                            "<i>Слиииишком много совпадений</i>. Попробуйте сузить область поиска.",
                            parse_mode="HTML")
        else:
            try:
                bot.sendMessage(um.chat_id,
                                text,
                                parse_mode="HTML")
            except BadRequest:
                text = '<i>Ветер завывает по окрестным лугам, замки как будто вымерли.</i>\n' \
                       'Видимо, ваш запрос так никто и не смог найти, а может, таких предметов и не существует'
                bot.sendMessage(chat_id=um.chat_id,
                                text=text,
                                parse_mode='HTML')
    else:
        bot.sendMessage(um.chat_id,
                        'Ваш запрос слишком короткий(меньше трёх символов).')
