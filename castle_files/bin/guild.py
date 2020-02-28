"""
В этом модуле находятся все функции для работы с гильдиями как с сущностями: создание, изменение и любые другие
операции с гильдиями, и игроками в них
"""
from castle_files.libs.guild import Guild
from castle_files.libs.player import Player
from castle_files.libs.bot_async_messaging import MAX_MESSAGE_LENGTH

from castle_files.bin.academy import change_headmaster
from castle_files.bin.service_functions import check_access
from castle_files.bin.reports import count_battle_id, count_battle_time

from castle_files.bin.buttons import get_edit_guild_buttons, get_delete_guild_buttons, get_view_guild_buttons, \
    get_guild_settings_buttons, get_guild_inline_buttons


from castle_files.work_materials.globals import dispatcher, cursor, conn, SUPER_ADMIN_ID, classes_to_emoji

from order_files.work_materials.pult_constants import divisions as divisions_const

from telegram.ext.dispatcher import run_async
from telegram.error import TelegramError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import logging
import re

GUILD_ROWS_ON_PAGE = 3


# Создание новой гильдии
def create_guild(bot, update):
    guild_tag = update.message.text.partition(' ')[2]
    if len(guild_tag) <= 0 or len(guild_tag) > 10:
        bot.send_message(chat_id=update.message.chat_id, text="Неверный синтаксис. Укажите тэг новой гильдии.")
        return
    if any(c in guild_tag for c in ['\f', '\n', '\r', '\t', '\v', ' ']):
        bot.send_message(chat_id=update.message.chat_id, text="Неверный синтаксис. "
                                                              "Тэг не должен содержать пробелы или иные разделители.")
        return
    guild = Guild.get_guild(guild_tag=guild_tag)
    if guild is not None:
        bot.send_message(chat_id=update.message.chat_id, text="Гильдия с этим тэгом уже существует!")
        return
    guild = Guild(None, guild_tag, None, None, None, None, None, None, None, None, None, None, None)
    guild.create_guild()
    bot.send_message(chat_id=update.message.chat_id, text="Гильдия успешно создана! Отредактируйте её: "
                                                          "/edit_guild_{}".format(guild.id))
    return


def guild_repair(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    guild = Guild.get_guild(player.guild)
    if guild is None:
        bot.send_message(chat_id=update.message.chat_id, text="Вы не в гильдии. Попросите командира добавить вас.")
        return
    if not guild.check_high_access(player.id):
        bot.send_message(chat_id=update.message.chat_id, text="Функция доступна только командирам и заместителям.")
        return
    response = "Игроки, которым требуется ремонт:\n"
    for pl_id in guild.members:
        pl = Player.get_player(pl_id)
        res_new = "{}<b>{}</b> - @{}\n".format(pl.castle, pl.nickname, pl.username)
        has_broken = False
        for key, eq in list(pl.equipment.items()):
            if eq is None:
                continue
            if eq.condition == "broken":
                res_new += "    {} {}\n        (<em>{}</em>)\n" \
                           "".format(eq.name, " {} ".format(eq.quality) if eq.quality else "", key)
                has_broken = True
        res_new += "\n"
        if has_broken:
            response += res_new
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')




def guilds(bot, update):
    if not check_access(update.message.from_user.id):
        return
    divisions = get_edit_divisions()
    guilds_divided = build_divisions_guilds_list(divisions)
    buttons = get_divisions_buttons(guilds_divided, 0)
    bot.send_message(chat_id=update.message.chat_id, text=get_divisions_text(guilds_divided), parse_mode='HTML',
                     reply_markup=buttons)


def get_edit_divisions():
    return divisions_const[:3]



def guilds_division_change_page(bot, update):
    if not check_access(update.callback_query.from_user.id):
        return
    mes = update.callback_query.message
    data = update.callback_query.data
    new_page = re.search("guilds_divisions_page_(\\d+)", data)
    if new_page is None:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Ошибка. Попробуйте снова.",
                                show_alert=True)
        return
    new_page = int(new_page.group(1))
    divisions = get_edit_divisions()
    guilds_divided = build_divisions_guilds_list(divisions)
    bot.editMessageText(chat_id=mes.chat_id, message_id=mes.message_id, text=get_divisions_text(guilds_divided),
                        reply_markup=get_divisions_buttons(guilds_divided, new_page), parse_mode='HTML')
    bot.answer_callback_query(callback_query_id=update.callback_query.id)


def get_divisions_buttons(guilds_divided: dict, page: int):
    buttons = []
    max_guilds_num = max(len(data.get("guilds")) for data in list(guilds_divided.values()))
    for row_num in range(GUILD_ROWS_ON_PAGE):
        buttons.append([])
        for division, guilds_info in list(guilds_divided.items()):
            guilds: [Guild] = guilds_info.get("guilds")
            try:
                guild = guilds[page * GUILD_ROWS_ON_PAGE + row_num]
                buttons[row_num].append(InlineKeyboardButton(
                    text="{}|⚔{:.1f}\\{:.1f}".format(guild.tag, guild.get_attack() / 1000., guild.get_defense() / 1000.)
                    if guild.orders_enabled else "❌{}".format(guild.tag),
                    callback_data="guilds_divisions_{}_page_{}".format(guild.id, page)))
            except IndexError:
                guild = None
                buttons[row_num].append(InlineKeyboardButton("➖", callback_data="skip"))
    if page * GUILD_ROWS_ON_PAGE < max_guilds_num:
        buttons.append([InlineKeyboardButton("➡", callback_data="guilds_divisions_page_{}".format(page + 1))])
    if page > 0:
        buttons.append([InlineKeyboardButton("⬅", callback_data="guilds_divisions_page_{}".format(page - 1))])
    return InlineKeyboardMarkup(buttons)


def get_divisions_text(guilds_divided: dict):
    DIVIDER = " "
    response = "<code>"
    for name in guilds_divided:
        response += "{:<10}{}".format(name, DIVIDER)
    response += "\n"
    stages = {"⚔️": "atk", "🛡": "def"}
    for stage_name, key in list(stages.items()):
        for division, data in list(guilds_divided.items()):
            response += "{}{:<8}{}".format(stage_name, data.get(key), DIVIDER)
        response += "\n"
    response += "</code>"
    return response


