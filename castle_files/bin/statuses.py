"""
В этом модуле находятся функции, связанные со статусами
"""

from castle_files.work_materials.statuses_const import statuses as statuses_const

from castle_files.libs.player import Player

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest

import re

OWN_STATUS_PRICE = 10000


def status_shop(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    response = "Статусы, доступные для покупки:\n"
    player_statuses = player.tea_party_info.get("statuses") or []
    for status_id, status in list(statuses_const.items()):
        name, price = status.get("name"), status.get("price")
        if status not in player_statuses:
            response += "<b>{}</b>: {}🔘\n/buy_status_{}\n\n".format(name, price, status_id)
    response += "\n\nУстановить собственный статус (10000 🔘): /set_own_status {Новый статус}\n" \
                "<em>Обратите внимание, повторная смена статуса будет вновь стоить жетоны.</em>"
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')


def request_set_own_status(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    try:
        new_status = mes.text.split()[1]
    except IndexError:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис.")
        return
    if player.reputation < OWN_STATUS_PRICE:
        bot.send_message(chat_id=mes.chat_id, text="Недостаточно 🔘 жетонов")
        return
    player.tea_party_info.update({"requested_own_status": new_status})
    player.update()
    bot.send_message(chat_id=mes.chat_id, text="Установить собственный статус на {}? ({} 🔘)".format(new_status,
                                                                                                    OWN_STATUS_PRICE),
                     reply_markup=InlineKeyboardMarkup([
                         InlineKeyboardButton(text="✅Да", callback_data="p_own_status yes"),
                         InlineKeyboardButton(text="❌Нет", callback_data="p_own_status no")]))


def set_own_status(bot, update):
    mes = update.callback_query.message
    player = Player.get_player(update.callback_query.from_user.id)
    if player is None:
        return
    yes = 'yes' in update.callback_query.data
    if yes:
        if player.reputation < OWN_STATUS_PRICE:
            bot.answer_callback_query(callback_query_id=update.callback_query.id, text="Недостаточно 🔘 жетонов",
                                      show_alert=True)
            return
        new_status = player.tea_party_info.get("requested_own_status")
        if new_status is None:
            bot.answer_callback_query(callback_query_id=update.callback_query.id,
                                      text="Не найден новый статус. Начните заного (/set_own_status {status})",
                                      show_alert=True)
            return
        player.reputation -= OWN_STATUS_PRICE
        player.tea_party_info.update({"own_status": new_status})
        player.update()
        text = "Статус успешно изменён."

    else:
        text = "Изменение статуса отменено."
    player.tea_party_info.pop("requested_own_status")
    try:
        bot.editMessageText(chat_id=mes.chat_id, message_id=mes.message_id, text=text)
    except BadRequest:
        bot.send_message(chat_id=mes.chat_id, text=text)



def buy_status(bot, update):
    mes = update.message
    status_id = re.search("_(\\d+)", mes.text)
    if status_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Статус не найден")
        return
    status_id = int(status_id.group(1))
    player = Player.get_player(mes.from_user.id)
    player_statuses = player.tea_party_info.get("statuses")
    if player_statuses is None:
        player_statuses = []
        player.tea_party_info.update({"statuses": player_statuses})
    if status_id in player_statuses:
        bot.send_message(chat_id=mes.chat_id, text="Статус уже куплен")
        return
    status = statuses_const.get(status_id)
    price, name = status.get("price"), status.get("name")
    if player.reputation < price:
        bot.send_message(chat_id=mes.chat_id, text="Недостаточно 🔘")
        return
    player.reputation -= price
    player_statuses.append(status_id)
    player.update()
    bot.send_message(chat_id=mes.chat_id, text="Статус <b>{}</b> успешно куплен!".format(name), parse_mode='HTML')


def statuses(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    player_statuses = player.tea_party_info.get("statuses")
    if player_statuses is None:
        bot.send_message(chat_id=mes.chat_id,
                         text="Нет купленных статусов. Статусы можно купить в магазине (Чайная лига)")
        return
    response = "Текущий статус: <b>{}</b>\n\n".format(get_status_text_by_id(player.status)) if \
        player.status is not None else ""
    response += "Доступные статусы:\n"
    for status_id in player_statuses:
        status = statuses_const.get(status_id)
        name = status.get("name")
        response += "<b>{}</b>\n/status_on_{}\n\n".format(name, status_id)
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')


def status_on(bot, update):
    mes = update.message
    status_id = re.search("_(\\d+)", mes.text)
    if status_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис")
        return
    status_id = int(status_id.group(1))
    player = Player.get_player(mes.from_user.id)
    player_statuses = player.tea_party_info.get("statuses")
    if player_statuses is None or status_id not in player_statuses:
        bot.send_message(chat_id=mes.chat_id, text="Статус не найден. Он куплен?")
        return
    if player.status is not None:
        if player.status not in player_statuses:
            player_statuses.append(player.status)
    player.status = status_id
    player.update()
    bot.send_message(chat_id=mes.chat_id, text="Статус успешно изменён!")


def get_status_text_by_id(status_id: int, player_id=None) -> str:
    status = statuses_const.get(status_id)
    if status is not None:
        return status["name"]
    return None
