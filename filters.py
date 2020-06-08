# -*- coding: utf-8 -*-

from telegram.ext import BaseFilter
import sqlite3
import config
import re


class NotRegisteredUserFilter(BaseFilter):
    def filter(self, message):
            conn = sqlite3.connect(config.DBNAME, timeout=10)
            curs = conn.cursor()
            curs.execute('SELECT id FROM users WHERE id = {}'.format(message.from_user.id))
            user = curs.fetchone()
            conn.close()
            return not user


not_registered_user_filter = NotRegisteredUserFilter()


class NotRegisteredChatFilter(BaseFilter):
    def filter(self, message):
        if message.chat.type != 'private':
            try:
                conn = sqlite3.connect(config.DBNAME, timeout=10)
                curs = conn.cursor()
                curs.execute('SELECT id FROM chats WHERE id = {}'.format(message.chat.id))
                chat = curs.fetchone()
                conn.close()
                return not chat
            except:
                return True


not_registered_chat_filter = NotRegisteredChatFilter()


class PinFilter(BaseFilter):
    def filter(self, message):
        conn = sqlite3.connect(config.DBNAME, timeout=10)
        curs = conn.cursor()
        curs.execute('SELECT rights FROM users WHERE id = {}'.format(message.from_user.id))
        rights = curs.fetchone()[0]
        conn.close()
        return rights > 0 and message.text == 'Пін'


pin_filter = PinFilter()


class ROFilter(BaseFilter):
    def filter(self, message):
        conn = sqlite3.connect(config.DBNAME, timeout=10)
        curs = conn.cursor()
        curs.execute('SELECT rights FROM users WHERE id = {}'.format(message.from_user.id))
        rights = curs.fetchone()[0]
        conn.close()
        if rights > 0 and re.match(r'РО', message.text):
            return not re.match(r'РО\S', message.text)


RO_filter = ROFilter()


class RestrictMediaFilter(BaseFilter):
    def filter(self, message):
        conn = sqlite3.connect(config.DBNAME, timeout=10)
        curs = conn.cursor()
        curs.execute('SELECT rights FROM users WHERE id = {}'.format(message.from_user.id))
        rights = curs.fetchone()[0]
        conn.close()
        return rights > 0 and ('Бан медіа' == message.text)


restrict_media_filter = RestrictMediaFilter()


class UnbanFilter(BaseFilter):
    def filter(self, message):
        conn = sqlite3.connect(config.DBNAME, timeout=10)
        curs = conn.cursor()
        curs.execute('SELECT rights FROM users WHERE id = "{}"'.format(message.from_user.id))
        rights = curs.fetchone()[0]
        conn.close()
        return rights > 0 and 'Помилувати' == message.text


unban_filter = UnbanFilter()


class KickFilter(BaseFilter):
    def filter(self, message):
        conn = sqlite3.connect(config.DBNAME, timeout=10)
        curs = conn.cursor()
        curs.execute('SELECT rights FROM users WHERE id = {}'.format(message.from_user.id))
        rights = curs.fetchone()[0]
        conn.close()
        return rights > 0 and '!Бан' == message.text


kick_filter = KickFilter()


class NoTextFilter(BaseFilter):
    def filter(self, message):
        return message.text is None


no_text_filter = NoTextFilter()