def build_divisions_guilds_list(divisions: list):
    ret = {}
    for guild_id in Guild.guild_ids:
        guild = Guild.get_guild(guild_id)
        division = guild.division if guild.division in divisions else "Нет"
        if division == "Нет":
            continue
        div_info = ret.get(division)
        if div_info is None:
            div_info = {"guilds": [], "atk": 0, "def": 0}
            ret.update({division: div_info})
        guilds = div_info.get("guilds")
        guilds.append(guild)
        if guild.orders_enabled:
            div_info.update({"atk": guild.get_attack() + div_info.get("atk", 0),
                             "def": guild.get_defense() + div_info.get("def", 0)})
    return ret


def edit_guild_inline(bot, update):
    if not check_access(update.callback_query.from_user.id):
        return
    mes = update.callback_query.message
    data = update.callback_query.data
    parse = re.search("guilds_divisions_(\\d+)_page_(\\d+)", data)
    if parse is None:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Ошибка. Попробуйте снова.",
                                show_alert=True)
        return
    guild_id, page = int(parse.group(1)), int(parse.group(2))
    guild = Guild.get_guild(guild_id)
    buttons = get_guild_inline_buttons(guild, page)
    text = get_edit_guild_text(guild)
    bot.editMessageText(chat_id=mes.chat_id, message_id=mes.message_id, text=text,
                        reply_markup=buttons, parse_mode='HTML')
    bot.answer_callback_query(callback_query_id=update.callback_query.id)


def inline_edit_guild_division(bot, update):
    if not check_access(update.callback_query.from_user.id):
        return
    divisions = get_edit_divisions()
    mes = update.callback_query.message
    data = update.callback_query.data
    parse = re.search("guild_change_division_(\\d+)_page_(\\d+)", data)
    if parse is None:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Ошибка. Попробуйте снова.",
                                show_alert=True)
        return
    guild_id, page = int(parse.group(1)), int(parse.group(2))
    guild = Guild.get_guild(guild_id)
    try:
        current = divisions.index(guild.division)
    except ValueError:
        current = len(divisions) - 1
    if current == len(divisions) - 1:
        current = -1
    current += 1
    new = divisions[current]
    guild.division = new
    guild.update_to_database()
    text = get_edit_guild_text(guild)
    buttons = get_guild_inline_buttons(guild, page)
    bot.editMessageText(chat_id=mes.chat_id, message_id=mes.message_id, text=text,
                        reply_markup=buttons, parse_mode='HTML')
    bot.answer_callback_query(callback_query_id=update.callback_query.id)





# ДОРОГАЯ ОПЕРАЦИЯ - получение (и вывод в сообщении) списка ги
# @run_async
def list_guilds(bot, update):
    response = "Список зарегистрированных в боте гильдий:\n\n"
    attack = 0
    defense = 0
    for guild_id in Guild.guild_ids:
        guild = Guild.get_guild(guild_id=guild_id)
        if guild is None:
            logging.warning("Guild is None for the id {}".format(guild_id))
            continue
        response_new = "<b>{}</b>{}\nДивизион: {}\nРедактировать: /edit_guild_{}\nУдалить: /delete_guild_{}\n" \
                       "\n".format(guild.tag, " --- " + guild.name if guild.name is not None else "",
                                   guild.division or "Не задан", guild.id, guild.id)
        response_new += "⚔: <b>{}</b>, 🛡: <b>{}</b>\n\n----------------------------------" \
                        "\n".format(guild.get_attack(), guild.get_defense())
        if len(response + response_new) > MAX_MESSAGE_LENGTH:
            bot.send_message(chat_id=update.message.chat_id, text=response, parse_mode='HTML')
            response = ""
        response += response_new
        attack += guild.get_attack()
        defense += guild.get_defense()
    response += "Всего: ⚔: <b>{}</b>, 🛡: <b>{}</b>\n Добавить гильдию: /create_guild [TAG]".format(attack, defense)
    bot.send_message(chat_id=update.message.chat_id, text=response, parse_mode='HTML')


def guild_commanders(bot, update):
    player = Player.get_player(update.message.from_user.id)
    if player is None:
        return
    guild = Guild.get_guild(player.guild)
    if not (check_access(player.id)):  # or (guild is not None and guild.check_high_access(player.id))):
        return
    response = "Список 🎖гильдий, 🎗командиров и 🎖замов:\n"
    for guild_id in Guild.guild_ids:
        guild = Guild.get_guild(guild_id=guild_id)
        if guild is None:
            logging.warning("Guild is None for the id {}".format(guild_id))
            continue
        commander = Player.get_player(guild.commander_id, notify_on_error=False)
        response_new = "<b>{}</b>{}\n🎗: @{}".format(guild.tag, " --- " + guild.name if guild.name is not None else "",
                                                    commander.username if commander is not None else "Нет")
        if guild.assistants:
            response_new += "\n🎖: "
        for player_id in guild.assistants:
            player = Player.get_player(player_id, notify_on_error=False)
            if player is None:
                continue
            response_new += "@{} ".format(player.username)
        response_new += "\n--------------------------\n"
        if len(response + response_new) > MAX_MESSAGE_LENGTH:
            bot.send_message(chat_id=update.message.chat_id, text=response, parse_mode='HTML')
            response = ""
        response += response_new
    bot.send_message(chat_id=update.message.chat_id, text=response, parse_mode='HTML')


