import logging, time
from telegram import KeyboardButton, ReplyKeyboardMarkup

from time import strftime
from work_materials.globals import *
from libs.order import *
from work_materials.pult_constants import divisions as division_const, castles

import work_materials.globals as globals


def build_menu(buttons,
               n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


def menu(bot, update):
    button_list = [
    KeyboardButton("/⚔ 🍁"),
    KeyboardButton("/⚔ ☘"),
    KeyboardButton("/⚔ 🖤"),
    KeyboardButton("/⚔ 🐢"),
    KeyboardButton("/⚔ 🦇"),
    KeyboardButton("/⚔ 🌹"),
    KeyboardButton("/⚔ 🍆"),
    ]
    reply_markup = ReplyKeyboardMarkup(build_menu(button_list, n_cols=3))
    bot.send_message(chat_id=update.message.chat_id, text = 'Select castle', reply_markup=reply_markup)


def attackCommand(bot, update):
    response = update.message.text[1:len(update.message.text)]
    stats = "Рассылка пинов началась в <b>{0}</b>\n\n".format(time.ctime())

    bot.send_message(chat_id=update.message.chat_id, text=stats, parse_mode = 'HTML')
    request = "select chat_id, pin, disable_notification from guild_chats where enabled = '1'"
    cursor.execute(request)
    row = cursor.fetchone()
    orders_sent = 0
    while row:
        bot.send_order(order_id=globals.order_id, chat_id=row[0], response=response, pin=row[1], notification=not row[2])
        row = cursor.fetchone()
        orders_sent += 1
    response = ""
    orders_OK = 0
    orders_failed = 0
    while orders_OK + orders_failed < orders_sent:
        current = order_backup_queue.get()
        if current.order_id == globals.order_id:
            if current.OK:
                orders_OK += 1
            else:
                orders_failed += 1
                response += current.text
        else:
            order_backup_queue.put(current)
            logging.warning("Incorrect order_id, received {0}, now it is {1}".format(current, globals.order_id))

    globals.order_id += 1
    stats = "Выполнено в <b>{0}</b>, отправлено в <b>{1}</b> чатов, " \
            "ошибка при отправке в <b>{2}</b> чатов\n\n".format(time.ctime(), orders_OK, orders_failed) + response
    bot.send_message(chat_id=update.message.chat_id, text=stats, parse_mode = 'HTML')
    return

def send_order(bot, chat_callback_id, divisions, castle_target, defense, tactics, time = None):
    time_begin = datetime.datetime.now()
    time_add_str = "" if time is None else time.strftime("%H:%M")
    response = "{3}⚔️{0}\n🛡{1}\n{2}\n".format(castle_target, defense if defense else castle_target, tactics, time_add_str)
    orders_sent = 0
    if divisions == 'ALL':
        for chat in order_chats:
            bot.send_order(order_id=globals.order_id, chat_id=chat[0], response=response, pin=chat[1], notification=not chat[2])
            orders_sent += 1
    else:
        current_divisions = []
        for i in range(0, len(divisions)):
            if divisions[i]:
                current_divisions.append(division_const[i])
        for chat in order_chats:
            if chat[3] in current_divisions:
                bot.send_order(order_id=globals.order_id, chat_id=chat[0], response=response, pin=chat[1], notification=not chat[2])
                orders_sent += 1
    response = ""
    orders_OK = 0
    orders_failed = 0
    while orders_OK + orders_failed < orders_sent:
        current = order_backup_queue.get()
        if current.order_id == globals.order_id:
            if current.OK:
                orders_OK += 1
            else:
                orders_failed += 1
                response += current.text
        else:
            order_backup_queue.put(current)
            logging.warning("Incorrect order_id, received {0}, now it is {1}".format(current, globals.order_id))

    globals.order_id += 1
    time_end = datetime.datetime.now()
    time_delta = time_end - time_begin
    stats = "Выполнено в <b>{0}</b>, отправлено в <b>{1}</b> чатов, " \
            "ошибка при отправке в <b>{2}</b> чатов, " \
            "рассылка заняла <b>{3}</b>\n\n".format(datetime.datetime.now(tz=moscow_tz), orders_OK, orders_failed, time_delta) + response
    bot.send_message(chat_id = chat_callback_id, text=stats, parse_mode='HTML')

def send_order_job(bot, job):
    chat_callback_id = job.context[0]
    castle_target = job.context[1]
    defense = job.context[2]
    tactics = job.context[3]
    divisions = job.context[4]
    send_order(bot, chat_callback_id, divisions, castle_target, defense, tactics)
    refill_deferred_orders()

def remove_order(bot, update):
    mes = update.message
    deferred_id = int(mes.text.partition("@")[0].split("_")[2])
    current_order = None
    for order in deferred_orders:
        if order.deferred_id == deferred_id:
            current_order = order
            deferred_orders.remove(order)
            break
    request = "delete from deferred_orders where deferred_id = %s"
    cursor.execute(request, (deferred_id,))
    try:
        current_order.job.schedule_removal()
    except AttributeError:
        bot.send_message(chat_id = mes.chat_id, text="Приказ существует?")
        return
    bot.send_message(chat_id=mes.chat_id, text="Приказ успешно отменён")


def recashe_order_chats():
    logging.info("Recaching chats...")
    order_chats.clear()
    request = "select chat_id, pin, disable_notification, division from guild_chats where enabled = '1'"
    cursor.execute(request)
    row = cursor.fetchone()
    while row:
        current = []
        for elem in row:
            current.append(elem)
        order_chats.append(current)
        row = cursor.fetchone()
    logging.info("Recashing done")

def refill_deferred_orders():
    logging.info("Refilling deferred orders...")
    request = "select order_id, time_set, target, defense, tactics, deferred_id, divisions from deferred_orders"
    cursor.execute(request)
    row = cursor.fetchone()
    cursor2 = conn.cursor()
    while row:
        time_to_send = row[1].replace(tzinfo = moscow_tz)
        target = row[2]
        castle_target = castles[target]
        defense = row[3]
        tactics = row[4]
        divisions = row[6]
        now = datetime.datetime.now(tz = moscow_tz)
        if now > time_to_send:
            request = "delete from deferred_orders where deferred_id = '{0}'".format(row[5])
            cursor2.execute(request)
        else:
            context = [CALLBACK_CHAT_ID, castle_target, defense, tactics, divisions]
            j = job.run_once(send_order_job, time_to_send.astimezone(local_tz).replace(tzinfo = None), context=context)
            current = DeferredOrder(row[5], globals.order_id, divisions, time_to_send, castle_target, defense, tactics, j)
            deferred_orders.append(current)
        row = cursor.fetchone()
    logging.info("Orders refilled")