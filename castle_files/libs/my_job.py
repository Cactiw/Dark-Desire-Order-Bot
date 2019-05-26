"""
В данном модуле находится класс MyJob, который используется для сохранения запланированных работ и автоматического
восстановления при перезапуске бота.
"""
import time


class MyJob:

    def __init__(self, job, when):
        self.job = job
        self.start_time = time.time()
        self.stop_time = time.time() + when

    def get_time_left(self):
        t = self.stop_time - time.time()
        return t

    def get_time_spent(self):
        t = time.time() - self.start_time
        return t

    def swap_time(self):
        t1 = 2*time.time() - self.start_time
        t2 = 2*time.time() - self.stop_time
        self.start_time = t2
        self.stop_time = t1