def g_info(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    guild = Guild.get_guild(player.guild)
    guild_tag = mes.text.split()
    if len(guild_tag) == 1:
        if guild is None:
            bot.send_message(chat_id=mes.chat_id,
                             text="Вы не состоите в гильдии. Вступите в гильдию в игре и попросите "
                                  "командира добавить вас в гильдейском чате.")
            return
        requested_guild = guild
    else:
        guild_tag = guild_tag[1]
        if not (check_access(player.id) or (guild is not None and guild.check_high_access(player.id))):
            bot.send_message(chat_id=mes.chat_id,
                             text="Особист мрачно взглянул на вас. Его глаза будто пронзали насквозь.\n"
                                  "\"Не вашего уровня сведенья.\", — наконец процедил он.")
            return
        requested_guild = Guild.get_guild(guild_tag=guild_tag)
        if requested_guild is None:
            bot.send_message(chat_id=mes.chat_id, text="Гильдия не найдена")
            return
    commander = Player.get_player(requested_guild.commander_id, notify_on_error=False)
    glory, lvl, members = requested_guild.api_info.get("glory"), requested_guild.api_info.get("lvl"), \
        requested_guild.api_info.get("members")
    response = "<b>{}</b>\n{}🎗Командир: {}\n".format(
        "{} ({})".format(requested_guild.name, requested_guild.tag) if requested_guild.name is not None else
        requested_guild.tag, "🏅: <b>{}</b>, 🎖: <b>{}</b>, 👥: <b>{}</b>\n".format(lvl, glory, members) if
        all([lvl, glory, members]) else "", "<b>{}</b> (@{})".format(commander.nickname, commander.username)
        if commander is not None else "Нет")

    if guild.id == requested_guild.id:
        # Информация о своей гильдии
        if guild.assistants:
            response += "🎖Заместители: "
            for player_id in guild.assistants:
                player = Player.get_player(player_id, notify_on_error=False)
                if player is None:
                    continue
                response += "@{} ".format(player.username)
        response += "\n\n"
        stock_size, stock_limit = guild.api_info.get("stock_size"), guild.api_info.get("stock_limit")
        if stock_size is not None and stock_limit is not None:
            response += "📦Сток гильдии: <b>{}</b> / <b>{}</b>".format(stock_size, stock_limit)
    bot.send_message(chat_id=mes.from_user.id, text=response, parse_mode='HTML')


# @dispatcher.run_async # Не работает
def guild_info(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    if player is None:
        bot.send_message(chat_id=mes.chat_id, text="Игрок не найден. Отправьте /hero из @ChatWarsBot.")
        return
    if 'academy' in mes.text:
        if mes.chat_id != mes.from_user.id:
            return
        guild = Guild.get_academy()
        if player.id not in guild.members and player.id not in guild.assistants and player.id != guild.commander_id:
            return
    else:
        if player.guild is None:
            bot.send_message(chat_id=mes.chat_id,
                             text="Вы не состоите в гильдии. Вступите в гильдию в игре и попросите "
                                  "командира добавить вас в гильдейском чате.")
            return
        guild = Guild.get_guild(guild_id=player.guild)
    if guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Гильдия не найдена.")
        return
    commander = Player.get_player(guild.commander_id)
    response = "[<b>{}</b>]  {}\n".format(guild.tag, guild.name or "")
    response += "Командир: {}\n".format("@" + commander.username if commander is not None else "Не задан")
    if guild.invite_link is None:
        try:
            guild.invite_link = bot.exportChatInviteLink(guild.chat_id)
            if guild.invite_link is not None:
                guild.invite_link = guild.invite_link[22:]  # Обрезаю https://t.me/joinchat/
                guild.update_to_database()
        except TelegramError:
            pass
    response += "Чат отряда: {}, id: {}" \
                "\n{}\n".format(guild.chat_name or "Не задан",
                                "<code>{}</code>".format(guild.chat_id) if guild.chat_id is not None else "Не задан",
                                "<a href=\"{}\">Вступить</a>".format("https://t.me/joinchat/" + guild.invite_link)
                                if guild.invite_link is not None else "")

    response += "\nИгроков в гильдии: <b>{}</b>\n".format(guild.members_count)
    response += "⚔: <b>{}</b>, 🛡: <b>{}</b>\n".format(guild.get_attack(), guild.get_defense())
    buttons = get_view_guild_buttons(guild, user_id=mes.from_user.id)
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML', reply_markup=buttons)


def guild_reports(bot, update):
    if update.message is not None:
        # Сообщение с вызовом списка репортов.
        mes = update.message
        requested_player_id = mes.from_user.id
        if not check_access(mes.from_user.id):
            bot.send_message(chat_id=mes.chat_id, text="Доступ запрещён.")
            return
        try:
            guild_tag = mes.text.split()[1]
        except IndexError:
            bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис.")
            return
        guild = Guild.get_guild(guild_tag=guild_tag)
        try:
            battle_id = int(mes.text.split()[2])
        except (IndexError, ValueError):
            battle_id = count_battle_id(message=None)
    else:
        # Нажатие на кнопку "репорты" в меню гильдии.
        mes = update.callback_query.message
        data = update.callback_query.data
        requested_player_id = update.callback_query.from_user.id
        guild_id = re.search("_(\\d+)", data)
        if guild_id is None:
            bot.send_message(chat_id=mes.chat_id, text="Произошла ошибка. Начните сначала.")
            return
        guild_id = int(guild_id.group(1))
        requested_player = Player.get_player(requested_player_id)
        battle_id = count_battle_id(mes)
        if requested_player is None:
            bot.send_message(chat_id=mes.chat_id, text="Игрок не найден. Отправьте /hero из @ChatWarsBot.")
            return
        if guild_id is None:
            bot.send_message(chat_id=mes.chat_id,
                             text="Вы не состоите в гильдии. Вступите в гильдию в игре и попросите "
                                  "командира добавить вас в гильдейском чате.")
            return
        guild = Guild.get_guild(guild_id=guild_id)
    if guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Гильдия не найдена.")
        return
    if not guild.check_high_access(requested_player_id) and update.callback_query is not None:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Вы более не являетесь заместителем")
        return
    guild.sort_players_by_exp()
    response = "Статистика гильдии <b>{}</b> по битве <b>{}</b> (№ <b>{}</b>):" \
               "\n".format(guild.tag, count_battle_time(battle_id).strftime("%d/%m/%y %H:%M:%S"), battle_id)
    unsent_reports = []
    for player_id in guild.members:
        request = "select player_id, lvl, attack, additional_attack, defense, additional_defense, exp, gold, stock " \
                  "from reports where player_id = %s and battle_id = %s "
        cursor.execute(request, (player_id, battle_id,))
        row = cursor.fetchone()
        if row is None:
            unsent_reports.append(player_id)
            continue
        player = Player.get_player(row[0])
        if player is None:
            continue
        response_new = "<b>{}</b> -- @{}\n🏅:<code>{}</code> ⚔️:<code>{}</code>{} 🛡<code>{}</code>{} 🔥 <code>{}" \
                       "</code> 💰 <code>{}</code> 📦 <code>{}</code>\n\n" \
                       "".format(player.nickname, player.username, row[1], row[2],
                                 "({}{})".format("+" if row[3] > 0 else"", row[3]) if row[3] != 0 else "",
                                 row[4], "({}{})".format("+" if row[5] > 0 else"", row[5]) if row[5] != 0 else "",
                                 row[6], row[7], row[8])
        if len(response + response_new) >= MAX_MESSAGE_LENGTH:  # Превышение лимита длины сообщения
            bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
            response = ""
        response += response_new
    if response != "" and update.callback_query is not None:
        bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
        response = ""
    response += "\nНе сдали репорты:\n"
    for player_id in unsent_reports:
        player = Player.get_player(player_id)
        if player is None:
            continue
        response_new = "<b>{}</b> -- @{}\n".format(player.nickname, player.username)
        if len(response + response_new) >= MAX_MESSAGE_LENGTH:  # Превышение лимита длины сообщения
            bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
            response = ""
        response += response_new
    response += "\nВсего: <b>{}/{}</b> репортов".format(guild.members_count - len(unsent_reports), len(guild.members))
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
    if update.callback_query is not None:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id)


def get_guild_settings_text(guild):
    response = "Гильдия <b>{}</b>\n\n".format(guild.tag)
    settings = guild.settings
    if settings is None:
        settings = {}
        guild.settings = settings
    withdraw, unpin, arena_notify, battle_notify = settings.get("withdraw"), settings.get("unpin"), \
        settings.get("arena_notify"), settings.get("battle_notify")
    if withdraw is None:
        withdraw = True
        settings.update({"withdraw": withdraw})
    response += "<code>{:<18}</code> <b>{}</b>\n".format("🏷Выдача ресурсов",
                                                         "✅включена" if withdraw else "❌отключена")

    if unpin is None:
        unpin = True
        settings.update({"unpin": unpin})
    response += "<code>{:<18}</code> <b>{}</b>\n".format("📌Открепление пина",
                                                         "✅включено" if unpin else "❌отключено")

    if arena_notify is None:
        arena_notify = True
        settings.update({"arena_notify": arena_notify})
    response += "<code>{:<18}</code> <b>{}</b>\n".format("🔔Напоминалка в 12",
                                                         "✅включена" if arena_notify else "❌отключена")

    if battle_notify is None:
        battle_notify = True
        settings.update({"battle_notify": battle_notify})
    response += "<code>{:<20}</code> <b>{}</b>\n".format("⚔️️Пинги к битве",  # Не имею ни малейшего понятия, почему 20
                                                         "✅включены" if battle_notify else "❌отключены")
    return response


def guild_setting(bot, update):
    mes = update.callback_query.message
    data = update.callback_query.data
    guild_id = re.search("_(\\d+)", data)
    if guild_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Произошла ошибка. Начните сначала.")
        return
    guild_id = int(guild_id.group(1))
    requested_player = Player.get_player(update.callback_query.from_user.id)
    if requested_player is None:
        bot.send_message(chat_id=mes.chat_id, text="Игрок не найден. Отправьте /hero из @ChatWarsBot.")
        return
    if guild_id is None:
        bot.send_message(chat_id=mes.chat_id,
                         text="Вы не состоите в гильдии. Вступите в гильдию в игре и попросите "
                              "командира добавить вас в гильдейском чате.")
        return
    guild = Guild.get_guild(guild_id=guild_id)
    if guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Гильдия не найдена.")
        return
    if not guild.check_high_access(update.callback_query.from_user.id):
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Вы более не являетесь заместителем")
        return
    response = get_guild_settings_text(guild)
    buttons = get_guild_settings_buttons(guild)
    bot.send_message(chat_id=update.callback_query.message.chat_id, text=response, reply_markup=buttons,
                     parse_mode='HTML')
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id)


