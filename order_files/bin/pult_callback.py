import traceback
from telegram.error import (TelegramError, BadRequest)

from order_files.work_materials.pult_constants import *
from order_files.libs.pult import rebuild_pult, Pult
from order_files.libs.deferred_order import DeferredOrder
from order_files.bin.order import send_order, send_order_job, count_next_battle_time
from order_files.work_materials.pult_constants import divisions as divisions_const, potions as potions_consts, \
    tactics_order_to_emoji

from order_files.work_materials.globals import cursor, deferred_orders, moscow_tz, local_tz, job, bot, \
    MAX_MESSAGE_LENGTH, LOGS_CHAT_ID

from castle_files.bin.service_functions import check_access
from castle_files.bin.castle import fill_mid_players

import order_files.work_materials.globals as globals

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import logging
import re
import time


# Вызов нового пульта
def pult(bot, update):
    mes = update.message
    pult = Pult.get_pult(0, 0)  # Пульт - болванка
    response = ""
    message = None
    send_time = None
    variant = None
    if 'pult' in mes.text:
        # Обычный пульт
        response += Pult.get_text()
        PultMarkup = rebuild_pult("default", pult, None)
        message = bot.sync_send_message(
            chat_id=update.message.chat_id, text=response + "\n\n{0}".format(
                datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None).strftime("%d/%m/%y %H:%M:%S")),
            reply_markup=PultMarkup)
    elif 'order' in mes.text:
        # Вызывается пульт для установки отложки
        PultMarkup = rebuild_pult("default_deferred", pult, None)
        line = re.search("order (\\d+)-?(\\d*)-?(\\d*)", mes.text)
        if line is None:
            bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис")
            return
        hours = int(line.group(1))
        minutes = int(line.group(2)) if line.group(2) != '' else 0
        seconds = int(line.group(3)) if line.group(3) != '' else 0
        time_to_send = datetime.time(hour=hours, minute=minutes, second=seconds)
        time_now = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None).time()
        day_to_send = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None).date()
        date_to_send = datetime.datetime.combine(day_to_send, datetime.time(hour=0))
        if time_to_send < time_now:
            date_to_send += datetime.timedelta(days=1)
        date_to_send = date_to_send.date()
        send_time = datetime.datetime.combine(date_to_send, time_to_send)  # Время в мск
        response = "Отложенный приказ на {}".format(send_time)
        send_time = moscow_tz.localize(send_time).astimezone(tz=local_tz).replace(tzinfo=None)  # Локальное время
        message = bot.sync_send_message(chat_id=update.message.chat_id, text=response, reply_markup=PultMarkup,
                                        reply_to_message_id=mes.message_id)
    elif 'variant':
        variant = True
        PultMarkup = rebuild_pult("default_variant", pult, None)
        message = bot.sync_send_message(
            chat_id=update.message.chat_id, text="Создание варинта битвы:",
            reply_markup=PultMarkup)
    pult = Pult(message.chat_id, message.message_id, deferred_time=send_time, variant=variant)  # Создаётся новый пульт


def get_variants_text():
    if not Pult.variants:
        return "Вариантов битвы нет!"
    response = "Текущие варианты битвы:\n"

    for order in list(Pult.variants.values()):
        div_str = ""
        if order.divisions == "ALL":
            div_str = " ВСЕ"
        else:
            for i in range(len(divisions_const)):
                if order.divisions[i]:
                    div_str += " {0}".format(divisions_const[i])
        response += "{}\n{}, {}{}{}{}Удалить вариант: /remove_variant_{}\n\n" \
                    "".format(div_str[1:], order.target,
                              "🛡:{}\n".format(order.target if order.defense == "Attack!" else
                                               order.defense) if order.defense is not None else "",
                              "Тактика: {}\n".format(order.tactics) if order.tactics != "" else "",
                              "⚗️ Атака\n" if order.potions[0] else "", "⚗️ Деф\n" if order.potions[1] else "",
                              order.deferred_id)
    return response


