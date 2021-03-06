"""
В этом модуле находятся все функции для фидбека в виртуальном замке, например, аудиенция у короля, обращение в мид
"""
from castle_files.work_materials.globals import cursor, king_id, moscow_tz, MID_CHAT_ID, SENTINELS_DUTY_CHAT_ID, \
    DEFAULT_CASTLE_STATUS
from castle_files.bin.buttons import get_general_buttons
from castle_files.bin.castle import back
from castle_files.bin.quest_triggers import on_king_audience, on_mid_request

from castle_files.libs.castle.location import Location
from castle_files.libs.player import Player

from bin.service_functions import count_next_battle_time

import datetime
import re
import threading

# Запрещено отправлять сообщение миду за N минут до битвы и в течении N минут после битвы
MID_REQUEST_FORBID_MINUTES = 15


# Запрос на аудиенцию у Короля (возможно, когда-нибудь уберу прямые запросы в базу данных)
def request_king_audience(bot, update, user_data):
    if update.message.from_user.id == king_id:
        bot.send_message(chat_id=update.message.from_user.id, text="Это уже похоже на онанизм. Впрочем, навряд ли Вам "
                                                                   "нужно разрешение, чтобы говорить с самим собой.")
        return
    last_audience = user_data.get("last_king_audience")
    if last_audience is not None and datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None) - last_audience < \
            datetime.timedelta(hours=8):
        bot.send_message(chat_id=update.message.from_user.id,
                         text="\"Аудиенцию можно просить не чаще одного раза в 8 часов\", — сообщил дворецкий")
        return
    request = "insert into king_audiences(request_player_id, king_player_id, date_created) " \
              "values (%s, %s, %s) returning audience_id"
    cursor.execute(request, (update.message.from_user.id, king_id,
                             datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)))
    row = cursor.fetchone()
    user_data.update({"last_king_audience": datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)})
    bot.send_message(chat_id=king_id,
                     text="@{} просит аудиенции! \nПринять: /accept_king_audience_{}\nОтказать: "
                          "/decline_king_audience_{}".format(update.message.from_user.username, row[0], row[0]))
    bot.send_message(chat_id=update.message.from_user.id, text="Запрос об аудиенции отправлен. Ожидайте ответа")

    player = Player.get_player(update.message.from_user.id)
    on_king_audience(player)


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
    """
    Принять Аудиенцию
    """
    return_value = get_king_audience(bot, update)
    if return_value[0] == -1:
        return
    request = "update king_audiences set accepted = true, date_accepted = %s where audience_id = %s"
    cursor.execute(request, (datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None), return_value[1]))
    bot.send_message(chat_id=update.message.chat_id, text="Этот холоп достоин внимания! "
                                                          "Проследуйте в свой кабинет (личку) для продолжения общения.")
    bot.send_message(chat_id=return_value[0], text="Ваше прошение аудиенции у Короля удовлетворено. "
                                                   "Ожидайте, Король выйдет к Вам.")


def decline_king_audience(bot, update):
    """
    Отказать в аудиенции
    """
    return_value = get_king_audience(bot, update)
    if return_value[0] == -1:
        return
    request = "update king_audiences set accepted = false, date_accepted = %s where audience_id = %s"
    cursor.execute(request, (datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None), return_value[1]))
    bot.send_message(chat_id=update.message.chat_id, text="<em>Пошёл в̶ ̶т̶о̶р̶т̶у̶ж̶к̶у̶! отсюда!</em> - "
                                                          "раздаётся за дверью. Вы сладко потягиваетесь в кресле. "
                                                          "\"Нет человека - нет проблемы\", проносится у вас в голове.",
                     parse_mode='HTML')
    bot.send_message(chat_id=return_value[0], text="Ваше прошение аудиенции у Короля было отклонено. "
                                                   "Возможно, король занят, или Ваш вид вызывает у него отвращение.")


def check_mid_feedback_time_access(bot, update):
    """
    Функция проверки возможности писать в чат МИДа (запрещено в промежуток +- 15 минут от битвы)
    """
    remaining_before_battle_time = count_next_battle_time() - datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)
    battle_interval = datetime.timedelta(hours=8)
    forbid_interval = datetime.timedelta(minutes=MID_REQUEST_FORBID_MINUTES)

    if remaining_before_battle_time <= forbid_interval or \
            remaining_before_battle_time >= battle_interval - forbid_interval:
        bot.send_message(chat_id=update.message.chat_id, text="Совет отбыл на войну. Ожидайте его возращения.")
        return False
    return True


def request_mid_feedback(bot, update, user_data):
    """
    Функция запроса обращения в МИД
    """
    mes = update.message
    if not check_mid_feedback_time_access(bot, update):
        return
    loc = Location.get_location(2)
    banned_users = loc.special_info.get("banned_in_feedback")
    if mes.from_user.id in banned_users:
        bot.send_message(chat_id=mes.chat_id, text="Вам запретили общаться здесь!", reply_to_message_id=mes.message_id)
        return
    user_data.update({"status": "mid_feedback"})
    bot.send_message(chat_id=update.message.chat_id, text="Следующее сообщение будет отправлено в чат мида.",
                     reply_markup=get_general_buttons(user_data))


