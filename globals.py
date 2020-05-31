"""
В этом модуле находятся глобальные переменные, которые необходимы для совместной работы двух ботов.
"""
from multiprocessing import Queue

import pytz
import tzlocal
import os

# Очередь для передачи запросов из замкового бота в приказ на перекеширование некоторый вещей из БД (например, гильдий)
update_request_queue = Queue()

master_pid = os.getpid()

moscow_tz = pytz.timezone('Europe/Moscow')
try:
    local_tz = tzlocal.get_localzone()
except pytz.UnknownTimeZoneError:
    local_tz = pytz.timezone('Europe/Andorra')
