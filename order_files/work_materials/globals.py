import pytz
import tzlocal
import psycopg2

from order_files.libs.bot_async_messaging import AsyncBot
from libs.updater_async import AsyncUpdater
from config import Production_order_token, psql_creditals, request_kwargs, proxy, ServerIP, CONNECT_TYPE

from libs.database import Conn

from aiogram import Bot, Dispatcher, executor, types, utils
from aiogram.utils import exceptions

admin_ids = [231900398, 205356091, 352318827]
allowed_chats = [231900398, -1001139194354, -376246101]

CALLBACK_CHAT_ID = -1001351185651
LOGS_CHAT_ID = -1001461190292

MAX_MESSAGE_LENGTH = 4096

bot = Bot(Production_order_token, proxy=proxy)
dispatcher = Dispatcher(bot)

# bot = AsyncBot(token=Production_order_token, workers=25, request_kwargs=request_kwargs)
# """ Понимаю, что 16 - колоссальное число,
#     Однако тесты показали, что именно так достигается оптимальное время """
# updater = AsyncUpdater(bot=bot)
#
# dispatcher = updater.dispatcher
# job = updater.job_queue

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