def edit_guild_setting(bot, update):
    data_to_setting = {"gswith": "withdraw", "gsunpin": "unpin", "gsarenanotify": "arena_notify",
                       "gsbattlenotify": "battle_notify"}
    mes = update.callback_query.message
    data = update.callback_query.data
    setting = data_to_setting.get(data.partition("_")[0])
    if setting is None:
        bot.send_message(chat_id=mes.chat_id, text="Произошла ошибка. Начните сначала.")
        return
    guild_id = re.search("_(\\d+)", data)
    if guild_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Произошла ошибка. Начните сначала.")
        return
    guild_id = int(guild_id.group(1))
    requested_player = Player.get_player(update.callback_query.from_user.id)
    if requested_player is None:
        bot.send_message(chat_id=mes.chat_id, text="Игрок не найден. Отправьте /hero из @ChatWarsBot.")
        return
    if guild_id is None:
        bot.send_message(chat_id=mes.chat_id,
                         text="Вы не состоите в гильдии. Вступите в гильдию в игре и попросите "
                              "командира добавить вас в гильдейском чате.")
        return
    guild = Guild.get_guild(guild_id=guild_id)
    if guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Гильдия не найдена.")
        return
    if not guild.check_high_access(update.callback_query.from_user.id):
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Вы более не являетесь заместителем")
        return
    settings = guild.settings
    if settings is None:
        settings = {}
        guild.settings = settings
    cur = settings.get(setting)
    if cur is None:
        cur = True
        settings.update({setting: cur})
    settings.update({setting: not cur})
    guild.update_to_database(need_order_recashe=False)
    response = get_guild_settings_text(guild)
    buttons = get_guild_settings_buttons(guild)
    bot.editMessageText(chat_id=mes.chat_id, message_id=mes.message_id, text=response, reply_markup=buttons,
                        parse_mode='HTML')
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id)


