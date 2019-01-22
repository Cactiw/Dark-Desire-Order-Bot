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
from work_materials.filters.pult_filters import filter_remove_order

from libs.pult import build_pult, rebuild_pult
from libs.order import DeferredOrder

from bin.order import *
from bin.pult_callback import *
from bin.guild_chats import *

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

multiprocessing.log_to_stderr()
logger = multiprocessing.get_logger()
logger.setLevel(logging.INFO)



def inline_callback(bot, update):
    if update.callback_query.data.find("p") == 0:
        pult_callback(bot, update)
        return





dispatcher.add_handler(CommandHandler('⚔', attackCommand, filters=filter_is_admin))
dispatcher.add_handler(CommandHandler('pult', pult, filters=filter_is_admin))
dispatcher.add_handler(CommandHandler('menu', menu, filters=filter_is_admin))
dispatcher.add_handler(CommandHandler('add_pin', add_pin, filters=filter_is_admin))
dispatcher.add_handler(CommandHandler('pin_setup', pin_setup, filters=filter_is_admin))
dispatcher.add_handler(MessageHandler(Filters.command & filter_remove_order & filter_is_admin, remove_order))
dispatcher.add_handler(MessageHandler(Filters.command & filter_pinset & filter_is_admin, pinset))
dispatcher.add_handler(MessageHandler(Filters.command & filter_pinpin & filter_is_admin, pinpin))
dispatcher.add_handler(MessageHandler(Filters.command & filter_pinmute & filter_is_admin, pinmute))
dispatcher.add_handler(MessageHandler(Filters.command & filter_pindivision & filter_is_admin, pindivision))
dispatcher.add_handler(CallbackQueryHandler(inline_callback, pass_update_queue=False, pass_user_data=False))



recashe_order_chats()
refill_deferred_orders()
updater.start_polling(clean=False)


# Останавливаем бота, если были нажаты Ctrl + C
updater.idle()
# Разрываем подключение.
conn.close()
