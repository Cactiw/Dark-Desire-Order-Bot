#! /usr/bin/env python3.7
# coding=utf-8
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackQueryHandler


from order_files.work_materials.filters.pin_setup_filters import *
from order_files.work_materials.filters.service_filters import *
from order_files.work_materials.filters.pult_filters import filter_remove_order, filter_remove_variant


from order_files.bin.pult_callback import pult, pult_callback, pult_variants, send_variant, remove_variant, \
    plan_battle_jobs
from order_files.bin.order import attackCommand, menu, remove_order, refill_deferred_orders

from order_files.bin.guild_chats import add_pin, pin_setup, recashe_order_chats, pindivision, pinmute, pinpin, pinset

from order_files.bin.castle_update_monitor import castle_update_monitor

from order_files.work_materials.globals import dispatcher, updater, conn, LOGS_CHAT_ID, MAX_MESSAGE_LENGTH, ServerIP, \
    Production_order_token, CONNECT_TYPE

from castle_files.bin.castle import fill_mid_players

from globals import update_request_queue

import order_files.work_materials.globals as globals

import threading
import time
import logging

console = logging.StreamHandler()
console.setLevel(logging.INFO)

log_file = logging.FileHandler(filename='order_error.log', mode='a')
log_file.setLevel(logging.ERROR)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO, handlers=[log_file, console])


# ------------------------------------------------------------------------------------------------------

def send_logs(bot, update):
    for logs_to_send in [globals.logs[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(globals.logs), MAX_MESSAGE_LENGTH)]:
        bot.sync_send_message(chat_id=update.message.chat_id, text=logs_to_send)


def inline_callback(bot, update):
    if update.callback_query.data.find("p") == 0:
        pult_callback(bot, update)
        return


def not_allowed(bot, update):
    return
    mes = update.message
    title = update.message.chat.title
    if title is None:
        title = update.message.chat.username
    if (mes.text and '@Rock_Centre_Order_bot' in mes.text) or mes.chat_id > 0:
        bot.send_message(
            chat_id=admin_ids[0],
            text="Несанкционированная попытка доступа, от @{0}, telegram id = <b>{1}</b>,\n"
                    "Название чата - <b>{2}</b>, chat id = <b>{3}</b>".format(mes.from_user.username, mes.from_user.id,
                                                                             title, mes.chat_id), parse_mode='HTML')


def order_bot_processing():
    # dispatcher.add_handler(CommandHandler('add_pin', add_pin, filters=filter_is_admin))
    dispatcher.add_handler(MessageHandler(~(filter_super_admin | filter_djedy) & ~(filter_chat_allowed & filter_is_admin), not_allowed))
    # dispatcher.add_handler(CommandHandler('⚔', attackCommand, filters=filter_is_admin))
    dispatcher.add_handler(CommandHandler('pult', pult, filters=filter_is_admin))
    dispatcher.add_handler(CommandHandler('order', pult, filters=filter_is_admin))
    dispatcher.add_handler(CommandHandler('variant', pult, filters=filter_is_admin))
    dispatcher.add_handler(CommandHandler('pult_variants', pult_variants, filters=filter_is_admin))
    dispatcher.add_handler(CommandHandler('logs', send_logs, filters=filter_is_admin))
    dispatcher.add_handler(CommandHandler('menu', menu, filters=filter_is_admin))
    dispatcher.add_handler(CommandHandler('pin_setup', pin_setup, filters=filter_is_admin))
    dispatcher.add_handler(MessageHandler(Filters.command & filter_remove_order & filter_is_admin, remove_order))
    dispatcher.add_handler(MessageHandler(Filters.command & filter_remove_variant & filter_is_admin, remove_variant))
    # dispatcher.add_handler(MessageHandler(Filters.command & filter_pinset & filter_is_admin, pinset))
    # dispatcher.add_handler(MessageHandler(Filters.command & filter_pinpin & filter_is_admin, pinpin))
    # dispatcher.add_handler(MessageHandler(Filters.command & filter_pinmute & filter_is_admin, pinmute))
    # dispatcher.add_handler(MessageHandler(Filters.command & filter_pindivision & filter_is_admin, pindivision))

    dispatcher.add_handler(CallbackQueryHandler(send_variant, pattern="var_send_\\d+"))
    dispatcher.add_handler(CallbackQueryHandler(inline_callback, pass_update_queue=False, pass_user_data=False))

    recashe_order_chats()
    refill_deferred_orders()
    # Необходимо подождать, пока другой процесс не завершит работу с локациями
    time.sleep(1)
    fill_mid_players(other_process=True)
    plan_battle_jobs()

    processes = []

    """
    Добавление тестовых чатов в бд
    test_chat_ids = [-1001419462057, -1001230820040, -1001487614244, -1001477072492, -1001476724068, -1001475739761,
                     -1001435026865, -1001430784849, -1001412038190, -1001390152554, -1001368035955, -1001348741075,
                     -1001283912560, -1001282019466, -1001272172746, -1001236826600, -1001217590373, -1001220824226,
                     -1001215437199, -1001196550784, -1001186436424, -1001177668090, -1001165412104, -1001159542230,
                     -1001144095371, -1001475801291, -1001357874112, -1001468227123, -1001239921467, -1001218916668,
                     -1001404335288, -1001230615424, -1001295507776, -1001256515324, -1001490739745, -1001263667429,
                     -1001246220946, -1001270092742]
    tmp_cursor = conn.cursor()
    for i, chat_id in enumerate(test_chat_ids):
        request = "insert into guilds(guild_tag, chat_id) values (%s, %s)"
        tmp_cursor.execute(request, (str(i), chat_id))
    """

    update_monitor = threading.Thread(target=castle_update_monitor, name="Order Database Update Monitor")
    # update_monitor.start()
    processes.append(update_monitor)
    globals.bot_castle.start()

    if CONNECT_TYPE == 'webhook':
        updater.start_webhook(listen='0.0.0.0',
                              port=443,
                              url_path=Production_order_token,
                              key='./private.key',
                              cert='./cert.pem',
                              webhook_url='https://{}:443/{}'.format(ServerIP, Production_order_token))
    else:
        updater.start_polling(clean=False)

    # Останавливаем бота, если были нажаты Ctrl + C
    updater.idle()
    if globals.logs != "":
        for logs_to_send in [globals.logs[i:i+MAX_MESSAGE_LENGTH] for i in range(0, len(globals.logs), MAX_MESSAGE_LENGTH)]:
            dispatcher.bot.sync_send_message(chat_id=LOGS_CHAT_ID, text=logs_to_send)
    # Разрываем подключение.
    conn.close()
    update_request_queue.put(None)
    globals.bot_castle.stop()


if __name__ == "__main__":
    order_bot_processing()
