from telegram.ext import Updater
import pytz
import tzlocal
import psycopg2

from order_files.libs.bot_async_messaging import AsyncBot
from libs.updater_async import AsyncUpdater
from castle_files.libs.bot_async_messaging import AsyncBot as ClassicAsyncBot
from config import Production_order_token, Production_pult_token, psql_creditals, request_kwargs, proxy

from libs.database import Conn

admin_ids = [231900398, 205356091, 352318827]
allowed_chats = [231900398, -1001139194354, -376246101]

CALLBACK_CHAT_ID = -1001351185651
LOGS_CHAT_ID = -1001461190292

MAX_MESSAGE_LENGTH = 4096

# proxy = request_kwargs.get('proxy_url') if request_kwargs is not None else None
proxy = None
order_async_bot = AsyncBot(token=Production_order_token, workers=25, proxy=proxy)
""" Понимаю, что 16 - колоссальное число,
    Однако тесты показали, что именно так достигается оптимальное время """

bot = ClassicAsyncBot(token=Production_pult_token, request_kwargs=request_kwargs, workers=1)
updater = AsyncUpdater(bot=bot)

dispatcher = updater.dispatcher
job = updater.job_queue

conn = Conn(psql_creditals)
conn.start()
cursor = conn.cursor()

order_chats = []
deferred_orders = []

order_id = 0


moscow_tz = pytz.timezone('Europe/Moscow')
try:
    local_tz = tzlocal.get_localzone()
except pytz.UnknownTimeZoneError:
    local_tz = pytz.timezone('Europe/Andorra')
print("local tz =", local_tz)
