from castle_files.work_materials.globals import moscow_tz, local_tz, cursor, conn
from castle_files.bin.service_functions import count_battle_id
from castle_files.bin.stock import get_item_code_by_name
from castle_files.libs.player import Player
from castle_files.libs.guild import Guild

import re
import datetime

REPORT_REPUTATION_COUNT = 5


def count_battle_time(battle_id):
    first_battle = datetime.datetime(2018, 5, 27, 9, 0, 0, 0)
    target_battle = first_battle
    interval = datetime.timedelta(hours=8)
    for i in range(battle_id):
        target_battle += interval
    return target_battle


def add_report(bot, update, user_data):
    mes = update.message
    s = mes.text
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return

    try:
        forward_message_date: datetime.datetime = local_tz.localize(mes.forward_date).astimezone(tz=moscow_tz).replace(tzinfo=None)
    except ValueError:
        try:
            forward_message_date = mes.forward_date.astimezone(tz=moscow_tz).replace(tzinfo=None)
        except ValueError:
            forward_message_date = mes.forward_date
    except AttributeError:
        forward_message_date = local_tz.localize(mes.date).astimezone(tz=moscow_tz).replace(tzinfo=None)

    if 'hit' in s.lower() or 'miss' in s.lower() or 'last hit' in s.lower():
        earned = re.search("Получено: (.+) \\((\\d+)\\)", s)
        if earned is not None:
            name = earned.group(1)
            count = earned.group(2)
            code = get_item_code_by_name(name)
            if code is None:
                code = name
            drop = player.mobs_info.get("drop")
            if drop is None:
                drop = {}
                player.mobs_info.update({"drop": drop})
            drop.update({forward_message_date.timestamp(): {"code": code, "count": 1}})
            player.update()
        return
    line = re.search(".(.*)\\s⚔:(\\d+)\\(?(.?\\d*)\\)?.*🛡:(\\d+)\\(?(.?\\d*)\\)?.*Lvl: (\\d+)\\s", s)
    """ 
    . - замок, (.*)\\s - никнейм в игре - от замка до эмодзи атаки. ⚔:(\\d+) - Парсинг атаки в конкретной битве
    \\(? - Возможно атака подверглась модификациям, тогда сразу после числа атаки будет открывающая скобка. 
    \\(?(.?\\d*)\\)? - Парсинг дополнительной атаки целиком. Группа будет равна ' ', то есть одному пробельному символу,
    если дополнительной атаки нет.
    .*🛡: - всё лишнее до дефа. Далее абсолютно аналогично атаке 🛡:(\\d+)\\(?(.?\\d*)\\)?
    .*Lvl: (\\d+)\\s - лишнее до уровня и парсинг уровня, в комментариях не нуждается
    """
    nickname = line.group(1)
    if nickname != player.nickname:
        bot.send_message(chat_id=mes.chat_id, text="Это не ваш репорт. В случае ошибок обновите профиль.",
                         reply_to_message_id=mes.message_id)
        return
    attack = int(line.group(2))
    additional_attack = int(line.group(3)) if line.group(3) != " " else 0
    defense = int(line.group(4))
    additional_defense = int(line.group(5)) if line.group(5) != " " else 0
    lvl = int(line.group(6))
    exp = re.search("🔥Exp:\\s(-?\\d+)", s)
    exp = int(exp.group(1)) if exp is not None else 0
    gold = re.search("💰Gold:\\s+(-?\\d+)", s)
    gold = int(gold.group(1)) if gold is not None else 0
    stock = re.search("📦Stock:\\s+(-?\\d+)", s)
    stock = int(stock.group(1)) if stock is not None else 0
    battle_id = count_battle_id(mes)
    request = "select report_id from reports where battle_id = %s and player_id = %s"
    cursor.execute(request, (battle_id, player.id))
    row = cursor.fetchone()
    if row is not None:
        bot.send_message(chat_id=mes.from_user.id, text="Репорт за эту битву уже учтён!")
        return
    request = "insert into reports(player_id, battle_id, attack, additional_attack, defense, additional_defense, lvl, "\
              "exp, gold, stock) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(request, (player.id, battle_id, attack, additional_attack, defense, additional_defense, lvl, exp,
                             gold, stock))


    player.count_reports()
    reputation = REPORT_REPUTATION_COUNT

    if forward_message_date < datetime.datetime(year=2019, month=5, day=29, hour=12):
        reputation = 0

    player.reputation += reputation
    player.update()
    response = "Репорт учтён. Спасибо!\n" \
               "{}".format("Получено {}🔘!".format(reputation) if not user_data.get("rp_off") else "")
    bot.send_message(chat_id=mes.from_user.id, text=response, parse_mode='HTML')
    """
    bot.send_message(chat_id=mes.from_user.id,
                     text="<b>{}</b> ⚔:{}{} 🛡:{}{} Lvl: {}\n"
                          "🔥Exp: {}\n💰Gold:{}\n📦Stock:{}"
                          "".format(player.nickname, attack,
                                    "({})".format(additional_attack) if additional_attack != 0 else "",
                                    defense, "({})".format(additional_defense) if additional_defense != 0 else "",
                                    lvl, exp, gold, stock),
                     parse_mode='HTML')
    """


# VERY EXPENSIVE OPERATION
# TODO run_async
def battle_stats(bot, update):
    mes = update.message
    cursor1 = conn.cursor()
    battle_id = re.search("_(\\d+)", mes.text)
    battle_id = int(battle_id.group(1)) if battle_id is not None else count_battle_id(mes)

    guilds = []
    for guild_id in Guild.guild_ids:
        guild = Guild.get_guild(guild_id=guild_id)
        if guild is None:
            continue
        guild.clear_counted_reports()
        guilds.append(guild)
    guilds.sort(key=lambda x: x.division or "")
    guilds.append(Guild(-1, "Без гильдии", None, None, None, None, None, None, None, None, None, None, None, None))
    request = "select player_id, attack, defense, gold from reports where battle_id = %s"
    cursor1.execute(request, (battle_id,))
    row = cursor1.fetchone()
    response = "Статистика по битве {} - {}:\n".format(battle_id,
                                                       count_battle_time(battle_id).strftime("%d/%m/%y %H:%M:%S"))
    while row is not None:
        player = Player.get_player(row[0])
        if player.guild is None:
            guild = guilds[-1]
        else:
            guild = Guild.get_guild(player.guild)
        guild.add_count_report(row[1], row[2], row[3])
        row = cursor1.fetchone()
    total_reports = 0
    total_attack = 0
    total_defense = 0
    total_gold = 0
    for guild in guilds:
        values = guild.get_counted_report_values()
        total_reports += values[0]
        total_attack += values[1]
        total_defense += values[2]
        total_gold += values[3]
        response += "<code>{:<3}</code>-👣{} ⚔️{} 🛡{} 💰{}" \
                    "\n".format(guild.tag, values[0], values[1], values[2], values[3])
    response += "\nВсего: {} репортов, ⚔️: <b>{}</b>, 🛡: <b>{}</b>, " \
                    "💰: <b>{}</b>\n".format(total_reports, total_attack, total_defense, total_gold)
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