def list_players(bot, update, guild_id=None):
    mes = update.callback_query.message
    if guild_id is None:
        data = update.callback_query.data
        guild_id = re.search("_(\\d+)", data)
        if guild_id is None:
            bot.send_message(chat_id=mes.chat_id, text="Произошла ошибка. Начните сначала.")
            return
        guild_id = int(guild_id.group(1))
        player = Player.get_player(update.callback_query.from_user.id)
        if player is None:
            bot.send_message(chat_id=mes.chat_id, text="Игрок не найден. Отправьте /hero из @ChatWarsBot.")
            return
        if guild_id is None:
            bot.send_message(chat_id=mes.chat_id,
                             text="Вы не состоите в гильдии. Вступите в гильдию в игре и попросите "
                                  "командира добавить вас в гильдейском чате.")
            return
    guild = Guild.get_guild(guild_id=guild_id)
    if guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Гильдия не найдена.")
        return
    if guild.tag == 'АКАДЕМИЯ':
        user_id = update.callback_query.from_user.id
        if user_id != guild.commander_id and user_id not in guild.assistants:
            return
    response = "Список игроков в гильдии <b>{}</b>\n".format(guild.tag)
    guild.sort_players_by_exp()
    guild.calculate_attack_and_defense()
    high_access = guild.check_high_access(update.callback_query.from_user.id)
    if high_access:
        response += "<em>🖇 — полный доступ к АПИ, 📎 — без экипировки</em>\n\n"
    for player_id in guild.members:
        player = Player.get_player(player_id)
        if player is None:
            logging.warning("Player in guild is None, guild = {}, player_id = {}".format(guild.tag, player_id))
            continue
        api_text = ""
        if high_access:
            token = player.api_info.get("token")
            if token is not None:
                access = player.api_info.get("access") or []
                if "gear" in access:
                    api_text = "🖇"
                else:
                    api_text = "📎"
        rp1, rp2, rp3 = player.get_reports_count()
        response_new = "{}<b>{}</b> @{} {}\n🔥<code>{}</code>,🏅<code>{}\n⚔{}, 🛡{}, " \
                       "🎖{}/{}</code>" \
                       "".format(classes_to_emoji.get(player.game_class) or "", player.nickname, player.username,
                                 api_text, player.exp, player.lvl, player.attack, player.defense, rp1, rp2)
        if high_access:
            response_new += "\nПоказать профиль: /view_profile_{}" \
                       "".format(player.id)
        response_new += "\n\n"
        if len(response + response_new) > MAX_MESSAGE_LENGTH:
            bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
            response = ""
        response += response_new
    response += "Всего: ⚔: <code>{}</code>, 🛡: <code>{}</code>".format(guild.get_attack(), guild.get_defense())
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id)


# Функция для принудительного удаления игрока из гильдии
def remove_player(bot, update):
    mes = update.message
    player_id = re.search("_(\\d+)", mes.text)
    if player_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис.")
        return
    player_id = int(player_id.group(1))
    if player_id == mes.from_user.id:
        bot.send_message(chat_id=mes.chat_id, text="Почему бы не выйти как нормальный человек? /leave_guild")
        return
    current_player = Player.get_player(mes.from_user.id)
    if current_player is None:
        return
    guild = Guild.get_guild(guild_id=current_player.guild)
    player_to_remove = Player.get_player(player_id)
    player_to_remove_guild = guild
    if player_to_remove_guild is not None and player_to_remove_guild.is_academy():
        # Костыль на учителей в академке без гильдии (такие бывают, да)
        pass
    else:
        if guild is None:
            bot.send_message(chat_id=mes.chat_id, text="Вы не состоите в гильдии.")
            return
    if not guild.check_high_access(current_player.id):
        bot.send_message(chat_id=mes.chat_id, text="Право распоряжаться людьми необходимо заслужить.")
        return

    if player_to_remove is None or player_to_remove.id not in guild.members:
        player_to_remove_guild = Guild.get_guild(player_to_remove.guild)
        if player_to_remove_guild is not None and player_to_remove_guild.is_academy() and \
                player_to_remove_guild.check_high_access(current_player.id):
            pass
        else:
            if player_to_remove.guild is not None:
                player_to_remove_guild = Guild.get_guild(player_to_remove.guild)
                if player_id == player_to_remove_guild.commander_id or player_id in player_to_remove_guild.assistants:
                    pass
                else:
                    bot.send_message(chat_id=mes.chat_id, text="Вы можете удалять игроков только в своей гильдии.")
                    return
    guild = player_to_remove_guild
    guild.delete_player(player_to_remove)
    bot.send_message(chat_id=update.message.chat_id, text="<b>{}</b> успешно удалён из гильдии "
                                                          "<b>{}</b>".format(player_to_remove.nickname, guild.tag),
                     parse_mode='HTML')
    bot.send_message(chat_id=player_to_remove.id,
                     text="Появившийся из-за угла стражник окликнул вас:\n"
                          "<em>Твой командир просил передать, что ты больше не в гильдии, воин!</em>",
                     parse_mode='HTML')


def leave_guild(bot, update):
    if update.message is not None:
        mes = update.message
        user_id = mes.from_user.id
        guild_id = None
    else:
        mes = update.callback_query.message
        user_id = update.callback_query.from_user.id
        data = update.callback_query.data
        guild_id = re.search("_(\\d+)", data)
        if guild_id is None:
            bot.send_message(chat_id=mes.chat_id, text="Произошла ошибка. Начните сначала.")
            return
        guild_id = int(guild_id.group(1))
    player = Player.get_player(user_id)
    if player is None:
        bot.send_message(chat_id=mes.chat_id, text="Игрок не найден. Пожалуйста, отправьте форвард /hero.")
        return
    if player.guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Вы не состоите в гильдии.")
        return
    if guild_id is None:
        guild_id = player.guild
    guild = Guild.get_guild(guild_id=guild_id)
    if guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Гильдия не найдена.")
        return
    if guild.commander_id == player.id:
        # bot.send_message(chat_id=mes.chat_id, text="Командир не может покинуть гильдию")
        # return
        guild.commander_id = None
    guild.delete_player(player)
    bot.send_message(chat_id=mes.chat_id, text="Вы успешно покинули гильдию")
    if update.callback_query is not None:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id)


