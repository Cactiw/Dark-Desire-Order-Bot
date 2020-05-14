"""
Этот модуль содержит функции получения Inline, или обычных кнопок для отправки их в сообщении.
"""
from telegram import InlineKeyboardButton, KeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from castle_files.bin.service_functions import check_access

from castle_files.libs.castle.location import Location, status_to_location
from castle_files.libs.player import Player
from castle_files.libs.guild import Guild
from castle_files.libs.alliance import Alliance

from castle_files.work_materials.globals import dispatcher, king_id, SUPER_ADMIN_ID, construction_jobs


def get_profile_buttons(player, whois_access=False, self_request=False):
    buttons = [
        [
            InlineKeyboardButton("История гильдий", callback_data="pr_guild_history_{}".format(player.id)),
        ],
    ]
    if whois_access:
        buttons[0].append(InlineKeyboardButton("Репорты",
                                               callback_data="pr_reports_history_{}".format(player.id)),)
    if self_request:
        buttons.append([
            InlineKeyboardButton("🔥Опыт", callback_data="pr_exp_{}".format(player.id)),
            InlineKeyboardButton("⚙️Настройки", callback_data="pr_settings_{}".format(player.id)),
        ])
    return InlineKeyboardMarkup(buttons)


def get_profile_settings_buttons(player):
    buttons = [
        [
            InlineKeyboardButton("🛒Уведомления о продаже", callback_data="prssoldnotify_{}".format(player.id)),
            InlineKeyboardButton("📦Изменения стока", callback_data="prsstocknotify_{}".format(player.id)),
        ],
        [
            InlineKeyboardButton("📌Пинг на мобов", callback_data="prsmobsping_{}".format(player.id)),
        ],
    ]
    # if player.game_class == 'Ranger' and player.class_skill_lvl is not None:
    if player.class_skill_lvl is not None:
        buttons[1].append(InlineKeyboardButton("📌Пинг на аим", callback_data="prsaimping_{}".format(player.id)))
    return InlineKeyboardMarkup(buttons)


