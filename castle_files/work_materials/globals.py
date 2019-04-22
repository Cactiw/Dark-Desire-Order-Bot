import pytz
import tzlocal
import psycopg2

from config import Production_castle_token, request_kwargs, psql_creditals
from libs.updater_async import AsyncUpdater
from castle_files.libs.bot_async_messaging import AsyncBot

castles = ['🍆', '🍁', '☘', '🌹', '🐢', '🦇', '🖤']

bot = AsyncBot(token=Production_castle_token, workers=8, request_kwargs=request_kwargs)
updater = AsyncUpdater(bot=bot)

dispatcher = updater.dispatcher
job = updater.job_queue

conn = psycopg2.connect("dbname={0} user={1} password={2}".format(psql_creditals['dbname'], psql_creditals['user'], psql_creditals['pass']))
conn.set_session(autocommit=True)
cursor = conn.cursor()

CHAT_WARS_ID = 265204902
SUPER_ADMIN_ID = 231900398
high_access_list = []

processing = True

moscow_tz = pytz.timezone('Europe/Moscow')
try:
    local_tz = tzlocal.get_localzone()
except pytz.UnknownTimeZoneError:
    local_tz = pytz.timezone('Europe/Andorra')
