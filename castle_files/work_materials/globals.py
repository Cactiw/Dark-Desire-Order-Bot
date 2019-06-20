import pytz
import tzlocal
import psycopg2

from config import Production_castle_token, request_kwargs, psql_creditals
from libs.updater_async import AsyncUpdater
from castle_files.libs.bot_async_messaging import AsyncBot

castles = ['🍆', '🍁', '☘', '🌹', '🐢', '🦇', '🖤']

classes_list = ['Alchemist', 'Blacksmith', 'Collector', 'Ranger', 'Knight', 'Sentinel', 'Master', 'Esquire']
classes_to_emoji = {'Alchemist': '⚗️', 'Blacksmith': '⚒', 'Collector': '📦', 'Ranger': '🏹', 'Knight': '⚔️',
                    'Sentinel': '🛡', 'Esquire': '🗡', 'Master': '⛏'}
"""class_chats = {'Alchemist': -1001266047716, 'Blacksmith': -1001417227000, 'Collector': -1001302539982,
               'Ranger': -1001234986771, 'Knight': -1001488789603, 'Sentinel': -1001183827542}"""
class_chats = {'Alchemist': -1001438734208, 'Blacksmith': -1001164490198, 'Collector': -1001439849094,
               'Ranger': -1001189370559, 'Knight': -1001479145097, 'Sentinel': -1001165430197}

bot = AsyncBot(token=Production_castle_token, workers=8, request_kwargs=request_kwargs)
updater = AsyncUpdater(bot=bot)

dispatcher = updater.dispatcher
job = updater.job_queue

conn = psycopg2.connect("dbname={0} user={1} password={2}".format(psql_creditals['dbname'], psql_creditals['user'],
                                                                  psql_creditals['pass']))
conn.set_session(autocommit=True)
cursor = conn.cursor()

DEFAULT_CASTLE_STATUS = 'central_square'

CHAT_WARS_ID = 265204902
SUPER_ADMIN_ID = 231900398
high_access_list = [231900398, 205356091]
# king_id = SUPER_ADMIN_ID  # TODO сделать механику Короля
king_id = 320474708
MID_CHAT_ID = -1001351185651
SENTINELS_DUTY_CHAT_ID = -1001417510202
CENTRAL_SQUARE_CHAT_ID = -1001142055838
CASTLE_BOT_ID = 756892778
RESULTS_PARSE_CHANNEL_ID = 1369273162
MERC_ID = 105907720
MY_CHANNEL_ID = -1001341013464

construction_jobs = {}


allowed_list = []

processing = False
began = False

moscow_tz = pytz.timezone('Europe/Moscow')
try:
    local_tz = tzlocal.get_localzone()
except pytz.UnknownTimeZoneError:
    local_tz = pytz.timezone('Europe/Andorra')