def send_mid_feedback(bot, update, user_data):
    """
    Функция отправки обращения в МИД
    """
    if not check_mid_feedback_time_access(bot, update):
        return
    threading.Thread(target=forward_then_reply_to_mid, args=(bot, update.message)).start()
    user_data.update({"status": "throne_room"})
    rp_off = user_data.get("rp_off")
    if rp_off:
        user_data.update({"status": DEFAULT_CASTLE_STATUS})
    reply_markup = get_general_buttons(user_data)
    bot.send_message(chat_id=update.message.from_user.id,
                     text="Ваше обращение к Совету было озвучено. Если оно было по делу, то ожидайте ответа, "
                          "но бойтесь его кары, если это не так!", reply_markup=reply_markup)

    player = Player.get_player(player_id=update.message.from_user.id)
    on_mid_request(player)


def forward_then_reply_to_mid(bot, message):
    """
    Отправка сообщения в чат МИДа
    Сначала отправляется сообщение форвардом, потом ответом на него сервисное сообщение
    """
    mes = bot.forwardMessage(chat_id=MID_CHAT_ID, from_chat_id=message.chat_id, message_id=message.message_id)
    bot.send_message(chat_id=MID_CHAT_ID,
                     text="Запрос к МИДу от @{} #r{}\nЗаблокировать пользователя: "
                          "/restrict_feedback_{}".format(message.from_user.username,
                                                         message.from_user.id, message.from_user.id),
                     reply_to_message_id=mes.message_id)


def send_reply_to_mid_request(bot, update):
    """
    Функция ответа на обращение в МИД
    """
    mes = update.message.reply_to_message
    if mes.forward_from is None:
        chat_id = re.search("#r(\\d+)", mes.text)
        if chat_id is None:
            bot.send_message(chat_id=update.message.chat_id, text="Ошибка.",
                             reply_to_message_id=update.message.message_id)
            return
        chat_id = int(chat_id.group(1))
    else:
        chat_id = update.message.reply_to_message.forward_from.id
    bot.forwardMessage(chat_id=chat_id, from_chat_id=update.message.chat_id,
                       message_id=update.message.message_id)
    bot.send_message(chat_id=update.message.chat_id, text="Ответ успешно отправлен",
                     reply_to_message_id=update.message.message_id)


def restrict_feedback(bot, update):
    """
    Функция ограничения возможности обращения в МИД
    """
    mes = update.message
    user_id = re.search("_(\\d+)", mes.text)
    if user_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис", reply_to_message_id=mes.message_id)
        return
    user_id = int(user_id.group(1))
    location_id = None
    if mes.chat_id == MID_CHAT_ID:
        location_id = 2
    elif mes.chat_id == SENTINELS_DUTY_CHAT_ID:
        location_id = 3
    if location_id is None:
        return
    loc = Location.get_location(location_id)
    banned_users = loc.special_info.get("banned_in_feedback")
    if user_id in banned_users:
        bot.send_message(chat_id=mes.chat_id, text="Этот человек уже забанен", reply_to_message_id=mes.message_id)
        return
    banned_users.append(user_id)
    loc.update_location_to_database()
    bot.send_message(chat_id=mes.chat_id,
                     text="Пользователь успешно заблокирован.\nСнять блокировку: "
                          "/unrestrict_feedback_{}".format(user_id), reply_to_message_id=mes.message_id)
    bot.send_message(chat_id=user_id, text="Вам запретили общаться в {}".format(loc.name))


def unrestrict_feedback(bot, update):
    """
    Функция снятия ограничений с игрока по обращению в МИД
    """
    mes = update.message
    user_id = re.search("_(\\d+)", mes.text)
    if user_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис", reply_to_message_id=mes.message_id)
        return
    user_id = int(user_id.group(1))
    location_id = None
    if mes.chat_id == MID_CHAT_ID:
        location_id = 2
    elif mes.chat_id == SENTINELS_DUTY_CHAT_ID:
        location_id = 3
    if location_id is None:
        return
    loc = Location.get_location(location_id)
    banned_users = loc.special_info.get("banned_in_feedback")
    if user_id not in banned_users:
        bot.send_message(chat_id=mes.chat_id, text="Этот человек не забанен!", reply_to_message_id=mes.message_id)
        return
    banned_users.remove(user_id)
    loc.update_location_to_database()
    bot.send_message(chat_id=mes.chat_id,
                     text="Пользователь успешно разблокирован", reply_to_message_id=mes.message_id)
    bot.send_message(chat_id=user_id, text="Вам снова разрешено общаться в {}".format(loc.name))