def get_variants_markup():
    MAX_BUTTONS_IN_ROW = 2
    if not Pult.variants:
        return None
    buttons = [[]]
    current_row = 0
    for order in list(Pult.variants.values()):
        if len(buttons[current_row]) >= MAX_BUTTONS_IN_ROW:
            current_row += 1
            buttons.append([])
        print(order.potions)
        buttons[current_row].append(InlineKeyboardButton(
            text="{},{}{}{}{}".format(order.target, "🛡:{} ".format(order.target if order.defense == "Attack!" else
                                                                   order.defense) if order.defense is not None else "",
                                      "⚗️⚔️ " if order.potions[0] else "", "⚗️🛡 " if order.potions[1] else "",
                                      "/t{}".format(tactics_order_to_emoji.get(order.tactics)) if
                                      order.tactics != "" else "", order.deferred_id),
            callback_data="var_send_{}".format(order.deferred_id)))

    return InlineKeyboardMarkup(buttons)


def remove_variant(bot, update):
    mes = update.message
    order_id = re.search("_(\\d+)", mes.text)
    if order_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис")
        return
    order_id = int(order_id.group(1))
    order = Pult.variants.get(order_id)
    if order is None:
        bot.send_message(chat_id=mes.chat_id, text="Вариант не найден")
        return
    Pult.variants.pop(order_id)
    bot.send_message(chat_id=mes.chat_id, text="Вариант успешно удалён.")


def pult_variants(bot, update):
    response = get_variants_text()
    buttons = get_variants_markup()
    bot.send_message(chat_id=update.message.chat_id, text=response, reply_markup=buttons, parse_mode='HTML')


def send_variant(bot, update):
    data = update.callback_query.data
    try:
        fill_mid_players(other_process=True)  # TODO сделать нормально
    except Exception:
        logging.error(traceback.format_exc())
    if not check_access(update.callback_query.from_user.id):
        return
    variant_id = re.search("_(\\d+)", data)
    if variant_id is None:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Ошибка поиска варианта",
                                show_alert=True)
        return
    variant_id = int(variant_id.group(1))
    order = Pult.variants.get(variant_id)
    if order is None:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Ошибка поиска варианта",
                                show_alert=True)
        return
    send_order(bot=bot, chat_callback_id=update.callback_query.message.chat_id, divisions=order.divisions,
               castle_target=order.target, defense=order.defense, tactics=order.tactics, potions=order.potions,
               time=None)
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id)


def pult_callback(bot, update):
    update.callback_query.data = update.callback_query.data.partition("_")[0]
    data = update.callback_query.data
    try:
        fill_mid_players(other_process=True)  # TODO сделать нормально
    except Exception:
        logging.error(traceback.format_exc())
    if not check_access(update.callback_query.from_user.id):
        return
    if data == "ps":
        pult_send(bot, update)
        return
    if data.find("pdv") == 0:
        pult_divisions_callback(bot, update)
        return
    if data.find("pc") == 0:
        pult_castles_callback(bot, update)
        return
    if data.find("pt") == 0:
        pult_time_callback(bot, update)
        return
    if data.find("pds") == 0:
        pult_defense_callback(bot, update)
        return
    if data.find("pdt") == 0:
        pult_tactics_callback(bot, update)
        return
    if data.find("pp") == 0:
        pult_potions_callback(bot, update)
        return


