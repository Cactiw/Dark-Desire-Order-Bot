from castle_files.work_materials.globals import moscow_tz, local_tz, cursor, conn, SUPER_ADMIN_ID, utc, SKIPPED_DIVISIONS

from castle_files.bin.service_functions import count_battle_id, check_access
from castle_files.bin.stock import get_item_code_by_name
from castle_files.bin.quest_triggers import on_add_report

from castle_files.libs.player import Player
from castle_files.libs.guild import Guild

import re
import datetime
import json

REPORT_REPUTATION_COUNT = 5
MAX_REPORTS_COMBO = 10


def count_battle_time(battle_id) -> datetime.datetime:
    """
    Служебная функция, считающая время битвы с battle_id
    :param battle_id: Int - Id битвы, время которой нужно посчитать
    :return: datetime
    """
    first_battle = datetime.datetime(2018, 5, 27, 9, 0, 0, 0)
    target_battle = first_battle
    interval = datetime.timedelta(hours=8)
    for i in range(battle_id):
        target_battle += interval
    return target_battle


def add_report(bot, update, user_data):
    """
    Функция сохранения репорта от игрока
    """
    mes = update.message
    s = mes.text
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return

    try:
        forward_message_date = utc.localize(mes.forward_date).astimezone(tz=moscow_tz).replace(tzinfo=None)
    except ValueError:
        try:
            forward_message_date = mes.forward_date
        except AttributeError:
            forward_message_date = local_tz.localize(mes.date).astimezone(tz=moscow_tz).replace(tzinfo=None)

    line = re.search("[🍆🍁☘️🌹🐢🦇🖤️]*(.*)\\s⚔:(\\d+)\\(?(.?\\d*)\\)?.*🛡:(\\d+)\\(?(.?\\d*)\\)?.*Lvl: (\\d+)\\s", s)
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
    hp = re.search("❤️Hp: (-?\\d+)", s)
    hp = int(hp.group(1)) if hp is not None else 0
    outplay = re.search("Тактически переиграл (.+) на ⚔️(\\d+)", s)
    outplay_dict = {}
    if outplay is not None:
        outplay_nickname = outplay.group(1)
        outplay_attack = int(outplay.group(2))
        outplay_dict.update({"nickname": outplay_nickname, "attack": outplay_attack})

    if 'Встреча:' in s or ('Твои удары' in s.lower() and 'Атаки врагов' in s.lower() and 'Ластхит' in s.lower()):
        # Репорт с мобов
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
        names, lvls, buffs = [], [], []
        for string in mes.text.splitlines():
            parse = re.search("(.+) lvl\\.(\\d+)", string)
            if parse is not None:
                name = parse.group(1)
                lvl = int(parse.group(2))
                names.append(name)
                lvls.append(lvl)
                buffs.append("")
            else:
                parse = re.search("  ╰ (.+)", string)
                if parse is not None:
                    buff = parse.group(1)
                    buffs.pop()
                    buffs.append(buff)
        hit = re.search("Твои удары: (\\d+)", s)
        hit = int(hit.group(1)) if hit is not None else 0
        miss = re.search("Атаки врагов: (\\d+)", s)
        miss = int(miss.group(1)) if miss is not None else 0
        last_hit = re.search("Ластхит: (\\d+)", s)
        last_hit = int(last_hit.group(1)) if last_hit is not None else 0
        request = "select report_id from mob_reports where date_created = %s and player_id = %s"
        cursor.execute(request, (forward_message_date, player.id))
        row = cursor.fetchone()
        if row is not None:
            return
        request = "insert into mob_reports(player_id, date_created, attack, additional_attack, defense, " \
                  "additional_defense, lvl, exp, gold, stock, mob_names, mob_lvls, buffs, hp, hit, miss, last_hit) " \
                  "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(request, (player.id, forward_message_date, attack, additional_attack, defense,
                                 additional_defense, lvl, exp, gold, stock, names, lvls, buffs, hp, hit, miss, last_hit))
        return

    equip = re.search("Найдено: (.+) \\(from (.+)\\)", s)
    equip_change = None
    if equip is not None:
        name = equip.group(1)
        found_from = equip.group(2)
        equip_change = {"status": "Found", "name": name, "from": found_from}
    else:
        equip = re.search("Утрачено: (.+)", s)
        if equip is not None:
            name = equip.group(1)
            equip_change = {"status": "Lost", "name": name}

    request = "select report_id from reports where battle_id = %s and player_id = %s"
    cursor.execute(request, (battle_id, player.id))
    row = cursor.fetchone()
    if row is not None:
        bot.send_message(chat_id=mes.from_user.id, text="Репорт за эту битву уже учтён!")
        return
    request = "insert into reports(player_id, battle_id, attack, additional_attack, defense, additional_defense, lvl, "\
              "exp, gold, stock, equip, outplay) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(request, (player.id, battle_id, attack, additional_attack, defense, additional_defense, lvl, exp,
                             gold, stock, json.dumps(equip_change, ensure_ascii=False) if equip_change is not None else
                             None, json.dumps(outplay_dict, ensure_ascii=False) if outplay_dict is not None else None))

    player.count_reports()
    combo = count_reports_combo(player.id, battle_id)
    reputation = REPORT_REPUTATION_COUNT * combo

    if forward_message_date < datetime.datetime(year=2019, month=5, day=29, hour=12):
        reputation = 0

    player.reputation += reputation
    player.update()
    response = "Репорт учтён. Спасибо!\n" \
               "{}".format("Получено {}🔘 ({} х Комбо репортов подряд)!\n{}".format(
                    reputation, combo, "Максимальное комбо!" if combo == MAX_REPORTS_COMBO else "")
                                          if not user_data.get("rp_off") else "")
    bot.send_message(chat_id=mes.from_user.id, text=response, parse_mode='HTML')
    if exp != 0:
        on_add_report(player, forward_message_date)
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


