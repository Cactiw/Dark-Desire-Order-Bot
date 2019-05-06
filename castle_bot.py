from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackQueryHandler

from castle_files.work_materials.globals import dispatcher, updater, conn

from castle_files.work_materials.filters.profile_filters import filter_is_hero, filter_view_hero, filter_view_profile, \
    filter_is_profile, filter_not_registered, filter_forbidden
from castle_files.work_materials.filters.report_filters import filter_is_report, filter_battle_stats
from castle_files.work_materials.filters.guild_filters import filter_edit_guild, filter_change_guild_commander, \
    filter_change_guild_chat, filter_view_guild, filter_change_guild_division, filter_remove_player, filter_delete_guild
from castle_files.work_materials.filters.castle_filters import filter_central_square, filter_barracks, filter_back, \
    filter_throne_room, filter_castle_gates, filter_guide_signs, filter_not_constructed, filter_watch_portraits, \
    filter_king_cabinet, filter_add_general, filter_adding_general, filter_remove_general, \
    filter_request_change_castle_message, filter_change_castle_message, filter_headquarters, \
    filter_request_guild_message_notify, filter_send_guild_message_notify, filter_change_debrief, \
    filter_request_change_debrief
from castle_files.work_materials.filters.feedback_filters import filter_request_audience, filter_accept_audience, \
    filter_decline_audience, filter_request_mid_feedback, filter_send_mid_feedback, filter_reply_to_mid_feedback, \
    filter_restrict_feedback, filter_unrestrict_feedback
from castle_files.work_materials.filters.castle_duty_filters import filter_begin_duty, filter_end_duty, \
    filter_request_duty_feedback, filter_send_duty_feedback, filter_reply_to_duty_feedback, filter_ban_in_duty_chat
from castle_files.work_materials.filters.general_filters import filter_is_pm, filter_has_access

from castle_files.bin.service_functions import cancel, fill_allowed_list
from castle_files.bin.profile import hero, profile, view_profile, add_class_from_player
from castle_files.bin.guild import create_guild, edit_guild, edit_guild_commander, change_guild_commander, chat_info,\
    edit_guild_chat, change_guild_chat, add, guild_info, list_guilds, edit_guild_division, change_guild_division, \
    list_players, leave_guild, change_guild_bool_state, remove_player, request_delete_guild, delete_guild, \
    cancel_delete_guild
from castle_files.bin.castle import central_square, barracks, back, throne_room, castle_gates, guide_signs, \
    not_constructed, watch_portraits, fill_mid_players, king_cabinet, add_general, adding_general, remove_general, \
    request_change_castle_message, change_castle_message, headquarters, \
    request_guild_message_notify, send_guild_message_notify, change_rp, request_change_debrief, change_debrief
from castle_files.bin.castle_feedback import request_king_audience, accept_king_audience, decline_king_audience, \
    request_mid_feedback, send_mid_feedback, send_reply_to_mid_request, restrict_feedback, unrestrict_feedback
from castle_files.bin.castle_duty import begin_duty, end_duty, request_duty_feedback, send_duty_feedback, \
    send_reply_to_duty_request, check_ban_in_duty_chat, ask_to_revoke_duty_link, revoke_duty_link
from castle_files.bin.reports import add_report, battle_stats
from castle_files.bin.common_functions import unknown_input

from castle_files.bin.save_load_user_data import load_data, save_data
from castle_files.bin.unloading_resources import resources_monitor

from castle_files.libs.guild import Guild

import castle_files.work_materials.globals as file_globals

import threading


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Привет! Пришли мне форвард /hero из @chatwarsbot!")


def skip(bot, update):
    return


