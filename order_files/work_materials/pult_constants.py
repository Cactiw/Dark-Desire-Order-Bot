import datetime

divisions = ['Запад', 'Центр', 'Восток', 'Все атакеры', 'Луки', 'ВСЕ']

castles = ['🍆', '🍁', '☘', '🌹', '🐢', '🦇', '🖤']

times = ["⚠️", "58", "59", "30", "40", "45"]
times_to_time = [None, datetime.timedelta(minutes=2), datetime.timedelta(minutes=1),
                 datetime.timedelta(seconds=30), datetime.timedelta(seconds=20), datetime.timedelta(seconds=15)]

tactics = ["/t\n🐢", "/t\n🌹","/t\n🦇","/t\n🍁", "/rand", ""]
tactics_to_order = ["/tactics_tortuga", "/tactics_rassvet", "/tactics_night", "/tactics_amber", "/tactics_random", ""]

defense = ["Деф дома 🖤", "В атаку!", ""]
defense_to_order = ["🖤", "Attack!", None]

potions = ["⚗️ Атака", "⚗️ Деф"]
potions_to_order = ["Пьем ⚔️АТК ⚗️зелья\nVial of Rage: <a href=\"https://t.me/share/url?url=/use_p01\">/use_p01</a>\n"
                    "Potion of Rage: "
                    "<a href=\"https://t.me/share/url?url=/use_p02\">/use_p02</a>\nBottle of Rage: "
                    "<a href=\"https://t.me/share/url?url=/use_p03\">/use_p03</a>\n\n",
                    "Пьем 🛡ДЕФ ⚗️зелья\nVial of Peace: <a href=\"https://t.me/share/url?url=/use_p04\">/use_p04</a>\n"
                    "Potion of Peace: "
                    "<a href=\"https://t.me/share/url?url=/use_p05\">/use_p05</a>\nBottle of Peace: "
                    "<a href=\"https://t.me/share/url?url=/use_p06\">/use_p06</a>\n\n"]

pult_status_default = {'divisions': [False, False, False, False, False, True], 'target': -1, 'defense': 2,
                       'time': -1, "tactics": 5}
