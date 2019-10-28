"""
В этом модуле находятся функции, связанные со статусами
"""

from castle_files.work_materials.statuses_const import statuses as statuses_const, statuses_to_messages, \
    default_status_messages
from castle_files.work_materials.globals import STATUSES_MODERATION_CHAT_ID, moscow_tz

from castle_files.libs.player import Player

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest

import re
import datetime
import random

OWN_STATUS_PRICE = 5000
# PLAYER_STATUS_PRICE = 10000
OWN_STATUS_ID = 0


def status_shop(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    response = "Статусы, доступные для покупки:\n"
    player_statuses = player.tea_party_info.get("statuses") or []
    for status_id, status in list(statuses_const.items()):
        name, price = status.get("name"), status.get("price")
        if status not in player_statuses and not status.get("unique"):
            response += "<b>{}</b>: {}🔘\n/buy_status_{}\n\n".format(name, price, status_id)
    response += "\nУстановить собственный статус ({} 🔘): /set_own_status [Новый статус]\n" \
                "<em>Обратите внимание, повторная смена статуса будет вновь стоить жетоны.</em>\n" \
                "".format(OWN_STATUS_PRICE)
                # "Установить статус другому ({} 🔘): /set_player_status {} {}".format(
                # OWN_STATUS_PRICE, "{Новый статус}", PLAYER_STATUS_PRICE, "id игрока", "{Новый статус}")
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
    if player.tea_party_info.get("own_status_awaiting_moderation") is not None:
        bot.send_message(chat_id=mes.chat_id, text="У вас уже есть статус, проходящий модерацию. Дождитесь окончания.")
        return
    for status_id, status in list(statuses_const.items()):
        if new_status == status["name"]:
            bot.send_message(chat_id=mes.chat_id,
                             text="Новый статус совпадает с одним из зарезервированных. Выберите другой.")
            return
    if '🎗' in new_status:
        bot.send_message(chat_id=mes.chat_id, text="🎗 запрещена в статусе.")
        return
    player.tea_party_info.update({"requested_own_status": new_status})
    player.update()
    bot.send_message(chat_id=mes.chat_id, text="Установить собственный статус на {}? ({} 🔘)\n\n"
                                               "Обратите внимание, все статусы проходят модерацию."
                                               "".format(new_status, OWN_STATUS_PRICE),
                     reply_markup=InlineKeyboardMarkup([[
                         InlineKeyboardButton(text="✅Да", callback_data="p_own_status yes"),
                         InlineKeyboardButton(text="❌Нет", callback_data="p_own_status no")]]))


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
        player.tea_party_info.update({"own_status_awaiting_moderation": new_status})
        bot.send_message(chat_id=STATUSES_MODERATION_CHAT_ID, parse_mode='HTML',
                         text="<b>{}</b>(@{}) Хочет установить статус на <b>{}</b>.\n"
                              "Разрешить?".format(player.nickname, player.username, new_status),
                         reply_markup=InlineKeyboardMarkup([[
                             InlineKeyboardButton(text="✅Да",
                                                  callback_data="p_moderate_status_{} yes".format(player.id)),
                             InlineKeyboardButton(text="❌Нет",
                                                  callback_data="p_moderate_status_{} no".format(player.id))]]))
        player.update()
        text = "Статус отправлен на модерацию."

    else:
        text = "Изменение статуса отменено."
    player.tea_party_info.pop("requested_own_status")
    try:
        bot.editMessageText(chat_id=mes.chat_id, message_id=mes.message_id, text=text)
    except BadRequest:
        bot.send_message(chat_id=mes.chat_id, text=text)


def moderate_status(bot, update):
    mes = update.callback_query.message
    player_id = re.search("_(\\d+)", update.callback_query.data)
    if player_id is None:
        bot.answer_callback_query(callback_query_id=update.callback_query.id,
                                  text="Ошибка. Неверные данные в ответе",
                                  show_alert=True)
        return
    player_id = int(player_id.group(1))
    player = Player.get_player(player_id)
    if player is None:
        return
    yes = 'yes' in update.callback_query.data
    new_status = player.tea_party_info.get("own_status_awaiting_moderation")
    if new_status is None:
        bot.answer_callback_query(callback_query_id=update.callback_query.id,
                                  text="Не найден новый статус. Скорее всего, на запрос уже ответили",
                                  show_alert=True)
        return
    answer_text = "{} @<b>{}</b> в <code>{}</code>" \
                  "".format("Одобрено" if yes else "Отклонено", update.callback_query.from_user.username,
                            datetime.datetime.now(tz=moscow_tz).strftime("%d/%m/%y %H:%M:%S"))
    if yes:
        player.tea_party_info.update({"own_status": new_status})
        text = "Новый статус (<b>{}</b>) успешно прошёл модерацию.".format(new_status)
        # Записываю в статусы новый
        pl_statuses = player.tea_party_info.get("statuses")
        if pl_statuses is None:
            pl_statuses = []
            player.tea_party_info.update({"statuses": pl_statuses})
        if OWN_STATUS_ID not in pl_statuses:
            pl_statuses.append(OWN_STATUS_ID)
    else:
        text = "Статус (<b>{}</b>) отклонён.\nВозвращено {} 🔘 жетонов".format(new_status, OWN_STATUS_PRICE)
        player.reputation += OWN_STATUS_PRICE
    player.tea_party_info.pop("own_status_awaiting_moderation")
    player.update()
    bot.send_message(chat_id=player.id, text=text, parse_mode='HTML')
    bot.edit_message_text(chat_id=mes.chat_id, message_id=mes.message_id, text=mes.text + "\n" + answer_text,
                          parse_mode='HTML')


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
    if price is None:
        bot.send_message(chat_id=mes.chat_id, text="Этот статус невозможно купить.")
        return
    if player.reputation < price:
        bot.send_message(chat_id=mes.chat_id, text="Недостаточно 🔘")
        return
    player.reputation -= price
    player_statuses.append(status_id)
    player.update()
    bot.send_message(chat_id=mes.chat_id,
                     text="Статус <b>{}</b> успешно куплен!\nАктивируйте его! "
                          "Просмотреть доступные статусы: /statuses".format(name), parse_mode='HTML')


def statuses(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    player_statuses = player.tea_party_info.get("statuses")
    if player_statuses is None:
        bot.send_message(chat_id=mes.chat_id,
                         text="Нет купленных статусов. Статусы можно купить в магазине (Чайная лига)")
        return
    response = "Текущий статус: <b>{}</b>\n\n".format(get_status_text_by_id(player.status, player.id)) if \
        player.status is not None else ""
    response += "Доступные статусы:\n"
    for status_id in player_statuses:
        if status_id == OWN_STATUS_ID:
            name = player.tea_party_info.get("own_status")
        else:
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
    if status_id == OWN_STATUS_ID:
        player = Player.get_player(player_id, notify_on_error=False)
        if player is None:
            raise RuntimeError
        return player.tea_party_info.get("own_status")
    status = statuses_const.get(status_id)
    if status is not None:
        name = status["name"]
        if status.get("unique"):
            name += " 🎗"
        return name
    return None


def get_status_message_by_text(text: str) -> str:
    s = statuses_to_messages.get(text)
    return s if s is not None else random.choice(default_status_messages).format(text)
