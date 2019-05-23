"""
Здесь все функции, связанные со стройкой, в том числе добыча ресурсов, учёт репутации (в контексте стройки, она ведь
наверняка как-то ещё будет набираться), и сама стройка.
"""
from castle_files.bin.buttons import get_general_buttons, send_general_buttons

from castle_files.libs.player import Player
from castle_files.libs.castle.location import Location

from castle_files.work_materials.globals import job


def sawmill(bot, update, user_data):
    user_data.update({"status": "sawmill"})
    buttons = get_general_buttons(user_data)
    bot.send_message(chat_id=update.message.chat_id,
                     text="Вы отправились добывать дерево. Это займёт примерно 3 минуты.\n\nВы можете вернуться "
                          "мгновенно. В этом случае вся добыча будет утеряна.", reply_markup=buttons)
    context = [update.message.from_user.id, user_data, "wood"]
    job.run_once(callback=resource_return, when=3 * 60, context=context)


def quarry(bot, update, user_data):
    user_data.update({"status": "quarry"})
    buttons = get_general_buttons(user_data)
    bot.send_message(chat_id=update.message.chat_id,
                     text="Вы отправились добывать камень. Это займёт примерно 3 минуты", reply_markup=buttons)
    context = [update.message.from_user.id, user_data, "stone"]
    job.run_once(callback=resource_return, when=3 * 60, context=context)


def treasury(bot, update, user_data):
    user_data.update({"status": "treasury", "location_id": 6})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def resource_return(bot, job):
    if job.context[1].get("status") not in ["sawmill", "quarry"]:
        return
    throne = Location.get_location(2)
    throne.treasury.change_resource(job.context[2], 1)
    player = Player.get_player(job.context[0])
    player.reputation += 1
    player.update_to_database()
    job.context[1].update({"status": "castle_gates"})
    buttons = get_general_buttons(job.context[1], player)
    bot.send_message(chat_id=job.context[0], text="Вы успешно добыли {}. Казна обновлена. Получен 🔘"
                                                  "".format("дерево" if job.context[2] == "wood" else "камень"),
                     reply_markup=buttons)


def construct(bot, update, user_data):
    pass
