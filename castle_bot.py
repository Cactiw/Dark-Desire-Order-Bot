from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackQueryHandler

from castle_files.work_materials.globals import dispatcher, updater, conn

from castle_files.work_materials.filters.profile_filters import filter_is_hero, filter_view_hero, filter_view_profile, \
    filter_is_profile, filter_not_registered, filter_forbidden, filter_set_class
from castle_files.work_materials.filters.mid_filters import filter_mailing_pin, filter_mailing
from castle_files.work_materials.filters.trigger_filters import filter_is_trigger
from castle_files.work_materials.filters.report_filters import filter_is_report, filter_battle_stats
from castle_files.work_materials.filters.stock_filters import filter_guild_stock_parts, filter_guild_stock_recipes, \
    filter_stock_withdraw, filter_guild_stock_resources
from castle_files.work_materials.filters.guild_filters import filter_edit_guild, filter_change_guild_commander, \
    filter_change_guild_chat, filter_view_guild, filter_change_guild_division, filter_remove_player, filter_delete_guild
from castle_files.work_materials.filters.guild_chat_filters import filter_guild_list
from castle_files.work_materials.filters.castle_filters import filter_central_square, filter_barracks, filter_back, \
    filter_throne_room, filter_castle_gates, filter_guide_signs, filter_not_constructed, filter_watch_portraits, \
    filter_king_cabinet, filter_add_general, filter_adding_general, filter_remove_general, \
    filter_request_change_castle_message, filter_change_castle_message, filter_headquarters, \
    filter_request_guild_message_notify, filter_send_guild_message_notify, filter_change_debrief, \
    filter_request_change_debrief
from castle_files.work_materials.filters.technical_tower_filters import filter_technical_tower, filter_my_cabinet, \
    filter_request_change_update_message, filter_change_update_message, filter_request_bot_guild_message_notify, \
    filter_send_bot_guild_message_notify, filter_update_history
from castle_files.work_materials.filters.feedback_filters import filter_request_audience, filter_accept_audience, \
    filter_decline_audience, filter_request_mid_feedback, filter_send_mid_feedback, filter_reply_to_mid_feedback, \
    filter_restrict_feedback, filter_unrestrict_feedback
from castle_files.work_materials.filters.castle_duty_filters import filter_begin_duty, filter_end_duty, \
    filter_request_duty_feedback, filter_send_duty_feedback, filter_reply_to_duty_feedback, filter_ban_in_duty_chat
from castle_files.work_materials.filters.trade_union_filters import filter_trade_union, filter_union_list, \
    filter_need_to_ban_in_union_chat, filter_split_union
from castle_files.work_materials.filters.general_filters import filter_is_pm, filter_has_access, filter_is_merc

from castle_files.bin.service_functions import cancel, fill_allowed_list
from castle_files.bin.profile import hero, profile, view_profile, add_class_from_player, update_ranger_class_skill_lvl
from castle_files.bin.mid import mailing_pin, mailing, plan_battle_jobs
from castle_files.bin.trigger import add_trigger, remove_trigger, triggers, send_trigger, fill_triggers_lists, \
    info_trigger, replace_trigger
from castle_files.bin.stock import guild_parts, guild_recipes, send_withdraw, set_withdraw_res, withdraw_resources
from castle_files.bin.guild import create_guild, edit_guild, edit_guild_commander, change_guild_commander, chat_info,\
    edit_guild_chat, change_guild_chat, add, guild_info, list_guilds, edit_guild_division, change_guild_division, \
    list_players, leave_guild, change_guild_bool_state, remove_player, request_delete_guild, delete_guild, \
    cancel_delete_guild, add_assistant, del_assistant, assistants, guild_reports, guild_setting, edit_guild_withdraw
from castle_files.bin.guild_chats import notify_guild_attack, notify_guild_to_battle, parse_stats, mute
from castle_files.bin.castle import central_square, barracks, back, throne_room, castle_gates, guide_signs, \
    not_constructed, watch_portraits, fill_mid_players, king_cabinet, add_general, adding_general, remove_general, \
    request_change_castle_message, change_castle_message, headquarters, \
    request_guild_message_notify, send_guild_message_notify, change_rp, request_change_debrief, change_debrief
from castle_files.bin.technical_tower import technical_tower, my_cabinet, request_change_update_message, \
    change_update_message, request_bot_guild_message_notify, send_bot_guild_message_notify, update_history, \
    change_update_history
from castle_files.bin.castle_feedback import request_king_audience, accept_king_audience, decline_king_audience, \
    request_mid_feedback, send_mid_feedback, send_reply_to_mid_request, restrict_feedback, unrestrict_feedback
from castle_files.bin.castle_duty import begin_duty, end_duty, request_duty_feedback, send_duty_feedback, \
    send_reply_to_duty_request, check_ban_in_duty_chat, ask_to_revoke_duty_link, revoke_duty_link