def pult_send(bot, update):
    globals.logs += "{} - @{} Нажал \"Отправить\"" \
                      "\n".format(datetime.datetime.now(tz=moscow_tz).strftime("%d/%m/%y %H-%M-%S"),
                                  update.callback_query.from_user.username)
    mes = update.callback_query.message
    pult = Pult.get_pult(mes.chat_id, mes.message_id)
    pult_status = pult.status
    target = pult_status.get("target")
    time_to_send = pult_status.get("time")
    tactics_num = pult_status.get("tactics")
    potions = pult.potions_active.copy()
    if target == -1:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Необходимо выбрать цель")
        return
    divisions = pult_status.get("divisions").copy()
    if not any(divisions):
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Необходимо выбрать дивизион")
        return
    if divisions[len(divisions) - 1]:
        divisions = "ALL"
    elif divisions[pult.all_attackers_division_num] is True:
        for i in range(pult.all_attackers_division_num):
            divisions[i] = True
    print(divisions)
    castle_target = castles[target]
    defense = pult_status.get("defense")
    defense_target = defense_to_order[defense]
    tactics_target = tactics_to_order[tactics_num]
    if pult.variant:
        # Создание варианта битвы
        i = int(time.time() % (24 * 60 * 60))  # id уникален в течении суток
        while Pult.variants and i in Pult.variants:
            i += 1
        current = DeferredOrder(i, globals.order_id, divisions, time_to_send, castle_target, defense_target,
                                tactics_target, potions, None)
        pult.variants.update({i: current})
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Вариант создан.")
        return
    if time_to_send < 0 and pult.deferred_time is None:
        # Мгновенная отправка приказа
        send_order(bot=bot, chat_callback_id=mes.chat_id, divisions=divisions, castle_target=castle_target,
                   defense=defense_target, tactics=tactics_target, potions=potions)
        return
    # Планирование отложки
    if pult.deferred_time is not None:
        time_to_send = pult.deferred_time
    else:
        next_battle = count_next_battle_time()
        logging.info("Next battle : {0}".format(next_battle))
        next_battle_time = next_battle.time()
        if time_to_send == 0:   # Мгновенная отправка, но с подстановкой времени в пин
            send_order(bot=bot, chat_callback_id=mes.chat_id, divisions=divisions, castle_target=castle_target,
                       defense=defense_target, tactics=tactics_target, time=next_battle_time, potions=potions)
            bot.answerCallbackQuery(callback_query_id=update.callback_query.id)
            return
        time_to_send = next_battle - times_to_time[time_to_send]
        time_to_send = moscow_tz.localize(time_to_send).astimezone(local_tz).replace(tzinfo=None)
    #------------------------------------------------------------------------------------------------------- TEST ONLY
    #time_to_send = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None).replace(hour=16, minute=31, second=0)
    #-------------------------------------------------------------------------------------------------------
    if divisions == "ALL":
        divisions = []
        for i in range(len(divisions_const)):
            divisions.append(False)
        divisions[-1] = True
    request = "insert into deferred_orders(order_id, time_set, target, defense, tactics, divisions, potions) values " \
              "(%s, %s, %s, %s, %s, %s, %s) returning deferred_id"
    cursor.execute(request, (globals.order_id, time_to_send, target, defense, tactics_target, divisions, potions))
    row = cursor.fetchone()

    context = [mes.chat_id, castle_target, defense_target, tactics_target, divisions, potions, row[0]]
    j = job.run_once(send_order_job, time_to_send.astimezone(local_tz).replace(tzinfo=None), context=context)

    current = DeferredOrder(row[0], globals.order_id, divisions, time_to_send, castle_target, defense_target,
                            tactics_target, potions, j)
    deferred_orders.append(current)

    logging.info("Deffered successful on {0}".format(time_to_send))
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Приказ успешно отложен")
    new_text = Pult.get_text()
    reply_markup = rebuild_pult("None", pult, None)
    bot.editMessageText(chat_id=mes.chat_id, message_id=mes.message_id, text=new_text+ "\n\n{0}".format(
                datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None).strftime("%d/%m/%y %H:%M:%S")),
                        reply_markup=reply_markup, parse_mode='HTML')


def pult_divisions_callback(bot, update):
    mes = update.callback_query.message
    pult = Pult.get_pult(mes.chat_id, mes.message_id)
    pult_status = pult.status
    new_target = int(update.callback_query.data[3:])
    return_value = rebuild_pult("change_division", pult, new_target)
    new_markup = return_value[0]
    new_division = return_value[1]
    pult_status.update({"divisions": new_division })
    edit_pult(bot=bot, chat_id=mes.chat_id, message_id=mes.message_id, reply_markup=new_markup,
              callback_query_id=update.callback_query.id)
    globals.logs += "{} - @{} - Изменил дивизион на {}" \
            "\n".format(datetime.datetime.now(tz=moscow_tz).strftime("%d/%m/%y %H-%M-%S"),
                        update.callback_query.from_user.username, divisions_const[new_target])


def pult_castles_callback(bot, update):
    mes = update.callback_query.message
    pult = Pult.get_pult(mes.chat_id, mes.message_id)
    pult_status = pult.status
    new_target = int(update.callback_query.data[2:])
    new_markup = rebuild_pult("change_target", pult, new_target)
    pult_status.update({"target": new_target})
    edit_pult(bot=bot, chat_id=mes.chat_id, message_id=mes.message_id, reply_markup=new_markup,
              callback_query_id=update.callback_query.id)
    globals.logs += "{} - @{} - Изменил цель на {}" \
                      "\n".format(datetime.datetime.now(tz=moscow_tz).strftime("%d/%m/%y %H-%M-%S"),
                                  update.callback_query.from_user.username, castles[new_target])


