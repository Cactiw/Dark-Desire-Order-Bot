import traceback
from telegram.error import (TelegramError, BadRequest)

from order_files.work_materials.pult_constants import *
from order_files.libs.pult import rebuild_pult
from order_files.libs.deferred_order import DeferredOrder
from order_files.bin.order import send_order, send_order_job
from order_files.work_materials.pult_constants import divisions as divisions_const

from order_files.work_materials.globals import cursor, deferred_orders, moscow_tz, local_tz, job, admin_ids

import order_files.work_materials.globals as globals

import logging


pult_status = { 'divisions' : [False, False, False, True], 'target' : -1 , 'defense' : 2, 'time' : 0, "tactics" : 5}



def pult(bot, update):
    global pult_status
    pult_status = pult_status_default.copy()
    PultMarkup = rebuild_pult("default", None)
    response = ""
    for order in deferred_orders:
        div_str = ""
        for i in range(len(divisions_const)):
            if order.divisions[i]:
                div_str += " {0}".format(divisions_const[i])
        response += "{5}\n{0} -- {1}\nDefense home: {2}\n" \
                    "Tactics: {3}\nremove: /remove_order_{4}\n" \
                    "\n".format(order.time_set.replace(tzinfo = None).strftime("%D %H:%M:%S"), order.target,
                                order.defense, order.tactics, order.deferred_id, div_str[1:])
    bot.send_message(chat_id = update.message.chat_id,
                     text = response + "\n\n{0}".format(datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None).strftime("%D %H:%M:%S")),
                     reply_markup = PultMarkup)


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
    mes = update.callback_query.message
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
    if time_to_send < 0:
        send_order(bot = bot, chat_callback_id = mes.chat_id, divisions = divisions, castle_target = castle_target,
                   defense = defense_target, tactics = tactics_target)
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id)
        return
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


def pult_divisions_callback(bot, update):
    mes = update.callback_query.message
    new_target = int(update.callback_query.data[3:])
    return_value = rebuild_pult("change_division", new_target)
    new_markup = return_value[0]
    new_division = return_value[1]
    pult_status.update({ "divisions" : new_division })
    edit_pult(bot = bot, chat_id=mes.chat_id, message_id=mes.message_id, reply_markup=new_markup,
              callback_query_id=update.callback_query.id)


def pult_castles_callback(bot, update):
    mes = update.callback_query.message
    new_target = int(update.callback_query.data[2:])
    new_markup = rebuild_pult("change_target", new_target)
    pult_status.update({ "target" : new_target })
    edit_pult(bot = bot, chat_id=mes.chat_id, message_id=mes.message_id, reply_markup=new_markup,
              callback_query_id=update.callback_query.id)


def pult_time_callback(bot, update):
    mes = update.callback_query.message
    data = update.callback_query.data
    new_time = int(data[2:])
    new_markup = rebuild_pult("change_time", new_time)
    pult_status.update({ "time" : new_time })
    edit_pult(bot = bot, chat_id=mes.chat_id, message_id=mes.message_id, reply_markup=new_markup,
              callback_query_id=update.callback_query.id)


def pult_defense_callback(bot, update):
    mes = update.callback_query.message
    data = update.callback_query.data
    new_defense = int(data[3:])
    old_defense = pult_status.get("defense")
    if old_defense == new_defense:
        new_defense = 2
    new_markup = rebuild_pult("change_defense", new_defense)
    pult_status.update({"defense": new_defense})
    edit_pult(bot = bot, chat_id=mes.chat_id, message_id=mes.message_id, reply_markup=new_markup, callback_query_id=update.callback_query.id)


def pult_tactics_callback(bot, update):
    mes = update.callback_query.message
    data = update.callback_query.data
    new_tactics = int(data[3:])
    new_markup = rebuild_pult("change_tactics", new_tactics)
    pult_status.update({"tactics": new_tactics})
    edit_pult(bot = bot, chat_id=mes.chat_id, message_id=mes.message_id, reply_markup=new_markup, callback_query_id=update.callback_query.id)


def edit_pult(bot, chat_id, message_id, reply_markup, callback_query_id):
    try:
        bot.editMessageReplyMarkup(chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)
    except BadRequest:
        pass
    except TelegramError:
        logging.error(traceback.format_exc)
    finally:
        bot.answerCallbackQuery(callback_query_id=callback_query_id)