# Добавление игрока в гильдию
def add(bot, update):
    player = Player.get_player(update.message.from_user.id)
    if player is None:
        bot.send_message(chat_id=update.message.chat_id, text="Игрок не найден. Пожалуйста, отправьте форвард /hero.")
        return
    academy = Guild.get_academy()
    if academy is not None and update.message.chat_id == academy.chat_id:
        guild = academy
    else:
        guild = Guild.get_guild(guild_id=player.guild)
        if guild is None:
            bot.send_message(chat_id=update.message.chat_id, text="Гильдия не найдена.")
            return
        if player.guild != guild.id:
            bot.send_message(chat_id=update.message.chat_id, text="Можно добавлять игроков только в свою гильдию")
            return
    if update.message.chat_id != guild.chat_id:
        bot.send_message(chat_id=update.message.chat_id, text="Добавлять игроков в гильдию можно только в официальном "
                                                              "чате гильдии")
        return
    if player.id != guild.commander_id and player.id not in guild.assistants:
        bot.send_message(chat_id=update.message.chat_id, text="Только командир и его замы могут добавлять бойцов.")
        return
    if update.message.reply_to_message is None:
        bot.send_message(chat_id=update.message.chat_id, text="Сообщение должно являться ответом на сообщение игрока, "
                                                              "которого необходимо добавить в гильдию.")
        return
    player_to_add = Player.get_player(update.message.reply_to_message.from_user.id)
    if player_to_add is None:
        bot.send_message(chat_id=update.message.chat_id, text="Игрок для добавления не найден.")
        return
    if player_to_add.guild is not None:
        bot.send_message(chat_id=update.message.chat_id, text="Игрок уже находится в гильдии.")
        return
    guild.add_player(player_to_add)

    bot.send_message(chat_id=update.message.chat_id, text="<b>{}</b> успешно добавлен в гильдию "
                                                          "<b>{}</b>".format(player_to_add.nickname, guild.tag),
                     parse_mode='HTML')


def add_assistant(bot, update):
    player = Player.get_player(update.message.from_user.id)
    if player is None:
        bot.send_message(chat_id=update.message.chat_id, text="Игрок не найден. Пожалуйста, отправьте форвард "
                                                              "/hero личным сообщением боту.")
        return
    guild = Guild.get_guild(guild_id=player.guild)
    if guild is None:
        bot.send_message(chat_id=update.message.chat_id, text="Гильдия не найдена.")
        return
    if player.guild != guild.id:
        bot.send_message(chat_id=update.message.chat_id, text="Можно добавлять замов только в своей гильдии")
        return
    if update.message.chat_id != guild.chat_id:
        bot.send_message(chat_id=update.message.chat_id, text="Добавлять заместителя можно только в официальном "
                                                              "чате гильдии")
        return
    if player.id != guild.commander_id and player.id not in guild.assistants:
        bot.send_message(chat_id=update.message.chat_id, text="Только командир и его замы могут добавлять новых замов.")
        return
    if update.message.reply_to_message is None:
        bot.send_message(chat_id=update.message.chat_id, text="Сообщение должно являться ответом на сообщение игрока, "
                                                              "которого необходимо сделать замом.")
        return
    player_to_add = Player.get_player(update.message.reply_to_message.from_user.id)
    if player_to_add is None:
        bot.send_message(chat_id=update.message.chat_id, text="Игрок для добавления не найден.")
        return
    if player_to_add.guild != guild.id:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Сделать заместителем можно только игрока из своей гильдии.")
        return
    if guild.check_high_access(player_to_add.id):
        bot.send_message(chat_id=update.message.chat_id, text="Игрок уже имеет необходимые права.")
        return
    guild.assistants.append(player_to_add.id)
    guild.update_to_database()
    bot.send_message(chat_id=update.message.chat_id,
                     text="<b>{}</b> теперь заместитель в гильдии <b>{}</b>".format(player_to_add.nickname, guild.tag),
                     parse_mode='HTML', reply_to_message_id=update.message.message_id)


def del_assistant(bot, update):
    player = Player.get_player(update.message.from_user.id)
    if player is None:
        bot.send_message(chat_id=update.message.chat_id, text="Игрок не найден. Пожалуйста, отправьте форвард "
                                                              "/hero личным сообщением боту.")
        return
    guild = Guild.get_guild(guild_id=player.guild)
    if guild is None:
        bot.send_message(chat_id=update.message.chat_id, text="Гильдия не найдена.")
        return
    if player.guild != guild.id:
        bot.send_message(chat_id=update.message.chat_id, text="Можно удалять замов только в своей гильдии")
        return
    if update.message.chat_id != guild.chat_id:
        bot.send_message(chat_id=update.message.chat_id, text="Удалять заместителя можно только в официальном "
                                                              "чате гильдии")
        return
    if player.id != guild.commander_id and player.id not in guild.assistants:
        bot.send_message(chat_id=update.message.chat_id, text="Только командир и его замы могут удалять текущих замов.")
        return
    if update.message.reply_to_message is None:
        bot.send_message(chat_id=update.message.chat_id, text="Сообщение должно являться ответом на сообщение игрока, "
                                                              "которого необходимо снять с должности зама.")
        return
    player_to_add = Player.get_player(update.message.reply_to_message.from_user.id)
    if player_to_add is None:
        bot.send_message(chat_id=update.message.chat_id, text="Игрок для удаления не найден.")
        return
    if not guild.check_high_access(player_to_add.id):
        bot.send_message(chat_id=update.message.chat_id, text="Игрок и не являлся замом.")
        return
    if player_to_add.id == guild.commander_id and False:
        bot.send_message(chat_id=update.message.chat_id, text="Нельзя свергнуть командира.")
        return
    guild.assistants.remove(player_to_add.id)
    guild.update_to_database()
    bot.send_message(chat_id=update.message.chat_id,
                     text="<b>{}</b> более не является заместителем в гильдии <b>{}</b>".format(player_to_add.nickname,
                                                                                                guild.tag),
                     parse_mode='HTML', reply_to_message_id=update.message.message_id)