def pult_time_callback(bot, update):
    mes = update.callback_query.message
    pult = Pult.get_pult(mes.chat_id, mes.message_id)
    pult_status = pult.status
    data = update.callback_query.data
    new_time = int(data[2:])
    new_markup = rebuild_pult("change_time", pult, new_time)
    pult_status.update({ "time" : new_time })
    edit_pult(bot=bot, chat_id=mes.chat_id, message_id=mes.message_id, reply_markup=new_markup,
              callback_query_id=update.callback_query.id)
    globals.logs += "{} - @{} - Изменил время пина на {}" \
            "\n".format(datetime.datetime.now(tz=moscow_tz).strftime("%d/%m/%y %H-%M-%S"),
                        update.callback_query.from_user.username, times_to_time[new_time])


def pult_defense_callback(bot, update):
    mes = update.callback_query.message
    pult = Pult.get_pult(mes.chat_id, mes.message_id)
    pult_status = pult.status
    data = update.callback_query.data
    new_defense = int(data[3:])
    old_defense = pult_status.get("defense")
    if old_defense == new_defense:
        new_defense = 2
    new_markup = rebuild_pult("change_defense", pult, new_defense)
    pult_status.update({"defense": new_defense})
    edit_pult(bot=bot, chat_id=mes.chat_id, message_id=mes.message_id, reply_markup=new_markup,
              callback_query_id=update.callback_query.id)
    globals.logs += "{} - @{} - Изменил деф на {}" \
                      "\n".format(datetime.datetime.now(tz=moscow_tz).strftime("%d/%m/%y %H-%M-%S"),
                                  update.callback_query.from_user.username, defense_to_order[new_defense])


def pult_tactics_callback(bot, update):
    mes = update.callback_query.message
    pult = Pult.get_pult(mes.chat_id, mes.message_id)
    pult_status = pult.status
    data = update.callback_query.data
    new_tactics = int(data[3:])
    if new_tactics == pult_status.get("tactics"):
        new_tactics = -1
    new_markup = rebuild_pult("change_tactics", pult, new_tactics)
    pult_status.update({"tactics": new_tactics})
    edit_pult(bot=bot, chat_id=mes.chat_id, message_id=mes.message_id, reply_markup=new_markup,
              callback_query_id=update.callback_query.id)
    globals.logs += "{} - @{} - Изменил тактику на {}" \
                      "\n".format(datetime.datetime.now(tz=moscow_tz).strftime("%d/%m/%y %H-%M-%S"),
                                  update.callback_query.from_user.username, tactics_to_order[new_tactics])


def pult_potions_callback(bot, update):
    mes = update.callback_query.message
    pult = Pult.get_pult(mes.chat_id, mes.message_id)
    pult_status = pult.status
    data = update.callback_query.data
    new_potions = int(data[2:])
    new_markup = rebuild_pult("change_potions", pult, new_potions)
    edit_pult(bot=bot, chat_id=mes.chat_id, message_id=mes.message_id, reply_markup=new_markup,
              callback_query_id=update.callback_query.id)
    globals.logs += "{} - @{} - Изменил зелья на {}" \
                      "\n".format(datetime.datetime.now(tz=moscow_tz).strftime("%d/%m/%y %H-%M-%S"),
                                  update.callback_query.from_user.username, potions_consts[new_potions])


def edit_pult(bot, chat_id, message_id, reply_markup, callback_query_id):
    try:
        bot.editMessageReplyMarkup(chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)
    except BadRequest:
        pass
    except TelegramError:
        logging.error(traceback.format_exc)
    finally:
        bot.answerCallbackQuery(callback_query_id=callback_query_id)


def plan_battle_jobs():
    job.run_once(after_battle, moscow_tz.localize(count_next_battle_time()).astimezone(tz=local_tz).replace(tzinfo=None))


def after_battle(bot, job):
    time.sleep(1)
    plan_battle_jobs()
    Pult.variants.clear()
    send_and_clear_logs()


def send_and_clear_logs():
    for logs_to_send in [globals.logs[i:i + MAX_MESSAGE_LENGTH] for i in range(
            0, len(globals.logs), MAX_MESSAGE_LENGTH)]:
        bot.sync_send_message(chat_id=LOGS_CHAT_ID, text=logs_to_send)
    globals.logs = ""
