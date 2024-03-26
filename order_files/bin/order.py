import logging, time

import pytz
from telegram import KeyboardButton, ReplyKeyboardMarkup

from order_files.work_materials.globals import cursor, order_chats, deferred_orders, job, moscow_tz, CALLBACK_CHAT_ID, \
    local_tz, conn, admin_ids, LOGS_CHAT_ID, MAX_MESSAGE_LENGTH
from order_files.libs.deferred_order import DeferredOrder
from order_files.work_materials.pult_constants import divisions as division_const, castles, defense_to_order, \
    potions_to_order
from order_files.libs.bot_async_messaging import order_backup_queue
from order_files.libs.pult import Pult
from order_files.libs.bot_async_messaging import advanced_callback
from order_files.bin.buttons import get_order_buttons

from bin.service_functions import count_next_battle_time

import order_files.work_materials.globals as globals
import datetime
import threading


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
    request = "select chat_id, pin_enabled, disable_notification from guilds where orders_enabled = '1'"
    cursor.execute(request)
    row = cursor.fetchone()
    orders_sent = 0
    while row:
        bot.send_order(order_id=globals.order_id, chat_id=row[0], response=response, pin_enabled=row[1], notification=not row[2])
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
            # order_backup_queue.put(current)
            logging.warning("Incorrect order_id, received {0}, now it is {1}".format(current.order_id, globals.order_id))

    globals.order_id += 1
    stats = "Выполнено в <b>{0}</b>, отправлено в <b>{1}</b> чатов, " \
            "ошибка при отправке в <b>{2}</b> чатов\n\n".format(time.ctime(), orders_OK, orders_failed) + response
    bot.send_message(chat_id=update.message.chat_id, text=stats, parse_mode = 'HTML')
    return


def wait_debug(bot, orders_count):
    orders = {}
    orders_full = 0
    while orders_full < orders_count:
        data = advanced_callback.get()
        chat_id = data.get("chat_id")
        d = orders.get(chat_id)
        if d is None:
            d = {}
            orders.update({chat_id: d})
        for t in ["begin", "sent", "pin_end", "wait_start", "wait_end"]:
            if t in list(data):
                d.update({t: data.get(t)})
        # print(chat_id, d, *(k in d for k in ["begin", "sent", "pin_end", "wait_start", "wait_end"]))
        if all(k in d for k in ["begin", "sent", "pin_end", "wait_start", "wait_end"]):
            orders_full += 1
        # print(orders_full)
    response = "Рассылка в <b>{}</b>:\n".format(time.time())
    for chat_id, data in list(orders.items()):
        begin, wait_start, wait_end, sent, pin_end = data.get("begin"), data.get("wait_start"), data.get("wait_end"),\
                                                     data.get("sent"), data.get("pin_end")
        if not all([begin, wait_start, wait_end, sent, pin_end]):
            continue
        new_response = "Chat_id: <code>{}</code>" \
                       "\nВремя ожидания: <b>{}</b>\nВремя отправки: <b>{}</b>\nВремя пина: <b>{}</b>" \
                       "\nОбщее время пина: <b>{}</b>" \
                       "\n\n".format(chat_id, wait_end - wait_start,
                                     sent - wait_end, pin_end - sent, pin_end - wait_end)
        if len(response + new_response) > 4096:
            bot.send_message(chat_id=admin_ids[0], text=response, parse_mode='HTML')
            response = ""
        response += new_response
    bot.send_message(chat_id=admin_ids[0], text=response, parse_mode='HTML')


