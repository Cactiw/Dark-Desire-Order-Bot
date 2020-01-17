

faq_texts = {
    "↔️Указатели": """<b>Казарма</b> 

<code>Посмотреть в зеркало</code> - отображает Ваш текущий профиль в боте. 
<code>История гильдий</code> - отображает список последних 10 гильдий, в которых Вы состояли. 

<code>Посмотреть ведомость гильдии</code> - отображает информацию о Вашей гильдии. По нажатию на “Вступить” можно перейти в привязанный гильдейский чат. 
<code>	Заместители</code> - отображает список заместителей гм.  
<code>	Репорты</code> - возвращает статистику гильдии по последней битве. Отображает список сданных репортов и список участников, которые их еще не сдали. 
<code>	Настройки </code> - Различные настройки гильдии (отключение выдачи ресурсов в чате и другое)
<code>	Список игроков</code> - возвращает список игроков Вашей гильдии. Есть возможность просмотреть профиль по нажатию на соответствующий /view_profile_{ID игрока}, а также удалить из гильдии - /remove_player_{ID игрока}. 
<code>	Покинуть гильдию</code> - удаляет Вас из гильдии. 

<b>Тронный зал</b> 

Здесь можно посмотреть последний написанный дебриф. 

<code>Обратиться к командному составу</code> - следующее написанное сообщение будет отправлено в чат МИДа. Не работает при скрытом профиле в телеграмме. 
<code>Попросить аудиенции у 👑Короля</code> - будет отправлено Королю уведомление с пингом.
<code>Посмотреть на портреты</code> - отображает список текущего состава МИДа. 

<b>Врата замка</b>

<code>Обратиться к 💂‍♂Стражам</code> - следующее написанное сообщение будет отправлено стражникам на вахте. Они могут по желанию ответить Вам непосредственно в боте. Не работает при скрытом профиле в телеграмме. 
<code>Лесопилка</code> - отправляет Вас добывать дерево для казны замка на 3 минуты. 
<code>Каменоломня</code> - отправляет Вас добывать камень для казны замка на 3 минуты. 

<b>Башня ТехМаг наук</b>
	
Здесь можно посмотреть последние новости от разработчика бота. 

<code>Архив объявлений</code> - хранит в себе историю всех обновлений. Перемещаться можно стрелочками вперед и назад. 

<b>Мандапа Славы</b>
	
<code>Топы</code> - отображает топов замка по категориям: Атака, Защита, Дерево, Камень, Стройка. Внутри каждой категории работают классовые фильтры.
""",
    "👤Игроки": """
/dokument (от /vashi_dokumenty)
/document
/dok
/doc
возвращает в боте профиль игрока. Работает на автора реплайнутого сообщения и по игровому нику как с тегом гильдии, так и без него (например, сработает как /doc [SVN]Vamik76, так и /doc Vamik76), а также по юзерке (ex. /doc @username). 
""",
    "👥Гильдии": """<b>Готовность к битве</b>
Бот умеет пинговать на битвы тех, кто отдыхает и не становится по пину (отдых, квесты, лавки и пр). 
Для этого в чат гильдии необходимо скинуть список игроков гильдии (👥Гильдия -> 📋Состав) и выбрать /notify_guild_sleeping. 
Работает за полчаса и менее до битвы. Сообщение должно быть не старше двух минут. 
Доступ есть только у админов чата гильдии. 

<b>Напоминание лучникам о битве</b>
Также существует возможность отдельных пингов для лучников в зависимости от уровня Aiming. 
Для активации необходимо обновить информацию о классе в боте (если ещё не сделали этого), и уже после этого скинуть боту форвард ответа на /class. 
За посчитанное время до битвы начнут приходить персональные уведомления в чат гильдии.
""",
    "🖋Триггеры": """/create_trigger {текст триггера} — создать локальный триггер
/delete_trigger {текст триггера} — удалить локальный триггер
/triggers — список триггеров, как локальных, так и глобальных
/info_trigger {текст триггера} — информация о триггере, очень полезно, когда в чате много триггеров, а необходимо посмотреть, кто и когда создал конкретный
/replace_trigger {текст триггера — удаляет и тут же создаёт новый триггер вместо старого. Полезно, например, при обновлении информации о выпадении вещей в чв.
""",
    "📦Сток":"""
<b>1. Выдача ресурсов</b>
При отправке сообщения с нехватающими ресурсами для крафта в чат с ботом или в самого бота, отправляет нужную команду в ответ. (/g_withdraw)

<b>2. Депозит всего в ги</b>
Для получения команд на депозит, достаточно отправить в бота форварды /stock /misc или 🛎Аукцион — для кусков, рецептов и свитков.

<b>3. Подсчёт, сколько и какого шмота, можно скрафтить в данный момент</b>
При отправке в бота форварда рецептов и кусков, находящихся в гильдии (/g_stock_rec и /g_stock_parts, именно в данном порядке) Бот отвечает списком тех вещей, на которые хватает рецептов и кусков для крафта.

<b>4. Выдача ресурсов для ГМ-ов и Стокменов</b>
Функция нацелена для быстрого вывода всех необходимых ресурсов, находящиеся в гильдии. 
Для начала, необходимо уставить список ресурсов командой /set_withdraw_res { коды ресурсов }
После чего отправить в бота форвард из игрового бота /g_stock_res
Бот отправит команду на выдачу всех выбранных ресурсов, которые имеются в ги.

<b>5. Вывод дропа с квестов, отслеживающий настоящее время в игре</b>
Для использования команды, достаточно отравить в бота или в чате с ним данные команды: 
/d2 — отображает дроп 📗Tier 2, например, Hunter и т.д.
/dc — отображает дроп оружий, которые не попадают под дроп Т3, такие, как Thundersoul Sword. 
/d3 — отображает дроп 📘Tier 3 — Lion и т.д.
/d4 — отображает дроп 📙Tier 4, Griffin, в том числе и плащи.

<b>6. Поиск дропа, указывающий игровое время и место, где падает предмет</b>
Чтобы узнать, в какое время и где падает кусок или рецепт достаточно написать /drop {Название, не меньше трёх букв}
""",
    "🏠Профсоюзы": """<b>1.Регистрация</b>
    
Для добавления профсоюза необходимо переслать боту форвардом сообщение из чв вида
🏠Trade Union: Название
🏅Owner:Создатель
👥Members: Число людей
📈Страшный таймер
View: ссылка
/tu_leave to leave

Глава союза должен быть зарегистрирован в боте. 

<b>2. Добавление людей</b>

Затем боту можно присылать сообщения вида (опять же форвардами) 

🖤Ник 1
🖤Ник 2
🖤Ник 3
◀️  /tu_list_p9  /tu_list_p11 ▶️

И бот сам добавит в профсоюз тех людей, что в нём зарегистрированы. 

/add_to_union_user_id { id игрока } - добавляет в чат человека по айди, если он отсуствует в боте. Работает для создателя профсоюза. Рекомендуется добавлять людей стандартным способом, ибо после сброса игроков в профсоюзах придётся этих людей добавлять вручную заново.

<b>3. Привязка к чату</b>

Глава профсоюза (создатель) может указать специальный чат как чат данного профсоюза командой /set_union_chat в данном чате. После чего бот начнёт кикать всех, кто пишет в этом чате и не принадлежит профсоюзу.
 Убедитесь, что у бота есть права кикать людей. 

<b>4. Обновление состава</b>

Обновлять список людей в профсоюзе можно только кидая форварды — это единственный безопасный способ. Необходимо внимательно следить, какие форварды Вы пересылаете — бот не имеет никакой возможности проверить, это состав вашего профсоюза или нет.

<b>5. Удаление людей</b>

/clear_union_list - удаляет всех игроков из профсоюза. Постарайтесь кинуть новый список как можно скорее, ведь бот будет кикать людей, которые в нём не состоят из чата профсоюза (то есть на этот момент всех) спустя минуту после выполнения вашей команды.

<b>6. Состав</b>

/guild_union_players { Название профсоюза } -  отображает список согильдийцев, которые состоят в этом профсоюзе и тех, кто состоит в других / не состоит вовсе. Работает для гм и их замов.
Чрезвычайно удобно в случае, если вы решили одной гильдией идти в конкрентный профсоюз и хотите видеть, кто в него вступил, а кто — нет.
/guild_unions - отображает список всех игроков гильдии и профсоюзы, в которых они состоят. Работает для гм и их замов в лс бота.
/add_union_assistant { telegram id зама } - добавляет зама создателя профсоюза. Замам доступно все функции создателей.
/del_union_assistant { telegram id зама } - удаляет зама создателя профсоюза.
/union_stats - отображает статы союза. Работает для создателей и их замов. 
/top_union_attack - отображает топ-20 игроков по атаке в профсоюзе.
/top_union_defense - отображает топ-20 игроков по защите в профсоюзе.

<b>7. Битвы</b>

/split_union_attack - разделяет атаку союза в заданных пропорциях (ex. /split_union_attack 1:2:3 поделит союз на 3 части с атакой в соотношении 1 / 2 / 3).
/split_union_defense - разделяет защиту союза в заданных пропорциях (ex. /split_union_def 1:2:3 поделит союз на 3 части с защитой в соотношении 1 / 2 / 3).
/split_union_attack_full,  /split_union_defense_full  - работают как и краткие версии, однако суффикс full отображает также ник в игре, требуемую стату и сумму статов по группам. 
/split_union_attack_full_alt, /split_union_defense_full_alt - использует альтернативный алгоритм разделения атаки/защиты, обеспечивая баланс количества игроков в разных группах.
""",
                "📓Гайды": """<b>📓Гайды</b>:
                
 🛡 <b>Хранитель</b> - https://telegra.ph/Gajd-klassa-Sentinel-Skaly-08-09

 ⚔️ <b>Рыцарь</b> - https://telegra.ph/Gajd-klassa-Knight-Skaly-09-03

 🏹 <b>Лучник</b> - https://telegra.ph/Gajd-klassa-RangerSkaly-09-03

 ⚗️ <b>Алхимик</b> - https://telegra.ph/Gajd-klassa-Alchemist-Skaly-09-03
 
 📦 <b>Добытчик</b> - https://telegra.ph/Gajd-klassa-CollectorSkaly-09-03

 ⚒ <b>Кузнец</b> - https://telegra.ph/Gajd-klassa-BlacksmithSkaly-09-03""",
            "📓Guides": """<b>📓Guides</b> (only in Russian for now):
                
 🛡 <b>Sentinel</b> - https://telegra.ph/Gajd-klassa-Sentinel-Skaly-08-09

 ⚔️ <b>Knight</b> - https://telegra.ph/Gajd-klassa-Knight-Skaly-09-03

 🏹 <b>Ranger</b> - https://telegra.ph/Gajd-klassa-RangerSkaly-09-03

 ⚗️ <b>Alchemist</b> - https://telegra.ph/Gajd-klassa-Alchemist-Skaly-09-03
 
 📦 <b>Collector</b> - https://telegra.ph/Gajd-klassa-CollectorSkaly-09-03

 ⚒ <b>Blacksmith</b> - https://telegra.ph/Gajd-klassa-BlacksmithSkaly-09-03""",
                "↔️Signs": """<b>Barracks</b>

<code>Look in the mirror</code> - shows yours current profile in the bot.
<code>History of guilds</code> - shows the list of the last 10 guilds you belonged to.

<code>View Guild List</code> - shows the information on your Guild. By clicking on "Join" you can go to the attached Guild chat.
<code> Deputies</code> - shows the list of Deputies of Guild master.
<code> Reports</code> - returns Guild statistics for the last battle. Displays a list of submitted reports and a list of participants who have not yet submitted them.
<code> Settings </code> - Various Guild settings (disabling the output of resources in the chat and more).
<code> List of players</code> - returns the list of players of your Guild. It is possible to view the profile by clicking on the appropriate /view_profile_{ID of a player}, as well as remove from the Guild - /remove_player_{ID of a player}.
<code> Leave the Guild</code> - removes you from the Guild.

<b>Throne room</b>

Here you can see the last written debrief.

<code>Contact the command staff</code> - The next written message will be sent to the Foreign Ministry chat. It does not work with a hidden telegram profile.
<code>Ask an audience with 👑King</code> - A notification will be sent to the King with a ping.
<code>Look at the portraits</code> - displays a list of the current composition of the Ministry of Foreign Affairs.

<b>Castle gates</b>

<code>Refer to 💂‍♂Guards</code> - the next written message will be sent to the guards on duty. They can optionally answer you directly in the bot. It does not work with a hidden telegram profile.
<code>Sawmill</code> - sends you to mine a tree for the treasury of the castle for 3 minutes.
<code>Quarry</code> - sends you to mine a stone for the treasury of the castle for 3 minutes.


<b>TechMag Science Tower</b>

Here you can see the latest news from the bot developer.

<code>Announcement Archive</code> - keeps the history of all updates. You can move by arrows forward and backward..

<b>The Hall of Fame</b>

<code>Tops</code> - displays castle tops by categories: Attack, Defense, Wood, Stone, Construction. Within each category the class filters work.
""",
                "👤Players": """
/dokument (от /vashi_dokumenty)
/document
/dok
/doc
returns the player profile in the bot. It works for the author of the posted message and on the game nickname with or without a Guild tag (for example, will work like /doc [SVN]Vamik76, and /doc Vamik76), as well as by user (ex. /doc @username).
""",
                "👥Guilds": """<b>Battle readiness</b>
The bot is able to ping into the battles of those who rest and do not ready for battle (rest, quests, shops, etc.).
To do this, you need to drop the list of Guild players in the Guild chat (👥Guild -> 📋Ыtaff) and choose /notify_guild_sleeping.
Works half an hour or less before the battle. The message must be no older than two minutes.
Access is available only to the Guild chat admins.

<b>Reminder for the Archers on Battle</b>
There is also the possibility of separate pings for archers depending on the level of Aiming.
To activate it, you need to update the class information in the bot (if you have not done so already), and after that send to the bot forward response to / class.
In the counted time before the battle, personal notifications will begin to come to the Guild chat.
""",
                "🖋Triggers": """/create_trigger {text of trigger} — create local trigger
/delete_trigger {text of trigger} — delete local trigger
/triggers — list of triggers, both local and global
/info_trigger {text of trigger} — information about the trigger, it is very useful when there are a lot of triggers in the chat, but you need to see who created the specific one and when
/replace_trigger {text of trigger} — deletes and immediately creates a new trigger instead of the old one. It is useful, for example, when updating information about the appearance of things in the ChatWars.
""",
                "📦Stock": """
<b> 1. Resource Delivery </b>
When sending a message with insufficient resources for crafting to chat with the bot or in the bot itself, it sends the necessary command in response.(/g_withdraw)

<b> 2. Deposit of all in Guild </b>
To receive commands for a deposit, it is enough to send forwards to the bot / stock / misc or 🛎Auction - for pieces, recipes and scrolls.

<b> 3. Counting how much and what things you can craft at the moment </b>
When sending forwards of recipes and pieces in the guild to the bot ( /g_stock_rec and /g_stock_parts, in this order), the Bot responds with a list of those things that have enough recipes and pieces for crafting.

<b> 4. Resource allocation for GMs and Stockmen </b>
The function is designed to quickly display all the necessary resources that are in the guild.
First, you need to set the list of resources with the command /set_withdraw_res {codes of resources}
Then send the forward to the bot from the game bot /g_stock_res
The bot will send a command to issue all the selected resources that are in the Guild.

<b> 5. Drop derivation from quests, tracking the current time in game </b>
To use a command, it is enough to send the command data in a bot or in a chat with a bot:
/d2 — shows the drop 📗Tier 2, for example, Hunter, etc.
/dc — displays the drop of weapons that do not fit the drop of T3, such as Thundersoul Sword.
/d3 — shows the drop 📘Tier 3 — Lion, etc.
/d4 — shows the drop 📙Tier 4, Griffin, including capes.

<b> 6. Drop search indicating playing time and place where the item falls. </b>
To find out at what time and where a piece or recipe falls, just write /drop {title at least three letters}
"""
}
