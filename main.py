import multiprocessing
import threading
import logging

from order_bot import order_bot_processing
from castle_bot import castle_bot_processing

from castle_files.bin.telethon_script import auth

import sys


console = logging.StreamHandler()
console.setLevel(logging.INFO)

log_file = logging.FileHandler(filename='error.log', mode='a')
log_file.setLevel(logging.ERROR)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO, handlers=[log_file, console])

# mpl = multiprocessing.log_to_stderr()
# mpl.setLevel(logging.INFO)

if len(sys.argv) > 1:
    for arg in sys.argv[1:]:
        if arg == "--auth":
            logging.info("Starting telethon auth")
            auth()  # Для авторизации на новой машине
            exit(0)

# order_bot_processing()
processes = []
order_bot_process = multiprocessing.Process(target=order_bot_processing)
order_bot_process.start()
processes.append(order_bot_process)

castle_bot_process = multiprocessing.Process(target=castle_bot_processing)
castle_bot_process.start()
processes.append(castle_bot_process)
try:
    processes[0].join()
except KeyboardInterrupt:
    pass
print("ended")
