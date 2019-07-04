import psycopg2
import logging
import traceback
import threading


class Conn:
    def __init__(self, credentials):
        self.credentials = credentials
        self.connection = None
        self.cursors = {}

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
        cursor = Cursor(self)
        self.cursors.update({threading.current_thread().ident: cursor.cursor})
        return cursor

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
        self.cursor = None
        self.load_cursor()

    def load_cursor(self):
        self.cursor = self.conn.cursors.get(self.pid)
        if self.cursor is None:
            print("reloading cursor")
            self.cursor = self.conn.connection.cursor() if self.conn.connection is not None else None

    def execute(self, request, *args):
        if threading.current_thread().ident != self.pid:
            pass
            # logging.error("USING CURSOR IN ANOTHER THREAD, curr pid = {}, init pid = {}"
            #               "".format(threading.current_thread().ident, self.pid))
        self.load_cursor()
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

    def fetchone(self):
        self.load_cursor()
        if threading.current_thread().ident != self.pid:
            pass
            # logging.error("USING CURSOR IN ANOTHER THREAD, curr pid = {}, init pid = {}"
            #               "".format(threading.current_thread().ident, self.pid))
        try:
            return self.cursor.fetchone()
        except psycopg2.ProgrammingError:
            return None

    def fetchmany(self):
        self.load_cursor()
        try:
            return self.cursor.fetchmany()
        except psycopg2.ProgrammingError:
            return None

    def fetchall(self):
        self.load_cursor()
        try:
            return self.cursor.fetchall()
        except psycopg2.ProgrammingError:
            return None
