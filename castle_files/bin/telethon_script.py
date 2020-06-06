from telethon.sync import TelegramClient, events, connection
from telethon.tl.types import PeerChannel

from castle_files.work_materials.globals import RESULTS_PARSE_CHANNEL_ID, RESULTS_PARSE_CHANNEL_ID_DEBUG

try:
    from config import phone, username, password, api_id, api_hash
except ImportError:
    pass
try:
    from config import telethon_proxy
except ImportError:
    telethon_proxy = None

from multiprocessing import Queue

from retrying import retry

import socks
import logging

logging.getLogger('telethon').setLevel(logging.WARNING)

castles_stats_queue = Queue()

TEST_CHANNEL_ID = 1353017829

guilds_str = ""


WAIT_BEFORE_RETRY = 30
MAX_RETRIES = 5


def not_keyboard_interrupt(exception: Exception) -> bool:
    return not isinstance(exception, KeyboardInterrupt)


@retry(wait_fixed=WAIT_BEFORE_RETRY * 1000, retry_on_exception=not_keyboard_interrupt,
       stop_max_attempt_number=MAX_RETRIES)
def script_work():
    global client
    session_path = "./sessions/{}".format(username)
    if telethon_proxy is not None:
        proxy = (telethon_proxy["host"], telethon_proxy["port"], telethon_proxy["secret"])
        admin_client = TelegramClient(session_path, api_id, api_hash, proxy=proxy,
                                      connection=connection.tcpmtproxy.ConnectionTcpMTProxyIntermediate)
    else:
        admin_client = TelegramClient(session_path, api_id, api_hash)
    # admin_client.start(phone, password)
    #
    # client = admin_client
    with admin_client as client:
        admin_client.get_entity("ChatWarsBot")
        client.add_event_handler(stats_handler, event=events.NewMessage)
        print("telegram script launched")

        admin_client.run_until_disconnected()


async def stats_handler(event):
    global guilds_str
    text = event.message.message
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
            castles_stats_queue.put({"data": text, "debug": debug})
            castles_stats_queue.put({"data": guilds_str, "debug": debug})
            guilds_str = ""
            return
