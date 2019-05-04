from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackQueryHandler

from castle_files.work_materials.globals import dispatcher, updater, conn

from castle_files.work_materials.filters.profile_filters import filter_is_hero, filter_view_hero
from castle_files.work_materials.filters.report_filters import filter_is_report, filter_battle_stats
from castle_files.work_materials.filters.guild_filters import filter_edit_guild, filter_change_guild_commander, \
    filter_change_guild_chat, filter_view_guild, filter_change_guild_division, filter_remove_player
from castle_files.work_materials.filters.castle_filters import filter_central_square, filter_barracks, filter_back, \
    filter_throne_room
from castle_files.work_materials.filters.feedback_filters import filter_request_audience, filter_accept_audience, \
    filter_decline_audience, filter_request_mid_feedback, filter_send_mid_feedback, filter_reply_to_mid_feedback
from castle_files.work_materials.filters.general_filters import filter_is_pm, filter_has_access

from castle_files.bin.service_functions import cancel
from castle_files.bin.profile import hero, profile
from castle_files.bin.guild import create_guild, edit_guild, edit_guild_commander, change_guild_commander, chat_info,\
    edit_guild_chat, change_guild_chat, add, guild_info, list_guilds, edit_guild_division, change_guild_division, \
    list_players, leave_guild, change_guild_bool_state, remove_player
from castle_files.bin.castle import central_square, barracks, back, throne_room
from castle_files.bin.castle_feedback import request_king_audience, accept_king_audience, decline_king_audience, \
    request_mid_feedback, send_mid_feedback, send_reply_to_mid_request
from castle_files.bin.reports import add_report, battle_stats
from castle_files.bin.common_functions import unknown_input

from castle_files.bin.save_load_user_data import load_data, save_data
from castle_files.bin.unloading_resources import resources_monitor

from castle_files.libs.guild import Guild

import castle_files.work_materials.globals as file_globals

import threading


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Привет! Пришли мне форвард /hero из @chatwarsbot!")


def castle_bot_processing():
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('cancel', cancel, pass_user_data=True))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_is_hero, hero, pass_user_data=True))

    # Приём репортов
    dispatcher.add_handler(MessageHandler(Filters.text & filter_is_report, add_report))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_view_hero, profile))

    # Хендлеры для команд гильдий
    dispatcher.add_handler(MessageHandler(Filters.text & filter_view_guild, guild_info))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_view_guild, guild_info))

    dispatcher.add_handler(MessageHandler(Filters.command & filter_remove_player, remove_player))

    dispatcher.add_handler(CommandHandler('leave_guild', leave_guild))

    dispatcher.add_handler(MessageHandler(Filters.all & ~filter_has_access & filter_is_pm, unknown_input,
                                          pass_user_data=True))

    # Хендлеры для виртуального замка
    dispatcher.add_handler(MessageHandler(Filters.text & filter_back, back, pass_user_data=True))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_central_square, central_square, pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_barracks, barracks, pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_throne_room, throne_room, pass_user_data=True))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_request_audience, request_king_audience))
    dispatcher.add_handler(MessageHandler(Filters.command & filter_accept_audience, accept_king_audience))
    dispatcher.add_handler(MessageHandler(Filters.command & filter_decline_audience, decline_king_audience))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_request_mid_feedback, request_mid_feedback,
                                          pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.all & filter_send_mid_feedback, send_mid_feedback,
                                          pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.all & filter_reply_to_mid_feedback, send_reply_to_mid_request))

    dispatcher.add_handler(MessageHandler(Filters.all & ~filter_has_access, unknown_input, pass_user_data=True))
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

    dispatcher.add_handler(MessageHandler(Filters.command & filter_battle_stats, battle_stats))

    dispatcher.add_handler(CommandHandler('chat_info', chat_info))
    # End of the restrictions---------------------------------------------------------------------------------------

    dispatcher.add_handler(CommandHandler('add', add))

    # Хендлеры для инлайн кнопок гильдий
    dispatcher.add_handler(CallbackQueryHandler(edit_guild_commander, pattern="gccmdr_\\d+", pass_user_data=True))
    dispatcher.add_handler(CallbackQueryHandler(edit_guild_chat, pattern="gccht_\\d+", pass_user_data=True))
    dispatcher.add_handler(CallbackQueryHandler(edit_guild_division, pattern="gcdvs_\\d+", pass_user_data=True))

    # Хендлер на любые изменения булеанов в гильдиях
    dispatcher.add_handler(CallbackQueryHandler(change_guild_bool_state, pattern="gc[opn]_\\d+"))

    dispatcher.add_handler(CallbackQueryHandler(list_players, pattern="gipl_\\d+"))
    dispatcher.add_handler(CallbackQueryHandler(leave_guild, pattern="gilv_\\d+"))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_is_pm, unknown_input, pass_user_data=True))

    # Загрузка user_data с диска
    load_data()
    Guild.fill_guild_ids()
    # Запуск потоков и процессов
    processes = []
    file_globals.processing = True

    # Поток, сохраняющий user_data на диск
    save_user_data = threading.Thread(target=save_data, name="Save User Data", args=())
    save_user_data.start()
    processes.append(save_user_data)

    unloading_resources = threading.Thread(target=resources_monitor, name="Castle Unloading Resources", args=())
    unloading_resources.start()
    processes.append(unloading_resources)

    updater.start_polling(clean=False)

    updater.idle()
    file_globals.processing = False
    save_user_data.join()

    conn.close()
