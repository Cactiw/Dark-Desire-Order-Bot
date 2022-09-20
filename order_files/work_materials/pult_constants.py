import datetime

divisions = ['West', 'Center', 'East', 'South', 'All attackers', 'Trust', 'Academy', 'ALL']  # 'Archers',

castles = ['🌑', '🐺', '🥔', '🦅', '🦈', '🐉', '🐢', '☘️', '🦌Def!🛡']

times = ["⚠️", "58", "59", "30", "45", "50"]
times_to_time = [None, datetime.timedelta(minutes=2), datetime.timedelta(minutes=1),
                 datetime.timedelta(seconds=30), datetime.timedelta(seconds=15), datetime.timedelta(seconds=10)]

tactics = ["/t\n🐢", "/t\n☘️", "/t\n🌑", "/t\n🐺", "/t\n🥔", "/t\n🦅", "/t\n🦈", "/t\n🐉", ""]
tactics_to_order = ["/tactics_tortuga", "/tactics_rampart", "/tactics_moonlight", "/tactics_wolfpack",
                    "/tactics_potato", "/tactics_highnest", "/tactics_sharkteeth", "/tactics_dragonscale",
                    ""]
tactics_order_to_emoji = {"/tactics_tortuga": "🐢", "/tactics_moonlight": "🌑", "/tactics_wolfpack": "🐺",
                          "/tactics_potato": "🥔", "/tactics_highnest": "🦅", "/tactics_sharkteeth": "🦈",
                          "/tactics_dragonscale": "🐉", "/tactics_rampart": "☘️",
                          "": ""}

defense = ["Def home 🖤", "Attack!", ""]
defense_to_order = ["🦌Def!🛡", "Attack!", None]

potions = ["⚗️ Atk", "⚗️ Def"]
potions_to_order = ["Drink ⚔️ATK ⚗️potions!\n"
                    "<a href=\"https://t.me/share/url?url=/misc rage\">⚔️Rage</a>\n"
                    "<a href=\"https://t.me/share/url?url=/misc morph\">⚗Morph</a>\n\n",
                    "Drink 🛡DEF ⚗️potions!\n"
                    "<a href=\"https://t.me/share/url?url=/misc peace\">🛡Peace</a>\n"
                    "<a href=\"https://t.me/share/url?url=/misc morph\">⚗Morph</a>\n\n"]

pult_status_default = {'divisions': [False, False, False, False, False, False, False, True], 'target': -1, 'defense': 2,
                       'time': -1, "tactics": 8}
