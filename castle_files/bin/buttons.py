"""
Этот модуль содержит функции получения Inline, или обычных кнопок для отправки их в сообщении.
"""
from telegram import InlineKeyboardButton, KeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from castle_files.bin.service_functions import check_access
from castle_files.libs.castle.location import Location
from castle_files.libs.player import Player
from castle_files.work_materials.globals import dispatcher, king_id, SUPER_ADMIN_ID


def get_edit_guild_buttons(guild):
    buttons = [
        [
            InlineKeyboardButton("Изменить командира", callback_data="gccmdr_{}".format(guild.id)),
            InlineKeyboardButton("Изменить чат гильдии", callback_data="gccht_{}".format(guild.id)),
        ],
        [
            InlineKeyboardButton("Изменить дивизион", callback_data="gcdvs_{}".format(guild.id)),
            InlineKeyboardButton("Отключить приказы" if guild.orders_enabled else "Включить приказы",
                                 callback_data="gco_{}".format(guild.id))
        ],
        [
            InlineKeyboardButton("Отключить пины" if guild.pin_enabled else "Включить пины",
                                 callback_data="gcp_{}".format(guild.id)),
            InlineKeyboardButton("Включить уведомления" if guild.disable_notification else "Выключить уведомления",
                                 callback_data="gcn_{}".format(guild.id)),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def get_delete_guild_buttons(guild):
    buttons = [
        [
            InlineKeyboardButton("Да", callback_data="g_delete_confirm_{}".format(guild.id)),
            InlineKeyboardButton("Нет", callback_data="g_delete_cancel_{}".format(guild.id)),
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def get_view_guild_buttons(guild, user_id=None):
    buttons = [
        [
            InlineKeyboardButton("Список игроков", callback_data="gipl_{}".format(guild.id)),
            InlineKeyboardButton("Покинуть гильдию", callback_data="gilv_{}".format(guild.id)),
        ],
    ]
    if user_id is not None and guild.check_high_access(user_id):
        buttons.append([
            InlineKeyboardButton("Заместители", callback_data="giass_{}".format(guild.id)),
        ])
    return InlineKeyboardMarkup(buttons)


# Функция, которая возвращает кнопки для любого статуса. Принимает на вход user_data, в котором читает поле "status",
# далее генерирует и возвращает кнопки
def get_general_buttons(user_data, player=None, only_buttons=False):
    status = user_data.get("status")
    rp_off = user_data.get("rp_off")
    buttons = None
    if rp_off:
        buttons = [
            [
                KeyboardButton("👀 Профиль"),
                KeyboardButton("👥 Гильдия"),
            ]
        ]
    if status is None or status == "default":
        status = "central_square"
        user_data.update({"status": status})
    if status == "central_square":
        buttons = [
            [
                KeyboardButton(Location.get_location(1).name),
                KeyboardButton(Location.get_location(2).name),
                KeyboardButton("⛩ Врата замка"),
                ],
            [
                KeyboardButton("🏚 Не построено"),
            ],
            [
                KeyboardButton("↔️ Подойти к указателям"),
                # KeyboardButton("↩️ Назад"),
            ]
        ]
    elif status == 'barracks':
        buttons = [
            [
                KeyboardButton("👀 Посмотреть в зеркало"),
                KeyboardButton("👥 Посмотреть ведомость гильдии"),
                ],
            [
                KeyboardButton("↩️ Назад"),
            ]
        ]
    elif status == 'throne_room':
        buttons = [
            [
                KeyboardButton("Обратиться к командному составу"),
                KeyboardButton("Попросить аудиенции у 👑Короля"),
                ],
            [
                KeyboardButton("🎇Посмотреть на портреты"),
            ],
            [
                KeyboardButton("↩️ Назад"),
            ]
        ]
        if player is not None and check_access(player.id):
            buttons[1].append(KeyboardButton("Штаб"))
        if player is not None and player.id in [king_id, SUPER_ADMIN_ID]:
            buttons[1].append(KeyboardButton("Кабинет Короля"))
    elif status in ['mid_feedback', 'duty_feedback', 'sending_guild_message',
                    'editing_debrief', 'changing_castle_message']:
        buttons = [
            [
                KeyboardButton("↩️ Назад"),
            ]
        ]
    elif status == 'castle_gates':
        on_duty = user_data.get("on_duty")
        print(on_duty, user_data)
        if on_duty:
            buttons = [
                [
                    KeyboardButton("Покинуть вахту"),
                ],
            ]
        else:
            buttons = [
                [
                    KeyboardButton("Обратиться к 💂‍♂Стражам"),
                ],
                [
                    KeyboardButton("↩️ Назад"),
                ]
            ]
            print(player, player.game_class if player is not None else "")
            if player is not None and player.game_class == "Sentinel":  # Только для стражей, захардкожено
                buttons[0].append(KeyboardButton("Заступить на вахту"))
    elif status == 'king_cabinet':
        buttons = [
            [
                KeyboardButton("Добавить генерала"),
                KeyboardButton("Изменить сообщение"),
            ],
            [
                KeyboardButton("↩️ Назад"),
            ]
        ]
    elif status == 'headquarters':
        buttons = [
            [
                KeyboardButton("📜Выкатить дебриф"),
                KeyboardButton("📣Рассылка по гильдиям"),
            ],
            [
                KeyboardButton("↩️ Назад"),
            ]
        ]
    if only_buttons:
        return buttons
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def get_text_to_general_buttons(user_data):
    status = user_data.get("status")
    location_id = user_data.get("location_id")
    rp_off = user_data.get("rp_off")
    if location_id is None:
        user_data.update({"location_id": 0})
    if rp_off:
        return "Доброго времени суток!\nВыберите действие:"
    if status is None or status == "default":
        return "Вы входите в замок Скалы. Выберите, куда направиться!"
    if location_id is not None:
        return Location.get_location_enter_text_by_id(location_id)


def send_general_buttons(user_id, user_data, bot=None):
    if bot is None:
        bot = dispatcher.bot
    player = Player.get_player(user_id)
    bot.send_message(chat_id=user_id, text=get_text_to_general_buttons(user_data),
                     reply_markup=get_general_buttons(user_data, player=player), parse_mode='HTML')