def assistants(bot, update):
    mes = update.callback_query.message
    data = update.callback_query.data
    guild_id = re.search("_(\\d+)", data)
    if guild_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Произошла ошибка. Начните сначала.")
        return
    guild_id = int(guild_id.group(1))
    player = Player.get_player(update.callback_query.from_user.id)
    if player is None:
        bot.send_message(chat_id=mes.chat_id, text="Игрок не найден. Отправьте /hero из @ChatWarsBot.")
        return
    if guild_id is None:
        bot.send_message(chat_id=mes.chat_id,
                         text="Вы не состоите в гильдии. Вступите в гильдию в игре и попросите "
                              "командира добавить вас в гильдейском чате.")
        return
    guild = Guild.get_guild(guild_id=guild_id)
    if guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Гильдия не найдена.")
        return
    if not guild.check_high_access(update.callback_query.from_user.id):
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Вы более не являетесь заместителем")
        return
    if not guild.assistants:
        response = "В гильдии пока нет заместителей.\n"
    else:
        response = "Список заместителей гильдии <b>{}</b>:\n".format(guild.tag)
        for player_id in guild.assistants:
            current_player = Player.get_player(player_id)
            if current_player is None:
                continue
            response += "@{} - <b>{}</b>\n".format(current_player.username, current_player.nickname)
    response += "\nДобавить заместителя - /add_assistant - реплаем на сообщение игрока, " \
                "которого необходимо сделать заместителем\nУдалить заместителя - " \
                "/del_assistant - аналогично, реплаем на сообщение игрока, " \
                "которого необходимо снять с должности заместителя"
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id)


# Генерирует корректный и обновлённый текст в ответе на изменение гильдии. Генерируется каждый раз при изменении ги
def get_edit_guild_text(guild):

    if guild.commander_id is not None:
        commander = Player.get_player(guild.commander_id)
    else:
        commander = None

    response = "Командир: {}\n".format("@" + commander.username if commander is not None else "Не задан")
    response += "Чат отряда: <code>{}</code>, id: {}" \
                "\n{}".format(guild.chat_name or "Не задан",
                              "<code>{}</code>".format(guild.chat_id) if guild.chat_id is not None else "Не задан",
                              "<a href=\"{}\">Вступить</a>".format("https://t.me/joinchat/" + guild.invite_link)
                              if guild.invite_link is not None else "")
    response += "\n\n⚔: <b>{}</b>, 🛡: <b>{}</b>\n".format(guild.get_attack(), guild.get_defense())
    response += "Дивизион: <b>{}</b>\n".format(guild.division or "не задан")
    response += "Рассылка <b>{}</b>\n".format("включена" if guild.mailing_enabled else "оключена")
    response += "Приказы <b>{}</b>\n".format("включены" if guild.orders_enabled else "оключены")
    response += "Сообщения <b>{}</b>\n".format("пинятся" if guild.pin_enabled else "не пинятся")
    response += "Пины <b>{}</b>\n".format("громкие" if not guild.disable_notification else "тихие")
    return response


# Команда /edit_guild
def edit_guild(bot, update):
    mes = update.message
    if mes.chat_id != mes.from_user.id:
        bot.send_message(chat_id=mes.chat_id, text="Команда разрешена только в лс.")
        return
    try:
        guild_id = int(mes.text.partition("@")[0].split("_")[2])
    except ValueError:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис")
        return
    guild = Guild.get_guild(guild_id=guild_id)
    if guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Гильдия не найдена")
        return
    response = "Гильдия <b>{}</b>\n".format(guild.tag)
    response += get_edit_guild_text(guild)
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML', reply_markup=get_edit_guild_buttons(guild))
    return


def request_delete_guild(bot, update):
    mes = update.message
    guild_id = re.search("_(\\d+)", mes.text)
    if guild_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис")
        return
    guild_id = int(guild_id.group(1))
    guild = Guild.get_guild(guild_id)
    if guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Гильдия не найдена.")
        return
    buttons = get_delete_guild_buttons(guild)
    bot.send_message(chat_id=mes.chat_id, text="Вы действительно хотите удалить гильдию <b>{}</b>?\n\n"
                                               "<b>Внимание!!! Это приведёт к потере всех данных о гильдии и отключению"
                                               " пинов в их чате!!!</b>".format(guild.tag),
                     parse_mode='HTML', reply_markup=buttons)


def delete_guild(bot, update):
    if not check_access(update.callback_query.from_user.id):
        bot.send_message(chat_id=SUPER_ADMIN_ID,
                         text="@{} (id=<code>{}</code> пытался удалить ги "
                              "({})".format(update.callback_query.from_user.username,
                                            update.callback_query.from_user.id, update.callback_query.data))
        bot.send_message(chat_id=update.callback_query.message.chat_id, text="У вас недостаточно доступа!")
        return
    guild_id = re.search("_(\\d+)", update.callback_query.data)
    guild_id = int(guild_id.group(1))
    guild = Guild.get_guild(guild_id)
    if guild is None:
        bot.send_message(chat_id=update.callback_query.message.chat_id, text="Гильдия не найдена.")
        return
    guild.delete_guild()
    try:
        bot.editMessageText(chat_id=update.callback_query.message.chat_id,
                            message_id=update.callback_query.message.message_id,
                            text="Гильдия <b>{}</b> успешно удалена".format(guild.tag), parse_mode='HTML')
    except TelegramError:
        pass
    guild.fill_guild_ids()


def cancel_delete_guild(bot, update):
    try:
        bot.editMessageText(chat_id=update.callback_query.message.chat_id,
                            message_id=update.callback_query.message.message_id,
                            text="Удаление гильдии отменено!")
    except TelegramError:
        pass


# Нажатие инлайн-кнопки "Изменить командира"
def edit_guild_commander(bot, update, user_data):
    try:
        user_data.update({"status": "edit_guild_commander",
                          "edit_guild_id": int(update.callback_query.data.split("_")[1])})
    except ValueError:
        bot.send_message(chat_id=update.callback_query.message.chat_id, text="Произошла ошибка")
    else:
        bot.send_message(chat_id=update.callback_query.message.chat_id, text="Введите id нового командира гильдии, "
                                                                             "или наберите /cancel для отмены")
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id)


