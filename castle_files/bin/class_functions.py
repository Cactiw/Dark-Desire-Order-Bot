"""
Здесь функции, связанные с особенностями разных классов в чв
"""
from castle_files.bin.stock import get_item_code_by_name, get_item_name_by_code

from castle_files.libs.player import Player

from castle_files.work_materials.globals import moscow_tz, local_tz

import re
import logging
import datetime


def add_trap(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    if player.game_class != 'Ranger':
        bot.send_message(chat_id=mes.from_user.id,
                         text="Учёт статистики ловушек доступен только лучникам.\n\n<em>Для обновления класса "
                              "необходимо скинуть форвард ответа игрокого бота на команду /me</em>", parse_mode='HTML')
        return
    strings = re.findall("Получено: (.+) \\((\\d+)\\)", mes.text)
    trap_info = player.class_info.get("trap_info")
    if trap_info is None:
        trap_info = {}
        player.class_info.update({"trap_info": trap_info})

    for res in strings:
        item_name = res[0]
        item_count = int(res[1])
        item_code = get_item_code_by_name(item_name)
        if item_code is None:
            logging.error("Item_code is None for {}".format(item_name))
            continue
        count = trap_info.get(item_code) or 0
        trap_info.update({item_code: count + item_count})
        if not item_code[0].isdigit():
            try:
                forward_message_date = local_tz.localize(mes.forward_date).astimezone(tz=moscow_tz).replace(tzinfo=None)
            except Exception:
                forward_message_date = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)
            trap_info.update({"last_not_resource": item_code, "last_not_resource_date":
                              forward_message_date.strftime("%d/%m/%y %H:%M")})
    player.update_to_database()
    bot.send_message(chat_id=mes.chat_id, text="Дроп из ловушек записан.\nСтатистика: /trap_stats")
    pass


def trap_stats(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    if player.game_class != 'Ranger':
        bot.send_message(chat_id=mes.from_user.id,
                         text="Учёт статистики ловушек доступен только лучникам.\n\n<em>Для обновления класса "
                              "необходимо скинуть форвард ответа игрокого бота на команду /me</em>", parse_mode='HTML')
        return
    trap_info = player.class_info.get("trap_info").copy()
    if trap_info is None:
        bot.send_message(chat_id=mes.from_user.id, text="<em>Пусто</em>\n\nДля учёта статистики ловушек кидайте"
                                                        " форварды с попаданием в ловушку в бота.",
                         parse_mode='HTML')
        return
    response = "Статистика выпадения дропа с ловушек:\n"
    last_good_drop, last_good_drop_date = trap_info.get("last_not_resource"), trap_info.get("last_not_resource_date")
    try:
        trap_info.pop("last_not_resource")
        trap_info.pop("last_not_resource_date")
    except KeyError:
        pass
    total = 0
    for count in list(trap_info.values()):
        if isinstance(count, int):
            total += count
    trap_info = list(sorted(list(trap_info.items()), key=lambda x: int(x[1]) if isinstance(x[1], int) else -1,
                            reverse=True))
    for code, count in trap_info:
        name = get_item_name_by_code(code)
        if name is None:
            continue
        response += "<b>{}</b> x {} ({}%)\n".format(name, count, int(count * 100 / total))
    if last_good_drop is not None and last_good_drop_date is not None:
        name = get_item_name_by_code(last_good_drop)
        response += "\n\nПоследний необычный дроп: <b>{}</b>" \
                    "\n( <em>{}</em> )".format(name, last_good_drop_date)
    bot.send_message(chat_id=mes.from_user.id, text=response, parse_mode='HTML')
