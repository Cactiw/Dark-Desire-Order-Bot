from telethon.sync import TelegramClient, events
from telethon.tl.types import PeerChannel

from castle_files.work_materials.globals import RESULTS_PARSE_CHANNEL_ID

try:
    from config import phone, username, password, api_id, api_hash
except ImportError:
    pass

from multiprocessing import Queue
import logging
logging.getLogger('telethon').setLevel(logging.WARNING)

castles_stats_queue = Queue()

TEST_CHANNEL_ID = 1353017829

guilds_str = ""


def script_work():
    global client
    admin_client = TelegramClient(username, api_id, api_hash)
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
    if event.message.to_id == PeerChannel(RESULTS_PARSE_CHANNEL_ID) and \
            ('Результаты сражений:' in text or '⛺️Гильдия' in text or '⛺Гильдия' in text):
        logging.error("Received data from telegram, sending: {}".format(text))
        if '⛺️Гильдия' in text:
            guilds_str += text + "\n"
            logging.info("Adding text to guilds_str = {}".format(guilds_str))
        else:
            print("put stats in queue")
            castles_stats_queue.put(text)
            castles_stats_queue.put(guilds_str)
            guilds_str = ""
            return
