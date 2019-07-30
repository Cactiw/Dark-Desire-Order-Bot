"""
Здесь функции, связанные с особенностями разных классов в чв
"""
from castle_files.bin.stock import get_item_code_by_name

from castle_files.libs.player import Player

import re
import logging


def add_trap(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    if player.game_class != 'Archer':
        bot.send_message(chat_id=mes.from_user.id,
                         text="Учёт статистики ловушек доступен только лучникам.\n\n<em>Для обновления класса "
                              "необходимо скинуть форвард ответа игрокого бота на команду /me</em>")
        return
    strings = re.findall("Получено: (.+) \\((\\d+)\\)", mes.text)
    trap_info = player.class_info.get("trap_info")
    if trap_info is None:
        trap_info = {}
        player.class_info.update({"trap_info": trap_info})

    for res in strings:
        item_name, count = res
        item_code = get_item_code_by_name(item_name)
        if item_code is None:
            logging.error("Item_code is None for {}".format(item_name))
            continue
        count = trap_info.get(item_code) or 0
        trap_info.update({item_code: count + 1})
        if not item_code[0].isdigit():
            trap_info.update({"last_not_resource": item_code})
    bot.send_message(chat_id=mes.chat_id, text="Дроп из ловушек записан.")
    pass
