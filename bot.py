from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, BaseFilter, CallbackQueryHandler
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.utils.request import Request

from telegram.error import (TelegramError, Unauthorized, BadRequest,
                            TimedOut, ChatMigrated, NetworkError)

import logging
import time
import datetime
import psycopg2
import threading
import traceback

import sys
import multiprocessing
from multiprocessing import Queue

from work_materials.globals import *
from work_materials.filters.pin_setup_filters import *
from work_materials.filters.service_filters import *

from libs.pult import build_pult, rebuild_pult

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

multiprocessing.log_to_stderr()
logger = multiprocessing.get_logger()
logger.setLevel(logging.INFO)


order_id = 0

pult_status = { 'target' : -1 , 'defense_home' : False}
order_chats = []


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


def send_order(bot, chat_id, response, notification):
    mes_current = None
    for i in range(0, 5):
        try:
            mes_current = bot.sync_send_message(chat_id=chat_id, text=response)  # Отправка в текущий чат
        except TelegramError:
            print("TELEGRAM ERROR")
            pass
        else:
            break

    try:
        bot.pinChatMessage(chat_id=chat_id, message_id=mes_current.message_id, disable_notification=notification)
        pass
    except TelegramError:
        pass


def attackCommand(bot, update):
    global order_id
    response = update.message.text[1:len(update.message.text)]
    stats = "Рассылка пинов началась в <b>{0}</b>\n\n".format(time.ctime())

    bot.send_message(chat_id=update.message.chat_id, text=stats, parse_mode = 'HTML')
    request = "select chat_id, pin, disable_notification from guild_chats where enabled = '1'"
    cursor.execute(request)
    row = cursor.fetchone()
    orders_sent = 0
    while row:
        bot.send_order(order_id=order_id, chat_id=row[0], response=response, pin=row[1], notification=not row[2])
        row = cursor.fetchone()
        orders_sent += 1
    response = ""
    orders_OK = 0
    orders_failed = 0
    while orders_OK + orders_failed < orders_sent:
        current = order_backup_queue.get()
        if current.order_id == order_id:
            if current.OK:
                orders_OK += 1
            else:
                orders_failed += 1
                response += current.text
        else:
            order_backup_queue.put(current)
            logging.warning("Incorrect order_id, received {0}, now it is {1}".format(current, order_id))

    order_id += 1
    stats = "Выполнено в <b>{0}</b>, отправлено в <b>{1}</b> чатов, " \
            "ошибка при отправке в <b>{2}</b> чатов\n\n".format(time.ctime(), orders_OK, orders_failed) + response
    bot.send_message(chat_id=update.message.chat_id, text=stats, parse_mode = 'HTML')
    return


def add_pin(bot, update):
    mes = update.message
    request = "SELECT guild_chat_id FROM guild_chats WHERE chat_id = '{0}'".format(mes.chat_id)
    cursor.execute(request)
    row = cursor.fetchone()
    if row is not None:
        bot.send_message(chat_id=update.message.chat_id, text='Беседа уже подключена к рассылке')
        return
    request = "INSERT INTO guild_chats(chat_id, chat_name) VALUES('{0}', '{1}')".format(mes.chat_id, mes.chat.title)
    cursor.execute(request)
    bot.send_message(chat_id=update.message.chat_id, text='Беседа успешо подключена к рассылке')
    recashe_order_chats()



def pin_setup(bot, update):
    request = "SELECT guild_chat_id, chat_id, chat_name, enabled, pin, disable_notification, division FROM guild_chats"
    cursor.execute(request)
    row = cursor.fetchone()
    response = "Текущие рассылки пинов:\n"
    while row:
        response_new = '\n' + str(row[0]) + ': ' + row[2] + ', chat_id = ' + str(row[1]) + '\npin = ' + str(row[4]) + '\ndisabled_notification = ' + str(row[5]) + '\nenabled = ' + str(row[3])
        response_new += '\n'
        if row[3]:
            response_new += 'disable /pinset_{0}_0'.format(row[0]) + '\n'
        else:
            response_new += 'enable /pinset_{0}_1'.format(row[0]) + '\n'

        if row[4]:
            response_new += 'disable_pin /pinpin_{0}_0'.format(row[0]) + '\n'
        else:
            response_new += 'enable_pin /pinpin_{0}_1'.format(row[0]) + '\n'

        if row[5]:
            response_new += 'enable_notification /pinmute_{0}_0'.format(row[0]) + '\n'
        else:
            response_new += 'disable_notification /pinmute_{0}_1'.format(row[0]) + '\n'
        response_new += 'division: {0}\n'.format(row[6])
        response_new += 'Change division: /pindivision_{0}\n\n'.format(row[0])
        if len(response + response_new) >= 4096:  # Превышение лимита длины сообщения
            bot.send_message(chat_id=update.message.chat_id, text=response, parse_mode='HTML')
            response = ""
        response += response_new

        row = cursor.fetchone()
    bot.send_message(chat_id=update.message.chat_id, text=response, reply_markup=ReplyKeyboardRemove())


def pinset(bot, update):
    mes = update.message
    mes1 = mes.text.split("_")
    request = "UPDATE guild_chats SET enabled = %s WHERE guild_chat_id = %s"
    cursor.execute(request, (mes1[2], mes1[1]))
    conn.commit()
    bot.send_message(chat_id=update.message.chat_id, text='Выполнено')


