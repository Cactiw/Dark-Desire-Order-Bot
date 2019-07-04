"""
Функции, связанные с голосованиями
"""
from castle_files.work_materials.globals import cursor, moscow_tz, SUPER_ADMIN_ID, classes_list

from castle_files.bin.buttons import get_vote_buttons
from castle_files.bin.service_functions import check_access

from castle_files.libs.player import Player
from castle_files.libs.vote import Vote

from telegram.error import TelegramError, BadRequest

import datetime
import logging
import traceback
import json
import re


def create_vote(bot, update, user_data):
    mes = update.message
    if not check_access(mes.from_user.id):
        return
    vote_name = mes.text.partition(" ")[2]
    if vote_name is None or len(vote_name) <= 1:
        bot.send_message(chat_id=mes.chat_id, text="Необходимо задать имя голосования в аргументах.")
        return
    user_data.update({"status": "creating_vote_text", "vote_name": vote_name, "vote_variants": [], "vote_text": ""})
    bot.send_message(chat_id=mes.chat_id, text="Голосование создаётся. Введите текст голосования.")


def add_vote_text(bot, update, user_data):
    mes = update.message
    if not check_access(mes.from_user.id):
        return
    user_data.update({"status": "creating_vote_variants", "vote_text": mes.text})
    bot.send_message(chat_id=mes.chat_id, text="Текст голосования принят. Введите варианты ответа.")


def add_vote_variant(bot, update, user_data):
    mes = update.message
    if not check_access(mes.from_user.id):
        return
    variants = user_data.get("vote_variants")
    if variants is None:
        variants = []
        user_data.update({"vote_variants": variants})
    variants.append(mes.text)
    bot.send_message(chat_id=mes.chat_id, text="Вариант добавлен. Введите ещё один, или нажмите /finish_vote")


def finish_vote(bot, update, user_data):
    mes = update.message
    if not check_access(mes.from_user.id):
        return
    name, variants, text = user_data.get("vote_name"), user_data.get("vote_variants"), user_data.get("vote_text")
    if not all([name, variants, text]):
        bot.send_message(chat_id=mes.chat_id, text="Все этапы должны быть заполнены перед запуском голосования")
    choices = {}
    for i in range(len(variants)):
        choices.update({i: []})
    choices = json.dumps(choices)
    request = "insert into votes(name, text, variants, choices) VALUES (%s, %s, %s, %s) returning id"
    cursor.execute(request, (name, text, variants, choices))
    row = cursor.fetchone()
    if row is None:
        bot.send_message(chat_id=mes.chat_id, text="Произошла ошибка. Возможно, голосование всё же создалось, "
                                                   "проверьте: /vote")
        return
    bot.send_message(chat_id=mes.chat_id, text="Голосование <b>{}</b> успешно создано.\n"
                                               "Просмотреть голосование: /view_vote_{}".format(name, row[0]),
                     parse_mode='HTML')
    user_data.pop("vote_name")
    user_data.pop("vote_variants")
    user_data.pop("vote_text")
    user_data.pop("status")


def view_vote(bot, update):
    mes = update.message
    if not check_access(mes.from_user.id):
        return
    vote_id = re.search("_(\\d+)", mes.text)
    if vote_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис.")
        return
    vote_id = int(vote_id.group(1))
    request = "select name, text, variants, started, duration, classes from votes where id = %s"
    cursor.execute(request, (vote_id,))
    row = cursor.fetchone()
    if row is None:
        bot.send_message(chat_id=mes.chat_id, text="Голосование не найдено.")
        return
    response = "Голосование <b>{}</b>\n".format(row[0])
    response += row[1] + "\n\n"
    response += "Начало: <code>{}</code>\n".format(row[3].strftime("%d/%m/%y %H:%M:%S") if row[3] is not None else
                                                  "Не началось.")
    response += "Длительность: <code>{}</code>\n".format(row[4] if row[4] is not None else
                                                        "Не задано.")
    cl_text = ""
    if all(row[5]) or not row[5]:
        cl_text = "ВСЕ"
    else:
        for i, b in enumerate(row[5]):
            cl_text += classes_list[i] if b else ""
    response += "Классы: <code>{}</code>\n".format(cl_text)
    if row[3] is None:
        response += "Изменить длительность: /change_vote_duration_{}\n".format(vote_id)
        response += "Начать голосование: /start_vote_{}\n".format(vote_id)
        response += "\nИзменить классы для голосований: /set_vote_classes_{} [Классы, которые ПРИНИМАЮТ участие " \
                    "в голосовании]\n\n<em>Классы ТОЛЬКО как в списке: {}</em>".format(vote_id, classes_list)
    print(response)
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')


