from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackQueryHandler

from castle_files.work_materials.globals import dispatcher, updater, conn

from castle_files.work_materials.filters.profile_filters import filter_is_hero, filter_view_hero
from castle_files.work_materials.filters.guild_filters import filter_edit_guild, filter_change_guild_commander, \
    filter_change_guild_chat, filter_view_guild, filter_change_guild_division

from castle_files.bin.service_functions import cancel
from castle_files.bin.profile import hero, profile
from castle_files.bin.guild import create_guild, edit_guild, edit_guild_commander, change_guild_commander, chat_info,\
    edit_guild_chat, change_guild_chat, add, guild_info, list_guilds, edit_guild_division, change_guild_division, \
    list_players, leave_guild

from castle_files.bin.save_load_user_data import load_data, save_data

import castle_files.work_materials.globals as file_globals

import threading


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Привет! Пришли мне форвард /hero из @chatwarsbot!")



def castle_bot_processing():
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('cancel', cancel, pass_user_data=True))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_is_hero, hero, pass_user_data=True))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_view_hero, profile))

    # Хендлеры для команд гильдий
    dispatcher.add_handler(MessageHandler(Filters.text & filter_view_guild, guild_info))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_view_guild, guild_info))

    dispatcher.add_handler(CommandHandler('leave_guild', leave_guild))

    # Restricted access---------------------------------------------------------------------------------------------
    dispatcher.add_handler(CommandHandler('create_guild', create_guild))
    dispatcher.add_handler(CommandHandler('list_guilds', list_guilds))
    dispatcher.add_handler(MessageHandler(Filters.command & filter_edit_guild, edit_guild))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_change_guild_commander, change_guild_commander,
                                          pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_change_guild_chat, change_guild_chat,
                                          pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_change_guild_division, change_guild_division,
                                          pass_user_data=True))

    dispatcher.add_handler(CommandHandler('chat_info', chat_info))
    # End of the restrictions---------------------------------------------------------------------------------------

    dispatcher.add_handler(CommandHandler('add', add))

    # Хендлеры для инлайн кнопок гильдий
    dispatcher.add_handler(CallbackQueryHandler(edit_guild_commander, pattern="gccmdr_\\d+", pass_user_data=True))
    dispatcher.add_handler(CallbackQueryHandler(edit_guild_chat, pattern="gccht_\\d+", pass_user_data=True))
    dispatcher.add_handler(CallbackQueryHandler(edit_guild_division, pattern="gcdvs_\\d+", pass_user_data=True))

    dispatcher.add_handler(CallbackQueryHandler(list_players, pattern="gipl_\\d+"))
    dispatcher.add_handler(CallbackQueryHandler(leave_guild, pattern="gilv_\\d+"))

    # Загрузка user_data с диска
    load_data()
    # Запуск потоков и процессов
    processes = []
    file_globals.processing = True

    # Поток, сохраняющий user_data на диск
    save_user_data = threading.Thread(target=save_data, name="Save User Data", args=())
    save_user_data.start()
    processes.append(save_user_data)

    updater.start_polling(clean=False)

    updater.idle()
    file_globals.processing = False
    save_user_data.join()

    conn.close()
