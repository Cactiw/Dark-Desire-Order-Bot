"""
В этом модуле находятся функции, связанные с "игровым" замком - виртуальным замком Скалы в боте
"""
from castle_files.bin.buttons import send_general_buttons
from castle_files.work_materials.globals import cursor, moscow_tz, king_id

import datetime
import re


def back(bot, update, user_data):
    statuses_back = {
        "barracks": "central_square",
        "central_square": "default",
        "throne_room": "central_square"
    }
    status = user_data.get("status")
    if status is None:
        send_general_buttons(update.message.from_user.id, user_data, bot=bot)
    new_status = statuses_back.get(status)
    user_data.update({"status": new_status})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def guide_signs(bot, update):
    bot.send_message(chat_id=update.message.from_user.id,
                     text="Указатели гласят:\n")


def welcome(bot, update, user_data):
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def central_square(bot, update, user_data):
    user_data.update({"status": "central_square", "location_id": 0})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def barracks(bot, update, user_data):
    user_data.update({"status": "barracks", "location_id": 1})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def throne_room(bot, update, user_data):
    user_data.update({"status": "throne_room", "location_id": 2})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


# Запрос на аудиенцию у Короля (возможно, когда-нибудь уберу прямые запросы в базу данных)
def request_king_audience(bot, update):
    request = "insert into king_audiences(request_player_id, king_player_id, date_created) " \
              "values (%s, %s, %s) returning audience_id"
    cursor.execute(request, (update.message.from_user.id, king_id,
                             datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)))
    row = cursor.fetchone()
    bot.send_message(chat_id=king_id,
                     text="@{} просит аудиенции! \nПринять: /accept_king_audience_{}\nОтказать: "
                          "/decline_king_audience_{}".format(update.message.from_user.username, row[0], row[0]))
    bot.send_message(chat_id=update.message.from_user.id, text="Запрос о аудиенции отправлен. Ожидайте ответа")


# Функция, которая возвращает [ id запросившего аудиенцию : id аудиенции ], или [-1], если произошла ошибка
def get_king_audience(bot, update):
    mes = update.message
    audience_id = re.search("_(\\d+)", mes.text)
    if audience_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис.")
        return [-1]
    audience_id = int(audience_id.group(1))
    request = "select request_player_id from king_audiences where audience_id = %s and accepted is null"
    cursor.execute(request, (audience_id,))
    row = cursor.fetchone()
    if row is None:
        bot.send_message(chat_id=mes.chat_id,
                         text="Невозможно найти заявку. Проверьте id. Возможно, вы уже рассмотрели её")
        return [-1]
    return [row[0], audience_id]


def accept_king_audience(bot, update):
    return_value = get_king_audience(bot, update)
    if return_value[0] == -1:
        return
    request = "update king_audiences set accepted = true where audience_id = %s"
    cursor.execute(request, (return_value[1],))
    bot.send_message(chat_id=update.message.chat_id, text="Этот холоп достоин внимания! "
                                                          "Проследуйте в свой кабинет (личку) для продолжения общения.")
    bot.send_message(chat_id=return_value[0], text="Ваше прошение аудиенции у Короля удовлетворено. "
                                                   "Ожидайте, Король выйдет к вам.")


def decline_king_audience(bot, update):
    return_value = get_king_audience(bot, update)
    if return_value[0] == -1:
        return
    request = "update king_audiences set accepted = false where audience_id = %s"
    cursor.execute(request, (return_value[1],))
    bot.send_message(chat_id=update.message.chat_id, text="<em>Пошёл в̶ ̶т̶о̶р̶т̶у̶ж̶к̶у̶! отсюда!</em> - "
                                                          "раздаётся за дверью. Вы сладко потягиваетесь в кресле. "
                                                          "\"Нет человека - нет проблемы\", проносится у вас в голове.",
                     parse_mode='HTML')
    bot.send_message(chat_id=return_value[0], text="Ваше прошение аудиенции у Короля было отклонено. "
                                                   "Возможно, король занят, или ваш вид вызывает у него отвращение.")