def pinpin(bot, update):
    mes = update.message
    mes1 = mes.text.split("_")
    #print(mes1[0], mes1[1], mes1[2])
    request = "UPDATE guild_chats SET pin = %s WHERE guild_chat_id = %s"
    cursor.execute(request, (mes1[2], mes1[1]))
    conn.commit()
    bot.send_message(chat_id=update.message.chat_id, text='Выполнено')

def pinmute(bot, update):
    mes = update.message
    mes1 = mes.text.split("_")
    request = "UPDATE guild_chats SET disable_notification = %s WHERE guild_chat_id = %s"
    cursor.execute(request, (mes1[2], mes1[1]))
    conn.commit()
    bot.send_message(chat_id=update.message.chat_id, text='Выполнено')

def pindivision(bot, update):
    mes = update.message
    mes1 = mes.text.split("_")
    division = mes.text.partition(' ')[2]
    request = "UPDATE guild_chats SET division = %s WHERE guild_chat_id = %s"
    cursor.execute(request, (division, mes1[1]))
    conn.commit()
    bot.send_message(chat_id=update.message.chat_id, text='Выполнено')

def pult(bot, update):
    PultMarkup = build_pult(castles)
    bot.send_message(chat_id = update.message.chat_id,
                     text = "{0}".format(datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)),
                     reply_markup = PultMarkup)

def pult_callback(bot, update):
    data = update.callback_query.data
    if data == "ps":
        pult_send(bot, update)
    if data.find("pc") == 0:
        pult_castles_callback(bot, update)
        return

def pult_send(bot, update):
    time_begin = datetime.datetime.now()
    global order_id
    mes = update.callback_query.message
    target = pult_status.get("target")
    if target == -1:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Необходимо выбрать цель")
        return
    castle_target = castles[target]
    defense_home = pult_status.get("defense_home")
    response = "⚔️{0}\n🛡{1}\n".format(castle_target, "?" if defense_home else castle_target)
    orders_sent = 0
    for chat in order_chats:
        bot.send_order(order_id=order_id, chat_id=chat[0], response=response, pin=chat[1], notification=not chat[2])
        orders_sent += 1
    response = ""
    orders_OK = 0
    orders_failed = 0
    while orders_OK + orders_failed < orders_sent:
        current = order_backup_queue.get()
        if current.order_id == order_id:
            if current.OK:
                orders_OK += 1
            else:
                orders_failed += 1
                response += current.text
        else:
            order_backup_queue.put(current)
            logging.warning("Incorrect order_id, received {0}, now it is {1}".format(current, order_id))

    order_id += 1
    time_end = datetime.datetime.now()
    time_delta = time_end - time_begin
    stats = "Выполнено в <b>{0}</b>, отправлено в <b>{1}</b> чатов, " \
            "ошибка при отправке в <b>{2}</b> чатов, " \
            "рассылка заняла <b>{3}</b>\n\n".format(time.ctime(), orders_OK, orders_failed, time_delta) + response
    bot.send_message(chat_id=mes.chat_id, text=stats, parse_mode='HTML')
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id)



def pult_castles_callback(bot, update):
    mes = update.callback_query.message
    new_target = int(update.callback_query.data[2])
    new_markup = rebuild_pult("change_target", new_target)
    pult_status.update({ "target" : new_target })
    try:
        bot.editMessageReplyMarkup(chat_id=mes.chat_id, message_id=mes.message_id, reply_markup=new_markup)
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id)
    except TelegramError:
        logging.error(traceback.format_exc)

def inline_callback(bot, update):
    if update.callback_query.data.find("p") == 0:
        pult_callback(bot, update)
        return



def recashe_order_chats():
    logging.info("Recaching chats...")
    order_chats.clear()
    request = "select chat_id, pin, disable_notification from guild_chats where enabled = '1'"
    cursor.execute(request)
    row = cursor.fetchone()
    while row:
        current = []
        for elem in row:
            current.append(elem)
        order_chats.append(current)
        row = cursor.fetchone()
    logging.info("Recashing done")

dispatcher.add_handler(CommandHandler('⚔', attackCommand, filters=filter_is_admin))
dispatcher.add_handler(CommandHandler('pult', pult, filters=filter_is_admin))
dispatcher.add_handler(CommandHandler('menu', menu, filters=filter_is_admin))
dispatcher.add_handler(CommandHandler('add_pin', add_pin, filters=filter_is_admin))
dispatcher.add_handler(CommandHandler('pin_setup', pin_setup, filters=filter_is_admin))
dispatcher.add_handler(MessageHandler(Filters.command & filter_pinset & filter_is_admin, pinset))
dispatcher.add_handler(MessageHandler(Filters.command & filter_pinpin & filter_is_admin, pinpin))
dispatcher.add_handler(MessageHandler(Filters.command & filter_pinmute & filter_is_admin, pinmute))
dispatcher.add_handler(MessageHandler(Filters.command & filter_pindivision & filter_is_admin, pindivision))
dispatcher.add_handler(CallbackQueryHandler(inline_callback, pass_update_queue=False, pass_user_data=False))



recashe_order_chats()
updater.start_polling(clean=False)


# Останавливаем бота, если были нажаты Ctrl + C
updater.idle()
# Разрываем подключение.
conn.close()
