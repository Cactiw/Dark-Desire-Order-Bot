import castle_files.work_materials.globals as file_globals
from castle_files.bin.construction import construction_jobs

import time
import pickle
import logging
import sys

log = logging.getLogger("Save load user data")


def load_data():
    try:
        f = open('castle_files/backup/user_data', 'rb')
        file_globals.dispatcher.user_data = pickle.load(f)
        f.close()
        print("Data picked up")
    except FileNotFoundError:
        logging.error("Data file not found")
    except Exception:
        logging.error(sys.exc_info()[0])


def save_data():
    need_exit = 0
    while need_exit == 0:
        for i in range(0, 5):
            time.sleep(5)
            if not file_globals.processing:
                need_exit = 1
                break
        # Before pickling
        log.debug("Writing data, do not shutdown bot...\r")
        if need_exit:
            log.warning("Writing data last time, do not shutdown bot...")
        try:
            f = open('castle_files/backup/user_data', 'wb+')
            pickle.dump(file_globals.dispatcher.user_data, f)
            f.close()
            dump = {}
            for k, v in list(construction_jobs.items()):
                """if v.get_time_left() < 0:
                    construction_jobs.pop(k)
                    continue"""
                dump.update({k: [file_globals.dispatcher.user_data.get(k).get("status"), v.stop_time]})
            if file_globals.began:
                f = open('castle_files/backup/construction_jobs', 'wb+')
                pickle.dump(dump, f)
                f.close()
            log.debug("Data write completed\b")
        except Exception:
            logging.error(sys.exc_info()[0])