def castle_bot_processing():
    dispatcher.add_handler(MessageHandler(Filters.all & filter_forbidden, skip))  # Отключение регистрации
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('cancel', cancel, pass_user_data=True))

    dispatcher.add_handler(CommandHandler('change_rp', change_rp, pass_user_data=True))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_is_hero, hero, pass_user_data=True))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_is_profile, add_class_from_player))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_not_registered, unknown_input, pass_user_data=True))

    # Приём репортов
    dispatcher.add_handler(MessageHandler(Filters.text & filter_is_report, add_report))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_view_hero, profile))

    # Хендлеры для команд гильдий
    dispatcher.add_handler(MessageHandler(Filters.text & filter_view_guild, guild_info))

    dispatcher.add_handler(MessageHandler(Filters.command & filter_view_profile, view_profile))
    dispatcher.add_handler(MessageHandler(Filters.command & filter_remove_player, remove_player))

    dispatcher.add_handler(CommandHandler('leave_guild', leave_guild))

    dispatcher.add_handler(CommandHandler('add', add))

    # Хендлеры для виртуального замка
    dispatcher.add_handler(MessageHandler(Filters.text & filter_back, back, pass_user_data=True))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_not_constructed, not_constructed))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_guide_signs, guide_signs))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_barracks, barracks, pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_throne_room, throne_room, pass_user_data=True))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_watch_portraits, watch_portraits))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_headquarters, headquarters, pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_request_change_debrief,
                                          request_change_debrief, pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_change_debrief, change_debrief, pass_user_data=True))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_request_guild_message_notify,
                                          request_guild_message_notify, pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.all & filter_send_guild_message_notify,
                                          send_guild_message_notify, pass_user_data=True))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_king_cabinet, king_cabinet, pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_add_general, add_general, pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_adding_general, adding_general, pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.command & filter_remove_general, remove_general,
                                          pass_user_data=False))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_request_change_castle_message,
                                          request_change_castle_message, pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_change_castle_message, change_castle_message,
                                          pass_user_data=True))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_begin_duty, begin_duty, pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_end_duty, end_duty, pass_user_data=True))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_request_duty_feedback, request_duty_feedback,
                                          pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.all & filter_send_duty_feedback, send_duty_feedback,
                                          pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.all & filter_reply_to_duty_feedback, send_reply_to_duty_request))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_request_audience, request_king_audience))
    dispatcher.add_handler(MessageHandler(Filters.command & filter_accept_audience, accept_king_audience))
    dispatcher.add_handler(MessageHandler(Filters.command & filter_decline_audience, decline_king_audience))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_request_mid_feedback, request_mid_feedback,
                                          pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.all & filter_send_mid_feedback, send_mid_feedback,
                                          pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.all & filter_reply_to_mid_feedback, send_reply_to_mid_request))

    dispatcher.add_handler(MessageHandler(Filters.command & filter_restrict_feedback, restrict_feedback))
    dispatcher.add_handler(MessageHandler(Filters.command & filter_unrestrict_feedback, unrestrict_feedback))

    dispatcher.add_handler(MessageHandler(Filters.all & filter_ban_in_duty_chat, check_ban_in_duty_chat))

    # Хендлеры далее специально ниже всех остальных, ибо невозможно проверять статус на эту исполнение этих команд
    dispatcher.add_handler(MessageHandler(Filters.text & filter_castle_gates, castle_gates, pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_central_square, central_square, pass_user_data=True))

    dispatcher.add_handler(MessageHandler(Filters.all & ~filter_has_access, unknown_input, pass_user_data=True))
    # Restricted access---------------------------------------------------------------------------------------------
    dispatcher.add_handler(CommandHandler('create_guild', create_guild))
    dispatcher.add_handler(CommandHandler('list_guilds', list_guilds))
    dispatcher.add_handler(MessageHandler(Filters.command & filter_edit_guild, edit_guild))
    dispatcher.add_handler(MessageHandler(Filters.command & filter_delete_guild, request_delete_guild))
    dispatcher.add_handler(CallbackQueryHandler(delete_guild, pattern="g_delete_confirm_\\d+"))
    dispatcher.add_handler(CallbackQueryHandler(cancel_delete_guild, pattern="g_delete_cancel_\\d+"))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_change_guild_commander, change_guild_commander,
                                          pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_change_guild_chat, change_guild_chat,
                                          pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_change_guild_division, change_guild_division,
                                          pass_user_data=True))

    dispatcher.add_handler(MessageHandler(Filters.command & filter_battle_stats, battle_stats))

    dispatcher.add_handler(CommandHandler('chat_info', chat_info))
    dispatcher.add_handler(CommandHandler('revoke_duty_link', revoke_duty_link))
    # End of the restrictions---------------------------------------------------------------------------------------

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
    fill_mid_players()
    fill_allowed_list()
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
    ask_to_revoke_duty_link()

    updater.idle()
    file_globals.processing = False
    save_user_data.join()

    conn.close()
