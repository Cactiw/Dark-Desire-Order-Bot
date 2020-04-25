import pytz
import tzlocal
import psycopg2
import threading

from config import Production_castle_token, request_kwargs, psql_creditals, cwuser, ServerIP, CONNECT_TYPE
from libs.updater_async import AsyncUpdater
from castle_files.libs.bot_async_messaging import AsyncBot

from libs.database import Conn

try:
    from config import enable_api, enable_telethon
except ImportError:
    enable_api = True
    enable_telethon = True

castles = ['🍆', '🍁', '☘', '🌹', '🐢', '🦇', '🖤']
emodji_to_castle_names = {'🍆': 'ferma', '🍁': 'amber', '☘': 'oplot', '🌹': 'rassvet', '🐢': 'tortuga', '🦇': 'night',
                          '🖤': 'skala'}

classes_list = ['Alchemist', 'Blacksmith', 'Collector', 'Ranger', 'Knight', 'Sentinel', 'Master', 'Esquire']
classes_to_emoji = {'Alchemist': '⚗️', 'Blacksmith': '⚒', 'Collector': '📦', 'Ranger': '🏹', 'Knight': '⚔️',
                    'Sentinel': '🛡', 'Esquire': '🗡', 'Master': '⛏', 'Воин': '🗡'}
classes_to_emoji_inverted = dict(zip(classes_to_emoji.values(), classes_to_emoji.keys()))

# class_chats = {'Alchemist': -1001438734208, 'Blacksmith': -1001164490198, 'Collector': -1001439849094,
#                'Ranger': -1001189370559, 'Knight': -1001479145097, 'Sentinel': -1001165430197}
# class_chats = {'Alchemist': -1001438734208, 'Blacksmith': -1001164490198, 'Collector': -1001439849094,
#                'Ranger': -1001189370559, 'Knight': -1001479145097, 'Sentinel': -1001165430197}
class_chats = {'Alchemist': -1001303783942, 'Blacksmith': -1001164490198, 'Collector': -1001254394389,
               'Ranger': -1001439995849, 'Knight': -1001289110366, 'Sentinel': -1001165430197}

bot = AsyncBot(token=Production_castle_token, workers=16, request_kwargs=request_kwargs)
updater = AsyncUpdater(bot=bot)

dispatcher = updater.dispatcher
job = updater.job_queue

bot.dispatcher = dispatcher

API_APP_NAME = cwuser
conn = Conn(psql_creditals)
conn.start()
cursor = conn.cursor()

DEFAULT_CASTLE_STATUS = 'central_square'

HOME_CASTLE = "🖤"

SKIPPED_DIVISIONS = ["Луки", "Траст"]

CHAT_WARS_ID = 265204902
SUPER_ADMIN_ID = 231900398
high_access_list = [231900398, 205356091]
# king_id = SUPER_ADMIN_ID  # TODO сделать механику Короля
king_id = 205356091
MID_CHAT_ID = -1001351185651
# MID_CHAT_ID = -1001346136061
# SENTINELS_DUTY_CHAT_ID = -1001291931253
SENTINELS_DUTY_CHAT_ID = -1001417510202
CENTRAL_SQUARE_CHAT_ID = -1001159705184
# CENTRAL_SQUARE_CHAT_ID = -1001346136061  # test
CASTLE_CHAT_ID = -1001250480643
# CASTLE_CHAT_ID = -1001346136061
CASTLE_BOT_ID = 756892778
RESULTS_PARSE_CHANNEL_ID = 1369273162
# RESULTS_PARSE_CHANNEL_ID = 1353017829  # Test channel
WORLDTOP_CHANGES_CHANNEL_ID = -1001357229904
SON_CHAT_ID = -1001387934680
ACADEMY_HQ_CHAT_ID = -1001159189851
STATUSES_MODERATION_CHAT_ID = -1001309812116
# STATUSES_MODERATION_CHAT_ID = -1001346136061  # test
MOB_CHAT_ID = -1001488531141
MERC_ID = 105907720
MY_CHANNEL_ID = -1001341013464

construction_jobs = {}
castle_chats = []


mobs_lock = threading.Lock()
mobs_messages: {str: [{}]} = {}

allowed_list = []

processing = False
began = False

moscow_tz = pytz.timezone('Europe/Moscow')
try:
    local_tz = tzlocal.get_localzone()
except pytz.UnknownTimeZoneError:
    local_tz = pytz.timezone('Europe/Andorra')
utc = pytz.utc
