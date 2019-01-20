import pytz
import tzlocal
import psycopg2
import datetime

from libs.bot_async_messaging import AsyncBot, order_backup_queue
from libs.updater_async import AsyncUpdater
from config import Production_token, psql_creditals, request_kwargs

admin_ids = [231900398, 205356091]

castles = ['🍆', '🍁', '☘', '🌹', '🐢', '🦇', '🖤']
times = ["⚠️", "58", "59", "30", "40", "45"]
times_to_time = [None, datetime.timedelta(minutes=2), datetime.timedelta(minutes=1),
                 datetime.timedelta(seconds=30), datetime.timedelta(seconds=20), datetime.timedelta(seconds=15)]

CALLBACK_CHAT_ID = 231900398

bot = AsyncBot(token=Production_token, workers=16, request_kwargs=request_kwargs)
""" Понимаю, что 16 - колоссальное число,
    Однако тесты показали, что именно так достигается оптимальное время """
updater = AsyncUpdater(bot = bot)

dispatcher = updater.dispatcher
job = updater.job_queue

conn = psycopg2.connect("dbname={0} user={1} password={2}".format(psql_creditals['dbname'], psql_creditals['user'], psql_creditals['pass']))
conn.set_session(autocommit = True)
cursor = conn.cursor()


moscow_tz = pytz.timezone('Europe/Moscow')
try:
    local_tz = tzlocal.get_localzone()
except pytz.UnknownTimeZoneError:
    local_tz = pytz.timezone('Europe/Andorra')
