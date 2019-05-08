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


pult_status_default = {'divisions': [False, False, False, False, False, True], 'target': -1, 'defense': 2,
                       'time': -1, "tactics": 5}