# Ввод id командира
def change_guild_commander(bot, update, user_data):
    mes = update.message
    try:
        player_id = int(mes.text)
    except ValueError:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис.")
        return
    player = Player.get_player(player_id, notify_on_error=False)
    if player is None:
        bot.send_message(chat_id=mes.chat_id, text="Игрок не найден. Проверьте правильность ввода id.")
        return
    guild_id = user_data.get("edit_guild_id")
    guild = None
    if guild_id is not None:
        guild = Guild.get_guild(guild_id=guild_id)
    if guild_id is None or guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Гильдия не найдена. Начните сначала.")
        return
    print(player.guild_tag, player.guild_tag, guild.tag)
    if guild.tag == "АКАДЕМИЯ":
        change_headmaster(bot, update, player, guild, user_data)
        return
    if player.guild_tag is not None and player.guild_tag != guild.tag:
        bot.send_message(chat_id=mes.chat_id, text="Командир может командовать только своей гильдией")

        # return
    if player.guild_tag is None or player.guild is None:
        guild.add_player(player)
    guild.commander_id = player_id
    if player.id not in guild.members:
        guild.add_player(player.id)
    guild.update_to_database()
    if "status" in user_data:
        user_data.pop("status")
    if "edit_guild_id" in user_data:
        user_data.pop("edit_guild_id")
    bot.send_message(chat_id=update.message.chat_id, text="Командиром гильдии <b>{}</b> назначен <b>{}</b> "
                                                          "{}".format(guild.tag, player.nickname,
                                                                      "(@{})".format(player.username)
                                                                      if player.username is not None else ""),
                     parse_mode='HTML')


# Нажатие инлайн-кнопки "Изменить чат гильдии"
def edit_guild_chat(bot, update, user_data):
    try:
        user_data.update(
            {"status": "edit_guild_chat", "edit_guild_id": int(update.callback_query.data.split("_")[1])})
    except ValueError:
        bot.send_message(chat_id=update.callback_query.message.chat_id, text="Произошла ошибка")
    else:
        bot.send_message(chat_id=update.callback_query.message.chat_id, text="Введите id нового чата гильдии, "
                                                                             "или наберите /cancel для отмены")
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id)


# Ввод айди нового чата ги
def change_guild_chat(bot, update, user_data):
    mes = update.message
    try:
        chat_id = int(mes.text)
    except ValueError:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис.")
        return
    guild_id = user_data.get("edit_guild_id")
    guild = None
    if guild_id is not None:
        guild = Guild.get_guild(guild_id=guild_id)
    if guild_id is None or guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Гильдия не найдена. Начните сначала.")
        return
    try:
        message = bot.sync_send_message(chat_id=chat_id, text="Это теперь официальный чат гильдии "
                                                              "<b>{}</b>".format(guild.tag), parse_mode='HTML')
        chat = bot.getChat(message.chat_id)
        if chat is None:
            bot.send_message(chat_id=update.message.chat_id, text="Произошла ошибка. Проверьте id "
                                                                  "и присутствие бота в этом чате")
            return
    except TelegramError:
        bot.send_message(chat_id=update.message.chat_id, text="Произошла ошибка. Проверьте id "
                                                              "и присутствие бота в этом чате")
        return
    guild.chat_id = chat.id
    guild.chat_name = chat.title
    try:
        guild.invite_link = bot.exportChatInviteLink(chat_id)
        if guild.invite_link is not None:
            guild.invite_link = guild.invite_link[22:]  # Обрезаю https://t.me/joinchat/
    except TelegramError:
        pass
    guild.update_to_database()
    bot.send_message(chat_id=mes.chat_id, text="Чат гильдии <b>{}</b> успешно изменён "
                                               "на <b>{}</b>".format(guild.tag, guild.chat_name or guild.chat_id),
                     parse_mode='HTML')
    if "status" in user_data:
        user_data.pop("status")
    if "edit_guild_id" in user_data:
        user_data.pop("edit_guild_id")


def edit_guild_division(bot, update, user_data):
    try:
        user_data.update(
            {"status": "edit_guild_division", "edit_guild_id": int(update.callback_query.data.split("_")[1])})
    except ValueError:
        bot.send_message(chat_id=update.callback_query.message.chat_id, text="Произошла ошибка")
    else:
        bot.send_message(chat_id=update.callback_query.message.chat_id,
                         text="Введите название нового дивизиона гильдии, или наберите /cancel для отмены")
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id)


def change_guild_division(bot, update, user_data):
    mes = update.message
    guild_id = user_data.get("edit_guild_id")
    guild = None
    if guild_id is not None:
        guild = Guild.get_guild(guild_id=guild_id)
    if guild_id is None or guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Гильдия не найдена. Начните сначала.")
        return
    guild.division = mes.text
    guild.update_to_database()
    bot.send_message(chat_id=mes.chat_id, text="Дивизион <b>{}</b> изменён на "
                                               "<b>{}</b>".format(guild.tag, guild.division),
                     parse_mode='HTML')
    if "status" in user_data:
        user_data.pop("status")
    if "edit_guild_id" in user_data:
        user_data.pop("edit_guild_id")


def change_guild_bool_state(bot, update):
    if not check_access(update.callback_query.from_user.id):
        return
    try:
        guild_id = int(update.callback_query.data.split("_")[1])
        new = "new" in update.callback_query.data
        page = int(update.callback_query.data.partition("page_")[2]) if new else 0
    except ValueError:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id,
                                text="Произошла ошибка. Попробуйте ещё раз")
        return
    guild = Guild.get_guild(guild_id)
    if guild is None:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id,
                                text="Гильдия не найдена. Попробуйте ещё раз")
        return
    edit_type = update.callback_query.data[2]
    if edit_type == 'o':
        guild.orders_enabled = not guild.orders_enabled
    elif edit_type == 'p':
        guild.pin_enabled = not guild.pin_enabled
    elif edit_type == 'n':
        guild.disable_notification = not guild.disable_notification
    elif edit_type == 'm':
        guild.mailing_enabled = not guild.mailing_enabled
    guild.update_to_database()
    mes = update.callback_query.message
    reply_markup = get_guild_inline_buttons(guild, page) if new else get_edit_guild_buttons(guild)
    new_text = get_edit_guild_text(guild)
    try:
        bot.editMessageText(chat_id=mes.chat_id, message_id=mes.message_id, text=new_text, reply_markup=reply_markup,
                            parse_mode='HTML')
    except TelegramError:
        pass
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id,
                            text="Успешно изменено.")


# Информация о чате в лс
def chat_info(bot, update):
    response = "<b>{}</b>, id: <code>{}</code>".format(update.message.chat.title, update.message.chat_id)
    bot.send_message(chat_id=update.message.from_user.id, text=response, parse_mode='HTML')
