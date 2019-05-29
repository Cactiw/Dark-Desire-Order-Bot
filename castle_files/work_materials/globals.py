import pytz
import tzlocal
import psycopg2

from config import Production_castle_token, request_kwargs, psql_creditals
from libs.updater_async import AsyncUpdater
from castle_files.libs.bot_async_messaging import AsyncBot

castles = ['🍆', '🍁', '☘', '🌹', '🐢', '🦇', '🖤']

classes_list = ['Alchemist', 'Blacksmith', 'Collector', 'Ranger', 'Knight', 'Sentinel']
classes_to_emoji = {'Alchemist': '⚗️', 'Blacksmith': '⚒', 'Collector': '📦', 'Ranger': '🏹', 'Knight': '⚔️',
                    'Sentinel': '🛡'}

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
high_access_list = [231900398, 205356091]  # Рей, 352318827]
# king_id = SUPER_ADMIN_ID  # TODO сделать механику Короля
king_id = 205356091
MID_CHAT_ID = -1001351185651
SENTINELS_DUTY_CHAT_ID = -1001417510202
CENTRAL_SQUARE_CHAT_ID = -1001142055838
CASTLE_BOT_ID = 756892778
RESULTS_PARSE_CHANNEL_ID = 1369273162
MERC_ID = 105907720
MY_CHANNEL_ID = -1001341013464

construction_jobs = {}


allowed_list = []

processing = True

moscow_tz = pytz.timezone('Europe/Moscow')
try:
    local_tz = tzlocal.get_localzone()
except pytz.UnknownTimeZoneError:
    local_tz = pytz.timezone('Europe/Andorra')