def get_edit_guild_buttons(guild):
    buttons = [
        [
            InlineKeyboardButton("Изменить командира", callback_data="gccmdr_{}".format(guild.id)),
            InlineKeyboardButton("Изменить чат гильдии", callback_data="gccht_{}".format(guild.id)),
            InlineKeyboardButton("Изменить дивизион", callback_data="gcdvs_{}".format(guild.id)),
        ],
        [
            InlineKeyboardButton("Отключить /mailing" if guild.mailing_enabled else "Включить /mailing",
                                 callback_data="gcm_{}".format(guild.id)),
            InlineKeyboardButton("Отключить приказы" if guild.orders_enabled else "Включить приказы",
                                 callback_data="gco_{}".format(guild.id)),
        ],
        [
            InlineKeyboardButton("Отключить пины" if guild.pin_enabled else "Включить пины",
                                 callback_data="gcp_{}".format(guild.id)),
            InlineKeyboardButton("Включить уведомления" if guild.disable_notification else "Выключить уведомления",
                                 callback_data="gcn_{}".format(guild.id)),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def get_guild_inline_buttons(guild: Guild, page):
    commander = Player.get_player(guild.commander_id) if guild.commander_id is not None else "Нет"
    buttons = [
        [
            InlineKeyboardButton(
                text="🎗:{} @{} ⚔️{}🛡{}".format(
                    commander.nickname, commander.username, commander.attack, commander.defense) if
                    isinstance(commander, Player) else "Нет командира", callback_data="gccmdr_{}".format(guild.id))
        ],
        [
            InlineKeyboardButton("Чат: {}".format(guild.chat_name or "Нет"), callback_data="gccht_{}".format(guild.id)),
        ],
        [
            InlineKeyboardButton("Дивизион: {}".format(guild.division),
                                 callback_data="guild_change_division_{}_page_{}".format(guild.id, page))
        ],
        [
            InlineKeyboardButton("Отключить /mailing" if guild.mailing_enabled else "Включить /mailing",
                                 callback_data="gcm_{}_new_page_{}".format(guild.id, page)),
        ],
        [
            InlineKeyboardButton("Отключить приказы" if guild.orders_enabled else "Включить приказы",
                                 callback_data="gco_{}_new_page_{}".format(guild.id, page)),
        ],
        [
            InlineKeyboardButton("Отключить пины" if guild.pin_enabled else "Включить пины",
                                 callback_data="gcp_{}_new_page_{}".format(guild.id, page)),
        ],
        [
            InlineKeyboardButton("Включить уведомления" if guild.disable_notification else "Выключить уведомления",
                                 callback_data="gcn_{}_new_page_{}".format(guild.id, page)),
        ],

        [
            InlineKeyboardButton("↩️Назад", callback_data="guilds_divisions_page_{}".format(page))
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def get_alliance_inline_buttons(alliance: Alliance):
    buttons = [
        [
            InlineKeyboardButton("📊Статистика по уровням", callback_data="ga_stats_{}".format(alliance.id)),
        ],
    ]
    return buttons



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
            InlineKeyboardButton("🏷Снаряжение", callback_data="gieq_{}".format(guild.id)),
            InlineKeyboardButton("Покинуть гильдию", callback_data="gilv_{}".format(guild.id)),
        ],
    ]
    if user_id is not None and guild.check_high_access(user_id):
        buttons.insert(0, [
            InlineKeyboardButton("Заместители", callback_data="giass_{}".format(guild.id)),
            InlineKeyboardButton("Репорты", callback_data="girep_{}".format(guild.id)),
            InlineKeyboardButton("Настройки", callback_data="giset_{}".format(guild.id)),
        ])
    return InlineKeyboardMarkup(buttons)


def get_guild_settings_buttons(guild):
    buttons = [
        [
            InlineKeyboardButton("{} выдачу ресурсов".format("Отключить" if guild.settings is not None and
                                                             guild.settings.get("withdraw") else "Включить"),
                                 callback_data="gswith_{}".format(guild.id)),
            InlineKeyboardButton("{} снятие пина".format("Отключить" if guild.settings is not None and
                                                         guild.settings.get("unpin") else "Включить"),
                                 callback_data="gsunpin_{}".format(guild.id)),
        ],
        [
            InlineKeyboardButton("{} напоминалку в 12".format("Отключить" if guild.settings is not None and
                                                              guild.settings.get("arena_notify") else "Включить"),
                                 callback_data="gsarenanotify_{}".format(guild.id)),
            InlineKeyboardButton("{} пинги к битве".format("Отключить" if guild.settings is not None and
                                                           guild.settings.get("battle_notify") else "Включить"),
                                 callback_data="gsbattlenotify_{}".format(guild.id)),
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def get_update_history_buttons(update_id, last_update_id):
    buttons = [[]]
    if update_id != 1:
        buttons[0].append(InlineKeyboardButton("⬅️️", callback_data="uhl_{}".format(update_id)))
    if update_id != last_update_id:
        buttons[0].append(InlineKeyboardButton("➡️️", callback_data="uhr_{}".format(update_id)))
    return InlineKeyboardMarkup(buttons)


def get_tops_buttons(stat, curr='all'):
    buttons = [
        [
            InlineKeyboardButton("{}ВСЕ".format('✅' if curr == 'all' else ""), callback_data="top_{}_all".format(stat)),
            InlineKeyboardButton("{}⚗️".format('✅' if curr == '⚗️' else ""), callback_data="top_{}_⚗️".format(stat)),
            InlineKeyboardButton("{}⚒".format('✅' if curr == '⚒' else ""), callback_data="top_{}_⚒".format(stat)),
        ],
        [
            InlineKeyboardButton("{}📦".format('✅' if curr == '📦' else ""), callback_data="top_{}_📦".format(stat)),
            InlineKeyboardButton("{}🏹".format('✅' if curr == '🏹' else ""), callback_data="top_{}_🏹".format(stat)),
            InlineKeyboardButton("{}⚔️".format('✅' if curr == '⚔️' else ""), callback_data="top_{}_⚔️".format(stat)),
            InlineKeyboardButton("{}🛡".format('✅' if curr == '🛡' else ""), callback_data="top_{}_🛡".format(stat)),
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def get_roulette_tops_buttons(curr=""):
    buttons = [
        [
            InlineKeyboardButton("{}🔘Выиграно".format('✅' if curr == 'roulette_won' else ""),
                                 callback_data="roulette_top_won"),
            InlineKeyboardButton("{}🏆Игр выиграно".format('✅' if curr == 'roulette_games_won' else ""),
                                 callback_data="roulette_top_games_won"),
            InlineKeyboardButton("{}🎰Игр сыграно".format('✅' if curr == 'roulette_games_played' else ""),
                                 callback_data="roulette_top_games_played"),
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def get_craft_buttons(code, count, explicit=True):
    buttons = [
        [
            InlineKeyboardButton("📦Выдать всё", callback_data="craft_withdraw_{}_{}".format(code, count)),
            InlineKeyboardButton("💰Купить всё", callback_data="craft_buy_{}_{}".format(code, count)),
        ],
        [
            InlineKeyboardButton("{} ресурсы в наличии".format("⬆Скрыть" if explicit else "⬇Показать"),
                                 callback_data="craft_{}_{}_{}".format("fewer" if explicit else "more", code, count))
        ],[
            InlineKeyboardButton("⚒Крафт!", callback_data="craft_go_{}_{}".format(code, count))
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def get_vote_buttons(vote, choice=None):
    buttons = []
    for i, var in enumerate(vote.variants):
        buttons.append([InlineKeyboardButton(text=var, callback_data="vote_{}_{}".format(vote.id, i))])
    if choice is not None:
        buttons[choice][0].text = '✅' + buttons[choice][0].text
    return InlineKeyboardMarkup(buttons)


# Функция, которая возвращает кнопки для любого статуса. Принимает на вход user_data, в котором читает поле "status",
# далее генерирует и возвращает кнопки
def get_general_buttons(user_data, player=None, only_buttons=False):
    status = user_data.get("status")
    rp_off = user_data.get("rp_off")
    buttons = None
    if rp_off and status in ["central_square", "rp_off"]:
        buttons = [
            [
                KeyboardButton("👀 Профиль"),
                KeyboardButton("👥 Гильдия"),
                KeyboardButton("📈Топы"),
            ],
            [
                KeyboardButton("🔖Связь с МИД"),
                KeyboardButton("🗂Обновления"),
                KeyboardButton("📰Инструкция"),
            ]
        ]
        if player is not None:
            if player.guild is not None:
                guild = Guild.get_guild(player.guild)
                if guild is not None:
                    if guild.check_high_access(player.id):
                        pass
                        # buttons[0].append(KeyboardButton("📜Список гильдий"))
    elif status is None or status in ["default", "central_square"]:
        status = "central_square"
        user_data.update({"status": status})
        buttons = [
            [
                KeyboardButton(Location.get_location(1).name),
                KeyboardButton(Location.get_location(2).name),
                KeyboardButton("⛩ Врата замка"),
                ],
            [
                KeyboardButton("🔭 Башня ТехМаг наук"),  # ❗
                KeyboardButton("🏤Мандапа Славы"),
                # KeyboardButton("📈Топы"),
                # KeyboardButton("🏚 Не построено"),
            ],
            [
                KeyboardButton("↔️ Подойти к указателям"),
                KeyboardButton("🏚 Стройплощадка"),
                # KeyboardButton("↩️ Назад"),
            ]
        ]
        # Стройка Мандапы Славы окончена
        # hall = Location.get_location(8)
        # if hall is not None and hall.is_constructed():
        #     buttons[1].insert(1, KeyboardButton("🏤Мандапа Славы"))

        tea_party = Location.get_location(9)
        if tea_party is not None and tea_party.is_constructed():
            buttons[1].insert(2, KeyboardButton("🍵Чайная лига"))

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
        if player is not None:
            if player.guild is not None:
                guild = Guild.get_guild(player.guild)
                if guild is not None:
                    if guild.alliance_id is not None:
                        buttons.insert(1, [KeyboardButton(" 🤝Альянс")])
                    if guild.check_high_access(player.id):
                        pass
                        # buttons.insert(1, [KeyboardButton("📜Изучить список гильдий")])
    elif status == 'throne_room':
        buttons = [
            [
                KeyboardButton("Обратиться к командному составу"),
                KeyboardButton("Попросить аудиенции у 👑Короля"),
                ],
            [
                KeyboardButton("🎇Посмотреть на портреты"),
                # KeyboardButton("💰Сокровищница"),
            ],
            [
                KeyboardButton("↩️ Назад"),
            ]
        ]
        if player is not None and check_access(player.id):
            buttons[1].append(KeyboardButton("Штаб"))
        if player is not None and player.id in [king_id, SUPER_ADMIN_ID]:
            buttons[1].append(KeyboardButton("Кабинет Короля"))
    elif status in ['mid_feedback', 'duty_feedback', 'sending_guild_message', 'editing_debrief',
                    'changing_castle_message', 'sending_bot_guild_message', 'editing_update_message', "treasury",
                    "awaiting_roulette_bet"]:
        buttons = [
            [
                KeyboardButton("↩️ Назад"),
            ]
        ]
    elif status in ["sawmill", "quarry", "construction", "exploration", "pit"]:
        buttons = [
            [
                KeyboardButton("👀 Профиль"),
            ],
            [
                KeyboardButton("↩️ Отмена"),
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
                    KeyboardButton("🌲Лесопилка"),
                    KeyboardButton("⛰Каменоломня"),
                ],
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
                KeyboardButton("Начать стройку"),
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
    elif status == 'technical_tower':
        buttons = [
            [
                # KeyboardButton("🔖Обратиться к магу"),
                KeyboardButton("📰Манускрипт"),
                KeyboardButton("🗂Архив объявлений"),
            ],
            [
                KeyboardButton("🧾История коммитов"),
            ],
            [
                KeyboardButton("↩️ Назад"),
            ]
        ]
        if player is not None and player.id == SUPER_ADMIN_ID:
            buttons[1].insert(1, KeyboardButton("💻Кабинет ботодела"))
    elif status == 'my_cabinet':
        buttons = [
            [
                KeyboardButton("📈Выкатить обнову"),
                KeyboardButton("📣Рассылка по гильдиям"),
            ],
            [
                KeyboardButton("↩️ Назад"),
            ]
        ]
    elif status == 'construction_plate':
        location = Location.get_location(status_to_location.get(status))
        buttons = location.buttons
    elif status == 'hall_of_fame':
        buttons = [
            [
                KeyboardButton("📈Топы"),
                # KeyboardButton("📣Ещё кнопка, хз что"),
            ],
            [
                KeyboardButton("↩️ Назад"),
            ]
        ]
    elif status == 'tops':
        buttons = [
            [
                KeyboardButton("⚔️Атака"),
                KeyboardButton("🛡Защита"),
                KeyboardButton("🔥Опыт"),
            ],
            [
                KeyboardButton("↩️ Назад"),
            ]
        ]
        if not rp_off:
            buttons.insert(1, [
                KeyboardButton("🌲Дерево"),
                KeyboardButton("⛰Камень"),
                KeyboardButton("🏚Стройка"),
            ])
    elif status == 'manuscript':
        buttons = [
            [
                KeyboardButton("👤Игроки"),
                KeyboardButton("👥Гильдии"),
                KeyboardButton("📓Гайды"),
            ],
            [
                KeyboardButton("🖋Триггеры"),
                KeyboardButton("📦Сток"),
                # KeyboardButton("🏠Профсоюзы"),
            ],
            [
                KeyboardButton("↩️ Назад"),
            ]
        ]
        if not rp_off:
            buttons[1].insert(0, KeyboardButton("↔️Указатели"))
    elif status == 'guides':
        buttons = [
            [
                KeyboardButton("⚗️Алхимик"),
                KeyboardButton("⚒Кузнец"),
                KeyboardButton("📦Добытчик"),
            ],
            [
                KeyboardButton("🏹Лучник"),
                KeyboardButton("⚔Рыцарь"),
                KeyboardButton("🛡Защитник"),
            ],
            [
                KeyboardButton("↩️ Назад"),
            ]
        ]
    elif status == 'tea_party':
        buttons = [
            # [
            # KeyboardButton("Разведка"),
            # KeyboardButton("Рыть котлован"),
            # ],
            [
                KeyboardButton("🎰Рулетка"),
                KeyboardButton("💲Магазин статусов"),
            ],
            [
                KeyboardButton("🧳Контрабандист"),
            ],
            [
                KeyboardButton("↩️ Назад"),
            ],
        ]
    elif status == 'roulette':
        buttons = [
            [
                KeyboardButton("🔸Сделать ставку"),
                KeyboardButton("📈Топы в рулетке"),
            ],
            [
                KeyboardButton("↩️ Назад")
            ],
        ]
    if only_buttons or buttons is None:
        return buttons
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def get_text_to_general_buttons(user_data, player=None):
    """
    Возвращает текст, который нужно отправить по умолчанию с статусом в user_data
    :param user_data: Словарь user_data, функция использует значения 'status' и 'rp_off'
    :param player: Player
    :return: Str
    """
    status = user_data.get("status")
    location_id = user_data.get("location_id")
    rp_off = user_data.get("rp_off")
    if location_id is None:
        user_data.update({"location_id": 0})
    print(rp_off, status)
    if rp_off and status in ["central_square", "rp_off"]:
        return "Доброго времени суток!\nВыберите действие:"
    if status is None or status == "default":
        return "Вы входите в замок Скалы. Выберите, куда направиться!"
    if status in ["construction", "sawmill", "quarry"]:
        if player is not None:
            j = construction_jobs.get(player.id)
            if j is not None:
                seconds_left = j.get_time_left()
                return "Вы заняты делом. Окончание через <b>{:02.0f}:{:02.0f}</b>".format(seconds_left // 60,
                                                                                          (seconds_left % 60) // 1)
    if location_id is not None:
        return Location.get_location_enter_text_by_id(location_id, player=player)


def send_general_buttons(user_id, user_data, bot=None):
    if bot is None:
        bot = dispatcher.bot
    player = Player.get_player(user_id)
    bot.send_message(chat_id=user_id, text=get_text_to_general_buttons(user_data, player=player),
                     reply_markup=get_general_buttons(user_data, player=player), parse_mode='HTML')
