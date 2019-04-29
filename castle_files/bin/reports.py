from castle_files.work_materials.globals import moscow_tz, local_tz, cursor
from castle_files.libs.player import Player

import re
import datetime


# Функция, которая считает id битвы по сообщению, крайне желательно переписать нормально, похоже на костыль
def count_battle_id(message):
    first_battle = datetime.datetime(2018, 5, 27, 9, 0, 0, 0)
    interval = datetime.timedelta(hours=8)
    try:
        forward_message_date = local_tz.localize(message.forward_date).astimezone(tz=moscow_tz).replace(tzinfo=None)
    except ValueError:
        try:
            forward_message_date = message.forward_date.astimezone(tz=moscow_tz).replace(tzinfo=None)
        except ValueError:
            forward_message_date = message.forward_date
    time_from_first_battle = forward_message_date - first_battle
    battle_id = 0
    while time_from_first_battle > interval:
        time_from_first_battle -= interval
        battle_id = battle_id + 1
    return battle_id


# TODO: защита от повторных репортов
def add_report(bot, update):
    mes = update.message
    s = mes.text
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    line = re.search(".(.*)\\s⚔:(\\d+)\\(?(.?\\d*)\\)?.*🛡:(\\d+)\\(?(.?\\d*)\\)?.*Lvl: (\\d+)\\s", s)
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
    request = "insert into reports(player_id, battle_id, attack, additional_attack, defense, additional_defense, lvl, "\
              "exp, gold, stock) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(request, (player.id, battle_id, attack, additional_attack, defense, additional_defense, lvl, exp,
                             gold, stock))
    bot.send_message(chat_id=mes.from_user.id, text="Репорт учтён. Спасибо!")