from castle_files.bin.trade_unions import add_union, union_list, add_union_chat_id, fill_union_chats, check_and_kick, \
    print_union_players, clear_union_list, view_guild_players_in_union, add_to_union_user_id, view_guild_unions, \
    count_union_stats, add_union_assistant, del_union_assistant, top_union_stats, split_union
from castle_files.bin.reports import add_report, battle_stats

from castle_files.bin.drop_data import drop_table  # ReiRose LTD 2019

from castle_files.bin.telethon_script import script_work
from castle_files.bin.common_functions import unknown_input

from castle_files.bin.save_load_user_data import load_data, save_data
from castle_files.bin.unloading_resources import resources_monitor

from castle_files.libs.guild import Guild

import castle_files.work_materials.globals as file_globals


import threading
import multiprocessing


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Привет! Пришли мне форвард /hero из @chatwarsbot!")


def skip(bot, update):
    return


def castle_bot_processing():
    # dispatcher.add_handler(MessageHandler(Filters.all & filter_forbidden, skip))  # Отключение регистрации
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('cancel', cancel, pass_user_data=True))

    dispatcher.add_handler(CommandHandler('change_rp', change_rp, pass_user_data=True))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_is_hero, hero, pass_user_data=True))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_is_profile, add_class_from_player))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_set_class, update_ranger_class_skill_lvl))

    # Профсоюзы
    dispatcher.add_handler(MessageHandler(Filters.text & filter_trade_union, add_union))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_union_list, union_list))
    dispatcher.add_handler(CommandHandler('set_union_chat', add_union_chat_id))
    dispatcher.add_handler(CommandHandler('clear_union_list', clear_union_list))
    dispatcher.add_handler(CommandHandler('union_list', print_union_players))
    dispatcher.add_handler(CommandHandler('union_stats', count_union_stats))
    dispatcher.add_handler(CommandHandler('guild_union_players', view_guild_players_in_union))
    dispatcher.add_handler(CommandHandler('guild_unions', view_guild_unions))
    dispatcher.add_handler(CommandHandler('add_to_union_user_id', add_to_union_user_id))
    dispatcher.add_handler(CommandHandler('add_union_assistant', add_union_assistant))
    dispatcher.add_handler(CommandHandler('del_union_assistant', del_union_assistant))
    dispatcher.add_handler(CommandHandler('top_union_attack', top_union_stats))
    dispatcher.add_handler(CommandHandler('top_union_defense', top_union_stats))
    dispatcher.add_handler(MessageHandler(Filters.command & filter_split_union, split_union))
    dispatcher.add_handler(MessageHandler(Filters.all & filter_need_to_ban_in_union_chat, check_and_kick))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_not_registered, unknown_input, pass_user_data=True))

    # Приём репортов
    dispatcher.add_handler(MessageHandler(Filters.text & filter_is_report, add_report))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_view_hero, profile))

    # Всякие команды в личке у бота
    dispatcher.add_handler(MessageHandler(Filters.text & filter_guild_stock_parts, guild_parts, pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_guild_stock_recipes, guild_recipes,
                                          pass_user_data=True))

    dispatcher.add_handler(CommandHandler('set_withdraw_res', set_withdraw_res, pass_user_data=True, pass_args=True))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_guild_stock_resources, withdraw_resources,
                                          pass_user_data=True))

    # Хендлеры для команд гильдий
    dispatcher.add_handler(MessageHandler(Filters.text & filter_view_guild, guild_info))

    dispatcher.add_handler(MessageHandler(Filters.command & filter_view_profile, view_profile))
    dispatcher.add_handler(MessageHandler(Filters.command & filter_remove_player, remove_player))

    dispatcher.add_handler(CommandHandler('leave_guild', leave_guild))

    dispatcher.add_handler(CommandHandler('add', add))
    dispatcher.add_handler(CommandHandler('add_assistant', add_assistant))
    dispatcher.add_handler(CommandHandler('del_assistant', del_assistant))

    dispatcher.add_handler(CommandHandler('d2', drop_table))
    dispatcher.add_handler(CommandHandler('d3', drop_table))
    dispatcher.add_handler(CommandHandler('d4', drop_table))
    dispatcher.add_handler(CommandHandler('dc', drop_table))

    dispatcher.add_handler(CommandHandler('dokument', view_profile))
    dispatcher.add_handler(CommandHandler('document', view_profile))
    dispatcher.add_handler(CommandHandler('dok', view_profile))
    dispatcher.add_handler(CommandHandler('doc', view_profile))

    # Хендлеры для триггеров
    dispatcher.add_handler(CommandHandler('create_trigger', add_trigger))
    dispatcher.add_handler(CommandHandler('create_global_trigger', add_trigger))
    dispatcher.add_handler(CommandHandler('delete_trigger', remove_trigger))
    dispatcher.add_handler(CommandHandler('triggers', triggers))
    dispatcher.add_handler(CommandHandler('info_trigger', info_trigger))
    dispatcher.add_handler(CommandHandler('replace_trigger', replace_trigger))

    # Хендлеры для чата гильдий
    dispatcher.add_handler(MessageHandler(Filters.text & filter_guild_list, notify_guild_attack))
    dispatcher.add_handler(CommandHandler('notify_guild_sleeping', notify_guild_to_battle))
    dispatcher.add_handler(CommandHandler('notify_guild_not_ready', notify_guild_to_battle))

    dispatcher.add_handler(CommandHandler('ro', mute, pass_args=True))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_stock_withdraw, send_withdraw))

    # Хендлеры для виртуального замка
    dispatcher.add_handler(MessageHandler(Filters.text & filter_back, back, pass_user_data=True))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_not_constructed, not_constructed))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_guide_signs, guide_signs))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_barracks, barracks, pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_throne_room, throne_room, pass_user_data=True))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_technical_tower, technical_tower, pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_my_cabinet, my_cabinet, pass_user_data=True))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_request_bot_guild_message_notify,
                                          request_bot_guild_message_notify, pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_send_bot_guild_message_notify,
                                          send_bot_guild_message_notify, pass_user_data=True))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_request_change_update_message,
                                          request_change_update_message, pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.text & filter_change_update_message,
                                          change_update_message, pass_user_data=True))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_update_history, update_history))

    dispatcher.add_handler(CallbackQueryHandler(change_update_history, pattern="uh[lr]_\\d+"))

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

    dispatcher.add_handler(MessageHandler((Filters.command | Filters.text) & filter_is_trigger, send_trigger))

    dispatcher.add_handler(MessageHandler(Filters.all & ~filter_has_access & ~filter_is_merc, unknown_input,
                                          pass_user_data=True))
    # Restricted access---------------------------------------------------------------------------------------------
    dispatcher.add_handler(CommandHandler('list_guilds', list_guilds))
    dispatcher.add_handler(MessageHandler(Filters.command & filter_battle_stats, battle_stats))
    dispatcher.add_handler(CommandHandler('chat_info', chat_info))

    dispatcher.add_handler(MessageHandler(Filters.all & filter_is_merc, unknown_input, pass_user_data=True))
    dispatcher.add_handler(CommandHandler('create_guild', create_guild))

    dispatcher.add_handler(MessageHandler(Filters.command & filter_mailing_pin, mailing_pin))
    dispatcher.add_handler(MessageHandler(Filters.command & filter_mailing, mailing))

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

    dispatcher.add_handler(CommandHandler('revoke_duty_link', revoke_duty_link))
    # End of the restrictions---------------------------------------------------------------------------------------

    # Хендлеры для инлайн кнопок гильдий
    dispatcher.add_handler(CallbackQueryHandler(edit_guild_commander, pattern="gccmdr_\\d+", pass_user_data=True))
    dispatcher.add_handler(CallbackQueryHandler(edit_guild_chat, pattern="gccht_\\d+", pass_user_data=True))
    dispatcher.add_handler(CallbackQueryHandler(edit_guild_division, pattern="gcdvs_\\d+", pass_user_data=True))

    # Хендлер на любые изменения булеанов в гильдиях
    dispatcher.add_handler(CallbackQueryHandler(change_guild_bool_state, pattern="gc[opn]_\\d+"))

    dispatcher.add_handler(CallbackQueryHandler(list_players, pattern="gipl_\\d+"))
    dispatcher.add_handler(CallbackQueryHandler(assistants, pattern="giass_\\d+"))
    dispatcher.add_handler(CallbackQueryHandler(guild_reports, pattern="girep_\\d+"))
    dispatcher.add_handler(CallbackQueryHandler(leave_guild, pattern="gilv_\\d+"))

    dispatcher.add_handler(CallbackQueryHandler(guild_setting, pattern="giset_\\d+"))
    dispatcher.add_handler(CallbackQueryHandler(edit_guild_withdraw, pattern="gswith_\\d+"))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_is_pm, unknown_input, pass_user_data=True))

    # Загрузка user_data с диска
    load_data()
    Guild.fill_guild_ids()
    fill_mid_players()
    fill_allowed_list()
    fill_triggers_lists()
    plan_battle_jobs()
    fill_union_chats()
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

    telethon_script = multiprocessing.Process(target=script_work, name="Telethon Parse Channels", args=())
    telethon_script.start()
    processes.append(telethon_script)

    parse_stats_pr = threading.Thread(target=parse_stats, name="Stats Parse")
    parse_stats_pr.start()
    processes.append(parse_stats_pr)

    updater.start_polling(clean=False)
    ask_to_revoke_duty_link()

    updater.idle()
    file_globals.processing = False
    save_user_data.join()

    conn.close()
