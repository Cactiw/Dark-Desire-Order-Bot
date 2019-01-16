import pytz
import tzlocal
import psycopg2

from libs.bot_async_messaging import AsyncBot
from libs.updater_async import AsyncUpdater
from config import Production_token, psql_creditals


bot = AsyncBot(token=Production_token, workers=8)
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