def send_order(bot, chat_callback_id, divisions, castle_target, defense, tactics, potions, time=None):
    bot = globals.bot_castle
    time_to_battle = count_next_battle_time() - datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)
    if time_to_battle >= datetime.timedelta(seconds=55):
        recashe_order_chats()
    time_begin = datetime.datetime.now()
    time_add_str = count_next_battle_time().astimezone(pytz.UTC).strftime("%H:%M") if time is None else time.strftime("%H:%M")
    pot_str = ""
    for i, p in enumerate(potions):
        if p:
            pot_str += potions_to_order[i]
    response = "{3}⚔:{0}\n{1}{2}\n\n{4}" \
               "\n".format(castle_target, "🛡:{}\n".format(castle_target if defense == "Attack!"
                                                         else defense) if defense is not None else "",
                           "<a href=\"https://t.me/share/url?url={}\">{}</a>".format(tactics, tactics)
                           if tactics != "" else "", "{}\n".format(time_add_str) if time_add_str != "" else
                                          time_add_str, pot_str)
    if '⚔:🦌Def!🛡\n🛡:🦌Def!🛡' in response:
        response = response.replace("⚔:🦌Def!🛡\n🛡:🦌Def!🛡", "🦌 FD! 🦌")
    if datetime.date(year=datetime.datetime.today().year, day=31, month=12) <= \
                datetime.date.today() <= datetime.date(year=datetime.datetime.today().year, day=3, month=1):
        response += "\n\n🎇Happy New Year!🎇\n"
    buttons = get_order_buttons(castle_target, defense)
    orders_sent = 0
    if divisions == 'ALL':
        for chat in order_chats:
            if chat[3] != 'Trust':
                bot.send_order(order_id=globals.order_id, chat_id=chat[0], response=response, pin_enabled=chat[1],
                               notification=not chat[2], reply_markup=buttons)
                orders_sent += 1
    else:
        current_divisions = []
        for i in range(0, len(divisions)):
            if divisions[i]:
                current_divisions.append(division_const[i])
        if len(current_divisions) == 1 and current_divisions[0] == 'Луки':
            # Пин только лукам
            response = response.replace("⚔", "🏹")
            buttons.inline_keyboard[0][0].text = buttons.inline_keyboard[0][0].text.replace("⚔", "🏹")
        for chat in order_chats:
            if chat[3] in current_divisions:
                bot.send_order(order_id=globals.order_id, chat_id=chat[0], response=response, pin_enabled=chat[1],
                               notification=not chat[2], reply_markup=buttons)
                orders_sent += 1
    threading.Thread(target=wait_debug, args=(bot, orders_sent)).start()
    response = ""
    orders_OK = 0
    orders_failed = 0
    orders_stuck = 0
    while orders_OK + orders_failed < orders_sent:
        current = order_backup_queue.get()
        if current.order_id == globals.order_id:
            if current.OK:
                orders_OK += 1
            else:
                orders_failed += 1
                response += current.text
        else:
            orders_stuck += 1
            logging.warning("Incorrect order_id, received {0}, now it is {1}".format(current, globals.order_id))
            if orders_stuck < 1_000:
                order_backup_queue.put(current)

    globals.order_id += 1
    time_end = datetime.datetime.now()
    time_delta = time_end - time_begin
    stats = "Выполнено в <b>{0}</b>, отправлено в <b>{1}</b> чатов, " \
            "ошибка при отправке в <b>{2}</b> чатов, " \
            "рассылка заняла <b>{3}</b>\n\n".format(datetime.datetime.now(tz=moscow_tz), orders_OK, orders_failed, time_delta) + response
    bot.send_message(chat_id = chat_callback_id, text=stats, parse_mode='HTML')


# Начало отправки отложки
def send_order_job(bot, job):
    chat_callback_id = job.context[0]
    castle_target = job.context[1]
    defense = job.context[2]
    tactics = job.context[3]
    print(tactics)
    divisions = job.context[4]
    if divisions[len(divisions) - 1]:
        divisions = "ALL"
    potions = job.context[5]
    deferred_id = job.context[6]
    send_order(bot, chat_callback_id, divisions, castle_target, defense, tactics, potions)
    for i, order in enumerate(deferred_orders):
        if order.deferred_id == deferred_id:
            order.delete()
            deferred_orders.pop(i)
            break
    # refill_deferred_orders()


# Удаление отложки
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
    pult = Pult.get_pult(None, Pult.last_pult_id)
    if pult is None:
        return
    new_text = pult.get_text()
    reply_markup = pult.get_reply_markup()
    bot.editMessageText(chat_id=pult.chat_id, message_id=pult.id, text=new_text + "\n\n{0}".format(
                datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None).strftime("%d/%m/%y %H:%M:%S")),
                        reply_markup=reply_markup, parse_mode='HTML')


# TODO ну и фигня же тут происходит, список списков. Переделать всё через классы!
def recashe_order_chats(new_cursor=None):
    if new_cursor is None:
        new_cursor = cursor  # Если в главном потоке, иначе он будет другим
    logging.info("Recaching chats...")
    order_chats.clear()
    request = "select chat_id, pin_enabled, disable_notification, division from guilds where orders_enabled = true"
    new_cursor.execute(request)
    row = new_cursor.fetchone()
    while row:
        current = []
        for elem in row:
            current.append(elem)
        order_chats.append(current)
        row = new_cursor.fetchone()
    logging.info("Recashing done")


def refill_deferred_orders():
    logging.info("Refilling deferred orders...")
    request = "select order_id, time_set, target, defense, tactics, deferred_id, divisions, potions from deferred_orders"
    cursor.execute(request)
    row = cursor.fetchone()
    cursor2 = conn.cursor()
    while row:
        time_to_send = row[1]
        target = row[2]
        castle_target = castles[target]
        defense = row[3]
        defense_target = None
        if defense is not None:
            defense_target = defense_to_order[defense]
        tactics = row[4]
        deferred_id = row[5]
        divisions = row[6]
        potions = row[7]
        now = datetime.datetime.now(tz=local_tz).replace(tzinfo=None)
        print(now, time_to_send)
        if now > time_to_send:
            request = "delete from deferred_orders where deferred_id = %s"
            cursor2.execute(request, (row[5],))
        else:
            context = [CALLBACK_CHAT_ID, castle_target, defense_target, tactics, divisions, potions, deferred_id]
            j = job.run_once(send_order_job, time_to_send.astimezone(local_tz).replace(tzinfo = None), context=context)
            current = DeferredOrder(row[5], globals.order_id, divisions, time_to_send, castle_target, defense_target, tactics, potions, j)
            deferred_orders.append(current)
        row = cursor.fetchone()
    logging.info("Orders refilled")


