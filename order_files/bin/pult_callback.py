import traceback
from telegram.error import (TelegramError, BadRequest)

from order_files.work_materials.pult_constants import *
from order_files.libs.pult import rebuild_pult, Pult
from order_files.libs.deferred_order import DeferredOrder
from order_files.bin.order import send_order, send_order_job
from order_files.work_materials.pult_constants import divisions as divisions_const

from order_files.work_materials.globals import cursor, deferred_orders, moscow_tz, local_tz, job, admin_ids

import order_bot
import order_files.work_materials.globals as globals

import logging
import re


# Вызов нового пульта
def pult(bot, update):
    mes = update.message
    pult = Pult.get_pult(0, 0)  # Пульт - болванка
    PultMarkup = rebuild_pult("default", pult, None)
    response = ""
    message = None
    send_time = None
    if 'pult' in mes.text:
        # Обычный пульт
        response += Pult.get_text()

        message = bot.sync_send_message(
            chat_id=update.message.chat_id, text=response + "\n\n{0}".format(
                datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None).strftime("%d/%m/%y %H:%M:%S")),
            reply_markup=PultMarkup)
    elif 'order' in mes.text:
        # Вызывается пульт для установки отложки
        line = re.search("order (\\d+)-?(\\d*)-?(\\d*)", mes.text)
        if line is None:
            bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис")
            return
        hours = int(line.group(1))
        minutes = int(line.group(2)) if line.group(2) != '' else 0
        seconds = int(line.group(3)) if line.group(3) != '' else 0
        time_to_send = datetime.time(hour=hours, minute=minutes, second=seconds)
        time_now = datetime.datetime.now().time()
        day_to_send = datetime.datetime.now().date()
        date_to_send = datetime.datetime.combine(day_to_send, datetime.time(hour=0))
        if time_to_send < time_now:
            date_to_send += datetime.timedelta(days=1)
        date_to_send = date_to_send.date()
        send_time = datetime.datetime.combine(date_to_send, time_to_send)  # Время в мск
        response = "Отложенный приказ на {}".format(send_time)
        send_time = moscow_tz.localize(send_time).astimezone(tz=local_tz).replace(tzinfo=None)  # Локальное время

        message = bot.sync_send_message(chat_id=update.message.chat_id, text=response, reply_markup=PultMarkup,
                                        reply_to_message=mes.message_id)
    pult = Pult(message.chat_id, message.message_id, deferred_time=send_time)  # Создаётся новый пульт


def pult_callback(bot, update):
    data = update.callback_query.data
    if update.callback_query.from_user.id not in admin_ids:
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


def pult_send(bot, update):
    order_bot.logs += "{} - @{} Нажал \"Отправить\"" \
                      "\n".format(datetime.datetime.now(tz=moscow_tz).strftime("%d/%m/%y %H-%M-%S"),
                                  update.callback_query.from_user.username)
    print(order_bot.logs)
    mes = update.callback_query.message
    pult = Pult.get_pult(mes.chat_id, mes.message_id)
    pult_status = pult.status
    target = pult_status.get("target")
    time_to_send = pult_status.get("time")
    tactics_num = pult_status.get("tactics")
    if target == -1:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Необходимо выбрать цель")
        return
    divisions = pult_status.get("divisions").copy()
    if divisions[len(divisions) - 1]:
        divisions = "ALL"
    castle_target = castles[target]
    defense = pult_status.get("defense")
    defense_target = defense_to_order[defense]
    tactics_target = tactics_to_order[tactics_num]
    if time_to_send < 0 and pult.deferred_time is None:
        send_order(bot = bot, chat_callback_id = mes.chat_id, divisions = divisions, castle_target = castle_target,
                   defense = defense_target, tactics = tactics_target)
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id)
        return
    if pult.deferred_time is not None:
        time_to_send = pult.deferred_time
    else:
        next_battle = datetime.datetime.now(tz = moscow_tz).replace(tzinfo=None).replace(hour = 1, minute = 0, second=0,
                                                                                         microsecond=0)

        now = datetime.datetime.now(tz = moscow_tz).replace(tzinfo=None)
        while next_battle < now:
            next_battle += datetime.timedelta(hours=8)
        logging.info("Next battle : {0}".format(next_battle))
        next_battle_time = next_battle.time()
        if time_to_send == 0:   # Мгновенная отправка, но с подстановкой времени в пин
            send_order(bot = bot, chat_callback_id = mes.chat_id, divisions = divisions, castle_target = castle_target,
                       defense = defense_target, tactics = tactics_target, time = next_battle_time)
            bot.answerCallbackQuery(callback_query_id=update.callback_query.id)
            return
        time_to_send = next_battle - times_to_time[time_to_send]
        time_to_send = moscow_tz.localize(time_to_send).astimezone(local_tz)
    #------------------------------------------------------------------------------------------------------- TEST ONLY
    #time_to_send = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None).replace(hour=16, minute=31, second=0)
    #-------------------------------------------------------------------------------------------------------
    if divisions == "ALL":
        divisions = []
        for i in range(len(divisions_const)):
            divisions.append(False)
        divisions[-1] = True
    request = "insert into deferred_orders(order_id, time_set, target, defense, tactics, divisions) values " \
              "(%s, %s, %s, %s, %s, %s) returning deferred_id"
    cursor.execute(request, (globals.order_id, time_to_send, target, defense, tactics_target, divisions))
    row = cursor.fetchone()

    context = [mes.chat_id, castle_target, defense_target, tactics_target, divisions, row[0]]
    j = job.run_once(send_order_job, time_to_send.astimezone(local_tz).replace(tzinfo=None), context=context)

    current = DeferredOrder(row[0], globals.order_id, divisions, time_to_send, castle_target, defense_target,
                            tactics_target, j)
    deferred_orders.append(current)

    logging.info("Deffered successful on {0}".format(time_to_send))
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text = "Приказ успешно отложен")
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
    order_bot.logs += "{} - @{} - Изменил дивизион на {}" \
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
    order_bot.logs += "{} - @{} - Изменил цель на {}" \
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
    order_bot.logs += "{} - @{} - Изменил время пина на {}" \
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
    order_bot.logs += "{} - @{} - Изменил деф на {}" \
                      "\n".format(datetime.datetime.now(tz=moscow_tz).strftime("%d/%m/%y %H-%M-%S"),
                                  update.callback_query.from_user.username, defense_to_order[new_defense])


def pult_tactics_callback(bot, update):
    mes = update.callback_query.message
    pult = Pult.get_pult(mes.chat_id, mes.message_id)
    pult_status = pult.status
    data = update.callback_query.data
    new_tactics = int(data[3:])
    new_markup = rebuild_pult("change_tactics", pult, new_tactics)
    pult_status.update({"tactics": new_tactics})
    edit_pult(bot=bot, chat_id=mes.chat_id, message_id=mes.message_id, reply_markup=new_markup,
              callback_query_id=update.callback_query.id)
    order_bot.logs += "{} - @{} - Изменил тактику на {}" \
                      "\n".format(datetime.datetime.now(tz=moscow_tz).strftime("%d/%m/%y %H-%M-%S"),
                                  update.callback_query.from_user.username, tactics_to_order[new_tactics])


def edit_pult(bot, chat_id, message_id, reply_markup, callback_query_id):
    try:
        bot.editMessageReplyMarkup(chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)
    except BadRequest:
        pass
    except TelegramError:
        logging.error(traceback.format_exc)
    finally:
        bot.answerCallbackQuery(callback_query_id=callback_query_id)
