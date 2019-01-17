from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, BaseFilter
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Bot
from telegram.utils.request import Request

from telegram.error import (TelegramError, Unauthorized, BadRequest,
                            TimedOut, ChatMigrated, NetworkError)

import logging
import time
import datetime
import psycopg2
import threading

import sys
import multiprocessing
from multiprocessing import Queue

from work_materials.globals import *

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)

multiprocessing.log_to_stderr()
logger = multiprocessing.get_logger()
logger.setLevel(logging.INFO)


order_id = 0




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
    print("begin")

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





class Filter_pinset(BaseFilter):
    def filter(self, message):
        return 'pinset' in message.text

filter_pinset = Filter_pinset()

class Filter_pinpin(BaseFilter):
    def filter(self, message):
        return 'pinpin' in message.text

filter_pinpin = Filter_pinpin()


class Filter_pinmute(BaseFilter):
    def filter(self, message):
        return 'pinmute' in message.text

filter_pinmute = Filter_pinmute()

class Filter_pindivision(BaseFilter):
    def filter(self, message):
        return 'pindivision' in message.text

filter_pindivision = Filter_pindivision()

dispatcher.add_handler(CommandHandler('⚔', attackCommand, filters=(Filters.user(user_id=231900398)  | Filters.user(user_id = 205356091))))
dispatcher.add_handler(CommandHandler('menu', menu, filters=(Filters.user(user_id=231900398)  | Filters.user(user_id = 205356091))))
dispatcher.add_handler(CommandHandler('add_pin', add_pin, filters=Filters.user(user_id = 231900398)))
dispatcher.add_handler(CommandHandler('pin_setup', pin_setup, filters=Filters.user(user_id = 231900398)))
dispatcher.add_handler(MessageHandler(Filters.command & filter_pinset & Filters.user(user_id = 231900398), pinset))
dispatcher.add_handler(MessageHandler(Filters.command & filter_pinpin & Filters.user(user_id = 231900398), pinpin))
dispatcher.add_handler(MessageHandler(Filters.command & filter_pinmute & Filters.user(user_id = 231900398), pinmute))
dispatcher.add_handler(MessageHandler(Filters.command & filter_pindivision & Filters.user(user_id = 231900398), pindivision))


updater.start_polling(clean=False)

"""
def updating(updater, division, cursor):
    #updater.start_polling(clean=True)
    orders = order_queues.get(division)
    data = orders.get()
    while data is not None:
        response = data.text
        order_id = data.order_id
        print("starting sending orders, division =", division)
        attack_send(updater, division, response, cursor, order_id)

        data = orders.get()

    #updater.idle()

#north_updating = multiprocessing.Process(target=updating, args=(north_updater, "north", cursor), name="North_updating")
request = Request( con_pool_size = 15, read_timeout=1.5, connect_timeout=1.5)
north_bot = Bot(token='790769244:AAHjr7pOnzEinv9nbKeoO_dbxGw6GVcHBOw', request=request)
south_bot = Bot(token='739120792:AAGMYTGwNx_kNMqq3epnaYYQfCpSFAnd0A4', request=request)
north_updating = multiprocessing.Process(target=updating, args=(north_bot, "north", cursor), name="North_updating")
north_updating.start()
south_updating = multiprocessing.Process(target=updating, args=(south_bot, "south", cursor2), name="South_updating")
south_updating.start()
#south_updater.start_polling(clean=True)
#north_updater.start_polling(clean=True)
"""

# Останавливаем бота, если были нажаты Ctrl + C
updater.idle()
# Разрываем подключение.
conn.close()
