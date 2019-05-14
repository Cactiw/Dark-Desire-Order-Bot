import multiprocessing
import logging

from order_bot import order_bot_processing
from castle_bot import castle_bot_processing

from castle_files.bin.telethon_script import script_work


console = logging.StreamHandler()
console.setLevel(logging.INFO)

log_file = logging.FileHandler(filename='error.log', mode='a')
log_file.setLevel(logging.ERROR)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO, handlers=[log_file, console])


# script_work()  # Для авторизации на новой машине

processes = []
order_bot_process = multiprocessing.Process(target=order_bot_processing)
order_bot_process.start()
processes.append(order_bot_process)

castle_bot_process = multiprocessing.Process(target=castle_bot_processing)
castle_bot_process.start()
processes.append(castle_bot_process)
try:
    processes[1].join()
except KeyboardInterrupt:
    pass
print("ended")