def count_reports_combo(player_id: int, battle_id: int) -> int:
    """
    Функция подсчитывает, комбо сданных репортов (сколько репортов сдано подряд).
    :param player_id: int - Player id
    :param battle_id: int - Battle id of new reports
    :return: int - reputation that should be added to player`s balance as a reward
    """
    request = "select battle_id from reports where player_id = %s and battle_id < %s order by battle_id desc limit %s"
    cursor.execute(request, (player_id, battle_id, MAX_REPORTS_COMBO - 1))
    rows = cursor.fetchall()
    combo = 1
    for (new_battle_id, *skip) in rows:
        if battle_id - new_battle_id > 1:
            break
        battle_id = new_battle_id
        combo += 1
    return combo


def battle_drop(bot, update):
    mes = update.message
    request = "select battle_id, equip from reports where player_id = %s and equip is not null " \
              "order by battle_id desc limit 20"
    cursor.execute(request, (mes.from_user.id,))
    rows = cursor.fetchall()
    response = "Последние изменения в экипировке по репортам:\n"
    for row in rows:
        found_from = row[1].get("from")
        response += "{} - <code>{}</code>: <b>{}</b> {}" \
                    "\n".format(count_battle_time(row[0]), row[1].get("status"), row[1].get("name"),
                                "(От {})".format(found_from) if found_from is not None else "")
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')


def battle_equip(bot, update):
    mes = update.message
    if not check_access(mes.from_user.id):
        return
    battle_id = re.search("\\d+", mes.text)
    if battle_id is None:
        battle_id = count_battle_id(mes)
    else:
        battle_id = int(battle_id.group(0))
    full = 'full' in mes.text
    request = "select player_id, equip from reports where battle_id = %s and equip is not null " \
              "order by equip ->> 'status'"
    cursor.execute(request, (battle_id,))
    rows = cursor.fetchall()
    response = "Дроп с битвы {} - {} :\n".format(battle_id, count_battle_time(battle_id).strftime("%d/%m/%y %H:%M:%S"))
    for row in rows:
        name, found_from = row[1].get("name"), row[1].get("from")
        player = Player.get_player(row[0])
        response += "{}<b>{}</b> {}\n".format("{} ".format((player.castle + player.nickname) if full else ""),
                                              name, "(От {})".format(found_from) if found_from is not None else "")
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')


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
        if guild is None or guild.division in SKIPPED_DIVISIONS:
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
        if player.castle != '🖤':
            row = cursor1.fetchone()
            continue
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
    guilds.sort(key=lambda x: (x.division or "", x.get_counted_report_values()[1]), reverse=True)
    current_division = guilds[0].division
    division_reports, division_attack, division_defense, division_gold = 0, 0, 0, 0
    for guild in guilds:
        if guild.division != current_division:
            response += "Дивизион {}:\nВсего: {} репортов, ⚔️: <b>{}</b>, 🛡: <b>{}</b>, 💰: <b>{}</b>\n\n" \
                        "".format(current_division, division_reports, division_attack, division_defense, division_gold)
            total_attack += division_attack
            total_defense += division_defense
            total_gold += division_gold
            total_reports += division_reports
            division_reports, division_attack, division_defense, division_gold = 0, 0, 0, 0

            current_division = guild.division

        values = guild.get_counted_report_values()
        division_reports += values[0]
        division_attack += values[1]
        division_defense += values[2]
        division_gold += values[3]
        response += "<code>{:<3}</code>-👣{} ⚔️{} 🛡{} 💰{}" \
                    "\n".format(guild.tag, values[0], values[1], values[2], values[3])


    response += "\nВсего: {} репортов, ⚔️: <b>{}</b>, 🛡: <b>{}</b>, " \
                    "💰: <b>{}</b>\n".format(total_reports, total_attack, total_defense, total_gold)
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