def set_vote_classes(bot, update):
    mes = update.message
    if not check_access(mes.from_user.id):
        return
    vote_id = re.search("_(\\d+)", mes.text)
    if vote_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис.")
        return
    vote_id = int(vote_id.group(1))
    vote = Vote.get_vote(vote_id)
    if vote is None:
        bot.send_message(chat_id=mes.chat_id, text="Голосование не найдено.")
        return
    vote.classes = []
    for i in classes_list:
        vote.classes.append(False)
    try:
        classes = list(mes.text.split()[1:])
    except IndexError:
        for i in range(len(vote.classes)):
            vote.classes[i] = True
        bot.send_message(chat_id=mes.chat_id, text="Голосование <b>{}</b> разрешено для всех классов".format(vote.name),
                         parse_mode='HTML')
        return
    for cl in classes:
        try:
            print(cl, classes_list.index(cl))
            vote.classes[classes_list.index(cl)] = True
        except ValueError:
            continue
    print(vote.classes)
    vote.update()
    bot.send_message(chat_id=mes.chat_id, text="Классы голосования <b>{}</b> обновлены.".format(vote.name),
                     parse_mode='HTML')


def request_change_vote_duration(bot, update, user_data):
    mes = update.message
    if not check_access(mes.from_user.id):
        return
    vote_id = re.search("_(\\d+)", mes.text)
    if vote_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис.")
        return
    vote_id = int(vote_id.group(1))
    vote = Vote.get_vote(vote_id)
    if vote is None:
        bot.send_message(chat_id=mes.chat_id, text="Голосование не найдено.")
        return
    user_data.update({"status": "editing_vote_duration", "vote_id": vote_id})
    bot.send_message(chat_id=mes.chat_id, text="Изменение длительности <b>{}</b>\nДайте ответ в виде %HH %MM %SS"
                                               "".format(vote.name), parse_mode='HTML')


def change_vote_duration(bot, update, user_data):
    mes = update.message
    if not check_access(mes.from_user.id):
        return
    vote_id = user_data.get("vote_id")
    if vote_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Произошла ошибка. Начните сначала.")
        return
    vote = Vote.get_vote(vote_id)
    if vote is None:
        bot.send_message(chat_id=mes.chat_id, text="Голосование не найдено.")
        return
    parse = mes.text.split()
    hours = int(parse[0])
    minutes = int(parse[1]) if len(parse) > 1 else 0
    seconds = int(parse[2]) if len(parse) > 2 else 0
    vote.duration = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
    vote.update()
    user_data.pop("status")
    user_data.pop("vote_id")
    bot.send_message(chat_id=mes.chat_id, text="Длительность <b>{}</b> успешно изменена!".format(vote.name),
                     parse_mode='HTML')


def start_vote(bot, update):
    mes = update.message
    if not check_access(mes.from_user.id):
        return
    vote_id = re.search("_(\\d+)", mes.text)
    if vote_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис.")
        return
    vote_id = int(vote_id.group(1))
    vote = Vote.get_vote(vote_id)
    if vote is None:
        bot.send_message(chat_id=mes.chat_id, text="Голосование не найдено.")
        return
    if len(vote.variants) <= 0:
        bot.send_message(chat_id=mes.chat_id, text="Необходимо задать хотя бы один ответ.")
        return
    if vote.duration is None:
        bot.send_message(chat_id=mes.chat_id, text="Необходимо задать длительность голосования.")
        return
    if vote.started is not None:
        bot.send_message(chat_id=mes.chat_id, text="Голосование уже началось!")
        return
    vote.started = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)
    vote.update()
    bot.send_message(chat_id=mes.chat_id, text="Голосование <b>{}</b> началось!".format(vote.name), parse_mode='HTML')


def votes(bot, update):
    mes = update.message
    response = "Доступные голосования в замке:\n\n"
    request = "select id, name, text, classes from votes where started is not null and started + duration > now() " \
              "AT TIME ZONE 'Europe/Moscow'"
    cursor.execute(request)
    row = cursor.fetchone()
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    while row is not None:
        try:
            if row[3] is not None and row[3] and (player.game_class is None or
                                                  row[3][classes_list.index(player.game_class)] is False):
                row = cursor.fetchone()
                continue
        except Exception:
            logging.error(traceback.format_exc())
        response += "<b>{}</b>\n{}\n<code>Принять участие в голосовании:</code> /vote_{}" \
                    "\n\n".format(row[1], row[2], row[0])
        row = cursor.fetchone()
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')


def get_vote_text(vote, choice=None):
    response = "<b>{}</b>:\n{}\n\n".format(vote.name, vote.text)
    if vote.classes is not None and vote.classes and not all(vote.classes):
        cl_text = ""
        for i, b in enumerate(vote.classes):
            cl_text += classes_list[b] if b else ""
        response += "Классы: <code>{}</code>\n\n".format(cl_text)
    response += "Доступные варианты:\n\n"
    for variant in vote.variants:
        response += variant + "\n\n"
    response += "Ваш выбор: {}\n".format(vote.variants[choice] if choice is not None else "Не сделан")
    return response


