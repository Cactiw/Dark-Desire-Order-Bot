from telethon.sync import TelegramClient, events, connection
from telethon.tl.types import PeerChannel

from castle_files.work_materials.globals import RESULTS_PARSE_CHANNEL_ID, RESULTS_PARSE_CHANNEL_ID_DEBUG, CHAT_WARS_ID

try:
    from config import phone, username, password, api_id, api_hash
except ImportError:
    pass
try:
    from config import telethon_proxy
except ImportError:
    telethon_proxy = None

from multiprocessing import Queue

import castle_files.work_materials.globals as globals

from retrying import retry

import socks
import logging
import traceback
import asyncio

logging.getLogger('telethon').setLevel(logging.WARNING)

castles_stats_queue = Queue()

TEST_CHANNEL_ID = 1353017829

guilds_str = ""


WAIT_BEFORE_RETRY = 30
MAX_RETRIES = 5

WORLDTOP_PERIOD = 30  # minutes

client: TelegramClient = None


def not_keyboard_interrupt(exception: Exception) -> bool:
    logging.error(traceback.format_exc())
    return not isinstance(exception, KeyboardInterrupt)


# @retry(wait_fixed=WAIT_BEFORE_RETRY * 1000, retry_on_exception=not_keyboard_interrupt,
#        stop_max_attempt_number=MAX_RETRIES)
def script_work():
    global client
    session_path = "./sessions/{}".format(username)
    if telethon_proxy is not None:
        proxy = (telethon_proxy["host"], telethon_proxy["port"], telethon_proxy["secret"])
        admin_client = TelegramClient(session_path, api_id, api_hash, proxy=proxy,
                                      connection=connection.tcpmtproxy.ConnectionTcpMTProxyIntermediate)
    else:
        admin_client = TelegramClient(session_path, api_id, api_hash)
    client = admin_client
    # admin_client.start(phone, password)
    #
    # client = admin_client
    with admin_client as client:
        admin_client.get_entity("ChatWarsBot")
        client.add_event_handler(stats_handler, event=events.NewMessage)
        print("telegram script launched")
        loop = asyncio.get_event_loop()
        loop.create_task(send_worldtop())
        try:
            loop.run_until_complete(client.disconnected)
        except KeyboardInterrupt:
            pass


async def stats_handler(event):
    global guilds_str
    text = event.message.message
    if event.message.from_id != CHAT_WARS_ID:
        print("Got telegram event", event)
        print(text)
        print(event.message.to_id, [PeerChannel(RESULTS_PARSE_CHANNEL_ID), PeerChannel(RESULTS_PARSE_CHANNEL_ID_DEBUG)],
              event.message.to_id in [PeerChannel(RESULTS_PARSE_CHANNEL_ID), PeerChannel(RESULTS_PARSE_CHANNEL_ID_DEBUG)])
    if event.message.to_id in [PeerChannel(RESULTS_PARSE_CHANNEL_ID), PeerChannel(RESULTS_PARSE_CHANNEL_ID_DEBUG)] and \
            ('Результаты сражений:' in text or '⛺️Гильдия' in text or '⛺Гильдия' in text or "Headquarters" in text or
             "🗺State of map" in text):
        debug = event.message.to_id == PeerChannel(RESULTS_PARSE_CHANNEL_ID_DEBUG)
        logging.error("Received data from telegram, sending: {}".format(text))
        if '⛺️Гильдия' in text:
            guilds_str += text + "\n"
            logging.info("Adding text to guilds_str = {}".format(guilds_str))
        else:
            print("put stats in queue")
            castles_stats_queue.put({"data": text, "message_id": event.message.id, "debug": debug})
            castles_stats_queue.put({"data": guilds_str, "debug": debug})
            guilds_str = ""
            return
    elif event.message.from_id == CHAT_WARS_ID and "🏆 очков" in text and "Past battles:" in text:
        logging.info("Received /worldtop")
        castles_stats_queue.put({"data": text, "type": "worldtop"})


async def send_worldtop():
    await asyncio.sleep(5)
    await client.send_message(CHAT_WARS_ID, "/worldtop")
    for i in range(WORLDTOP_PERIOD * 60 // 5):
        if not globals.processing:
            return
        await asyncio.sleep(5)
    await send_worldtop()
