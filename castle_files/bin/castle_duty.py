"""
В этом модуле находятся функции, относящиеся к вахте стражников
"""
from telegram.error import TelegramError
from castle_files.work_materials.globals import SENTINELS_DUTY_CHAT_ID, CASTLE_BOT_ID, dispatcher, SUPER_ADMIN_ID

from castle_files.bin.service_functions import check_access
from castle_files.bin.buttons import get_general_buttons
from castle_files.bin.quest_triggers import on_duty_request

from castle_files.libs.castle.location import Location
from castle_files.libs.player import Player

import logging
import traceback
import threading
import re


def revoke_duty_link(bot, update):
    """
    Функция перевыпуска ссылки в чат стражи
    """
    gates = Location.get_location(3)
    try:
        invite_link = bot.exportChatInviteLink(SENTINELS_DUTY_CHAT_ID)
        if invite_link is not None:
            invite_link = invite_link[22:]  # Обрезаю https://t.me/joinchat/
            gates.special_info.update({"invite_link": invite_link})
            gates.update_location_to_database()
            bot.send_message(chat_id=update.message.chat_id, text="Ссылка на чат вахты сброшена")
    except TelegramError:
        logging.error(traceback.format_exc())
        bot.send_message(chat_id=update.message.chat_id, text="Произошла ошибка.")


def ask_to_revoke_duty_link():
    """
    При запуске бота предлагает проверить ссылку в чат стражи и перевыпустить её при необходимости
    """
    gates = Location.get_location(3)
    invite_link = gates.special_info.get("invite_link")

    dispatcher.bot.send_message(chat_id=SUPER_ADMIN_ID,
                                text="<a href=\"{}\">Проверить ссылку</a>\n Сбросить ссылку: "
                                     "/revoke_duty_link".format("https://t.me/joinchat/" +
                                                                invite_link if invite_link is not None else ""),
                                parse_mode='HTML')


def begin_duty(bot, update, user_data):
    """
    Функция начала вахты для игрока (стражника)
    """
    mes = update.message
    player_id = mes.from_user.id
    player = Player.get_player(player_id)
    if player.game_class != 'Sentinel':
        bot.send_message(chat_id=mes.chat_id, text="Только стражники могут вставать на вахту!")
        return
    gates = Location.get_location(3)
    invite_link = gates.special_info.get("invite_link")
    if invite_link is None:
        try:
            invite_link = bot.exportChatInviteLink(SENTINELS_DUTY_CHAT_ID)
            if invite_link is not None:
                invite_link = invite_link[22:]  # Обрезаю https://t.me/joinchat/
                gates.special_info.update({"invite_link": invite_link})
                gates.update_location_to_database()
        except TelegramError:
            logging.error(traceback.format_exc())
    players_on_duty = gates.special_info.get("players_on_duty")
    if player_id in players_on_duty:
        bot.send_message(chat_id=mes.chat_id, text="Вы уже на вахте!")
    else:
        players_on_duty.append(player_id)
    gates.update_location_to_database()
    try:
        bot.unbanChatMember(chat_id=SENTINELS_DUTY_CHAT_ID, user_id=player_id)
    except TelegramError:
        logging.error(traceback.format_exc())
    user_data.update({"on_duty": True})
    reply_markup = get_general_buttons(user_data)
    bot.send_message(chat_id=mes.from_user.id, text="Вы заступили на вахту. <a href=\"{}\">Вступайте в чат!</a>"
                                                    "".format("https://t.me/joinchat/" + invite_link),
                     parse_mode='HTML', reply_markup=reply_markup)


def end_duty(bot, update, user_data):
    """
    Функция выхода со стражи (раньше кикала игрока из чата)
    """
    mes = update.message
    player_id = mes.from_user.id
    player = Player.get_player(player_id)
    gates = Location.get_location(3)
    players_on_duty = gates.special_info.get("players_on_duty")
    if player_id in players_on_duty:
        players_on_duty.remove(player_id)
        gates.update_location_to_database()
    if "on_duty" in user_data:
        user_data.pop("on_duty")
    reply_markup = get_general_buttons(user_data, player=player)
    try:
        pass
        # bot.kickChatMember(chat_id=SENTINELS_DUTY_CHAT_ID, user_id=player_id)
    except TelegramError:
        logging.error(traceback.format_exc())
    bot.send_message(chat_id=mes.from_user.id, text="Вы успешно покинули вахту. Спасибо за службу!",
                     reply_markup=reply_markup)


def request_duty_feedback(bot, update, user_data):
    """
    Функция запроса отправки сообщения стражникам
    """
    user_data.update({"status": "duty_feedback"})
    bot.send_message(chat_id=update.message.chat_id, text="Следующее сообщение будет отправлено стражникам на вахте!",
                     reply_markup=get_general_buttons(user_data))


def send_duty_feedback(bot, update, user_data):
    """
    Функция  отправки сообщения стражникам
    """
    threading.Thread(target=forward_then_reply_to_duty, args=(bot, update.message)).start()
    user_data.update({"status": "castle_gates"})
    reply_markup = get_general_buttons(user_data, player=Player.get_player(update.message.from_user.id))
    bot.send_message(chat_id=update.message.from_user.id,
                     text="Вы обратились к стражникам у городских ворот. Ожидайте ответа.", reply_markup=reply_markup)

    player = Player.get_player(update.message.from_user.id)
    on_duty_request(player)


def forward_then_reply_to_duty(bot, message):
    """
    Функция, которая отправляет сообщение в чат стражи (запускается в отдельном потоке... зачем??)
    """
    mes = bot.forwardMessage(chat_id=SENTINELS_DUTY_CHAT_ID, from_chat_id=message.chat_id, message_id=message.message_id)
    bot.send_message(chat_id=SENTINELS_DUTY_CHAT_ID,
                     text="Запрос к стражнику от @{} #r{}\nЗаблокировать пользователя: "
                          "/restrict_feedback_{}".format(message.from_user.username, message.from_user.id,
                                                         message.from_user.id),
                     reply_to_message_id=mes.message_id)


def send_reply_to_duty_request(bot, update):
    """
    Функция для ответа стражников на запрос к ним (в чате стражи)
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


def check_ban_in_duty_chat(bot, update):
    """
    Функция, которая проверяет, можно ли игроку зайти (и писать) в чат стражи
    """
    gates = Location.get_location(3)
    players_on_duty = gates.special_info.get("players_on_duty")
    user_id = update.message.from_user.id
    player = Player.get_player(user_id)
    if player is not None and player.game_class == 'Sentinel':
        # Временно разрешено находиться в чате всем стражам
        return
    if user_id not in players_on_duty and not check_access(user_id) and user_id != CASTLE_BOT_ID:
        bot.kickChatMember(chat_id=SENTINELS_DUTY_CHAT_ID, user_id=update.message.from_user.id)
        bot.send_message(chat_id=SENTINELS_DUTY_CHAT_ID, text="Только стражам на службе разрешён вход в этот чат")
