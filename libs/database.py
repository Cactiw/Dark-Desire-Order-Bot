import psycopg2
import logging
import traceback
import threading
import random


class Conn:
    def __init__(self, credentials):
        self.credentials = credentials
        self.connection = None

    def start(self):
        if self.connection is not None:
            try:
                self.connection.close()
            except Exception:
                logging.error(traceback.format_exc())
        self.connection = psycopg2.connect("dbname={0} user={1} password={2}".format(self.credentials['dbname'],
                                                                                     self.credentials['user'],
                                                                                     self.credentials['pass']))
        self.connection.set_session(autocommit=True)

    def cursor(self):
        return Cursor(self)

    def close(self):
        self.connection.close()

    def __del__(self):
        try:
            self.connection.close()
        except Exception:
            pass


class Cursor:
    def __init__(self, conn):
        self.conn = conn
        self.pid = threading.current_thread().ident
        self.id = random.randint(1, 10000000)  # Не использовать, исключительно для отладки, генерация небезопасна!
        self.error_threading_count = 0
        self.requests = ""
        self.cursor = conn.connection.cursor() if conn.connection is not None else None

    def execute(self, request, *args):
        if threading.current_thread().ident != self.pid:
            self.requests += request + "\n"
            self.error_threading_count += 1
            if self.error_threading_count >= 3 or True:
                logging.error("USING CURSOR {} IN ANOTHER THREAD (err_count = {}), curr pid = {}, "
                              "init pid = {}, request = {}\n"
                              "{}".format(self.id, self.error_threading_count, threading.current_thread().ident,
                                          self.pid, request, self.requests))
                self.pid = threading.current_thread().ident
        if self.cursor is None:
            self.cursor = self.conn.connection.cursor()
        try:
            self.cursor.execute(request, *args)
        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            try:
                self.cursor = self.conn.cursor()
                self.cursor.execute(request, *args)
            except Exception:
                logging.error(traceback.format_exc())
            else:
                return 0
            logging.error(traceback.format_exc())
            # Переподключаюсь к БД в случае падения
            self.conn.start()
            self.cursor = self.conn.connection.cursor()
            self.cursor.execute(request, *args)
        # except psycopg2.Error:
        #     logging.error("{}\nRequest: {} {}".format(traceback.format_exc(), request, args))

    def fetchone(self):
        if threading.current_thread().ident != self.pid:
            pass
            # logging.error("USING CURSOR IN ANOTHER THREAD, curr pid = {}, init pid = {}"
            #               "".format(threading.current_thread().ident, self.pid))
        try:
            return self.cursor.fetchone()
        except psycopg2.ProgrammingError:
            return None

    def fetchmany(self):
        try:
            return self.cursor.fetchmany()
        except psycopg2.ProgrammingError:
            return None

    def fetchall(self):
        try:
            return self.cursor.fetchall()
        except psycopg2.ProgrammingError:
            return None

    def close(self):
        self.cursor.close()