def vote(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    if player.castle != '🖤':
        bot.send_message(chat_id=mes.chat_id, text="Голосование доступно только жителям 🖤Скалы!")
        return
    if player.guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Голосование доступно только членам гильдий.")
        return
    vote_id = re.search("_(\\d+)", mes.text)
    if vote_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис.")
        return
    vote_id = int(vote_id.group(1))
    vote = Vote.get_vote(vote_id)
    if vote is None:
        bot.send_message(chat_id=mes.chat_id, text="Голосование не найдено.")
        return
    try:
        if vote.classes is not None and vote.classes and (player.game_class is None or
                                                          vote.classes[classes_list.index(player.game_class)] is False):
            bot.send_message(chat_id=mes.chat_id, text="Голосование недоступно для вашего класса.\n\n<em>В случае, "
                                                       "если ваш класс указан неверно, его можно обновить, "
                                                       "прислав форвард ответа </em>@ChatWarsBot<em> на </em>/me",
                             parse_mode='HTML')
            bot.answerCallbackQuery(callback_query_id=update.callback_query.id)
            return
    except Exception:
        logging.error(traceback.format_exc())
    choice = None
    for i, ch in enumerate(vote.choices):
        if player.id in ch:
            choice = i
            break
    response = get_vote_text(vote, choice)
    buttons = get_vote_buttons(vote, choice)
    bot.send_message(chat_id=mes.chat_id, text=response, reply_markup=buttons, parse_mode='HTML')


def set_vote_variant(bot, update):
    data = update.callback_query.data
    mes = update.callback_query.message
    player = Player.get_player(update.callback_query.from_user.id)
    if player is None:
        return
    if player.castle != '🖤':
        bot.send_message(chat_id=mes.chat_id, text="Голосование доступно только жителям 🖤Скалы!")
        return
    if player.guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Голосование доступно только членам гильдий.")
        return
    parse = re.search("_(\\d+)_(\\d+)", data)
    if parse is None:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис.")
        return
    vote_id = int(parse.group(1))
    variant = int(parse.group(2))
    vote = Vote.get_vote(vote_id)
    if vote is None:
        bot.send_message(chat_id=mes.chat_id, text="Голосование не найдено.")
        return
    try:
        if vote.classes is not None and vote.classes and (player.game_class is None or
                                        vote.classes[classes_list.index(player.game_class)] is False):
            bot.send_message(chat_id=mes.chat_id, text="Голосование недоступно для вашего класса.\n\n<em>В случае, "
                                                       "если ваш класс указан неверно, его можно обновить, "
                                                       "прислав форвард ответа </em>@ChatWarsBot<em> на </em>/me",
                             parse_mode='HTML')
            bot.answerCallbackQuery(callback_query_id=update.callback_query.id)
            return
    except Exception:
        logging.error(traceback.format_exc())
    if vote.started + vote.duration < datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None):
        bot.send_message(chat_id=mes.chat_id, text="Голосование уже завершено.")
        return
    for ch in vote.choices:
        if player.id in ch:
            ch.remove(player.id)
    vote.choices[variant].append(player.id)
    vote.update()
    choice = None
    for i, ch in enumerate(vote.choices):
        if player.id in ch:
            choice = i
            break
    response = get_vote_text(vote, choice=choice)
    buttons = get_vote_buttons(vote, choice=choice)
    try:
        bot.editMessageText(chat_id=mes.chat_id, message_id=mes.message_id, text=response,
                            reply_markup=buttons, parse_mode='HTML')
    # except Exception:
        # logging.error(traceback.format_exc())
    except BadRequest:
        pass
    except TelegramError:
        pass
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id)


def vote_results(bot, update):
    mes = update.message
    if mes.from_user.id != SUPER_ADMIN_ID:
        return
    vote_id = re.search("_(\\d+)", mes.text)
    if vote_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис.")
        return
    vote_id = int(vote_id.group(1))
    vote = Vote.get_vote(vote_id)
    if vote is None:
        bot.send_message(chat_id=mes.chat_id, text="Голосование не найдено.")
        return
    results = {}
    total_voices = 0
    for i, ch in enumerate(vote.choices):
        variant_count = 0
        for player_id in ch:
            if player_id != 0:
                variant_count += 1
        results.update({vote.variants[i]: variant_count})
        total_voices += variant_count
    results = sorted(list(results.items()), key=lambda x: x[1], reverse=True)
    response = "Результаты <b>{}</b>:\n".format(vote.name)
    for res in results:
        response += "{} —— <code>{}</code> (<code>{:.0f}%</code>)\n".format(res[0], res[1], res[1]/total_voices*100)
    response += "\n<em>Всего голосов:</em> <b>{}</b>".format(total_voices)
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
