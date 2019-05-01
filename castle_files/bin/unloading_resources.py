from castle_files.libs.player import players
from castle_files.libs.guild import guilds
import castle_files.work_materials.globals as globals

import time
import logging
import traceback

LOAD_OUT_CHECK_EVERY_MINUTES = 1
LOAD_OUT_MINUTES_LIMIT = 30


# Монитор выполняется в отдельном потоке, производит выгрузку из памяти неиспользуемых игроков и гильдий
def resources_monitor():
    while globals.processing:
        try:
            players_list = list(players.values())
            for player in players_list:
                if player.last_access_time is not None and \
                        time.time() - player.last_access_time > LOAD_OUT_MINUTES_LIMIT * 60:
                    try:
                        players.pop(player.id)
                    except Exception:
                        logging.error(traceback.format_exc())

            guilds_list = list(guilds.values())
            for guild in guilds_list:
                if guild.last_access_time is not None and \
                        time.time() - guild.last_access_time > LOAD_OUT_MINUTES_LIMIT * 60:
                    try:
                        guilds.pop(guild.id)
                    except Exception:
                        logging.error(traceback.format_exc())

            for i in range(int(LOAD_OUT_CHECK_EVERY_MINUTES * 60)):
                if not globals.processing:
                    return 0
                time.sleep(1)
        except Exception:
            logging.error(traceback.format_exc())
