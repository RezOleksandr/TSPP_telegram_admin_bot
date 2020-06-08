# -*- coding: utf-8 -*-

from telegram.ext.dispatcher import run_async
# from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import Updater, MessageHandler, CommandHandler
import telegram
import sqlite3
import logging
import filters
import config
import time

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG, stream=open('logs.log', 'a',
                                                                                         encoding='utf-8'))
local_logging = logging.getLogger('local_logging')
local_logging.setLevel(logging.INFO)
sh = logging.StreamHandler(open('log.log', 'a', encoding='utf-8'))
local_logging.addHandler(sh)
formatter = logging.Formatter('%(asctime)s - %(message)s')

updater = Updater(token=config.TOKEN, use_context=True, workers=100)
dispatcher = updater.dispatcher


@run_async
def start(updater, context):
    message = updater.message
    bot = context.bot
    reply = bot.send_message(message.chat.id, 'Кря')
    local_logging.info(eval(config.LOGGING_INFO_TEXT_FULL))


@run_async
def authorise(updater, context):
    message = updater.message
    bot = context.bot
    conn = sqlite3.connect(config.DBNAME, timeout=10)
    curs = conn.cursor()
    if context.args and context.args[0] == config.TOKEN:
        curs.execute(f'SELECT * FROM users WHERE id = {message.from_user.id}')
        user = curs.fetchone()
        if not user:
            curs.execute('INSERT INTO users VALUES (?,?,?)', [message.from_user.id, message.from_user.username, 2])
        else:
            curs.execute(f'UPDATE users SET rights = 2 WHERE id = {message.from_user.id}')
        conn.commit()
        reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                 text='Ви авторизувалися як головний адміністратор')
        logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
        conn.close()


@run_async
def add_chat(updater, context):
    message = updater.message
    bot = context.bot
    conn = sqlite3.connect(config.DBNAME, timeout=10)
    curs = conn.cursor()
    curs.execute("SELECT rights FROM users WHERE id = {}".format(message.from_user.id))
    sender_rights = curs.fetchone()[0]
    curs.execute('SELECT id FROM chats')
    registered_chats_raw = curs.fetchall()
    registered_chats = []
    for chat in registered_chats_raw:
        registered_chats.append(chat[0])
    curs.execute('SELECT name FROM chats')
    registered_chats_names_raw = curs.fetchall()
    registered_chats_names = []
    for chat_name in registered_chats_names_raw:
        registered_chats_names.append(chat_name[0])
    if sender_rights > 2 and message.chat.type != 'private':
        try:
            if message.chat.id in registered_chats:
                if message.chat.title in registered_chats_names:
                    reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                             text='Чат уже зареєстрований')
                    logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
                else:
                    curs.execute("UPDATE chats SET name = '{0}' WHERE id = {1}".format(message.chat.title,
                                                                                       message.chat.id))
                    conn.commit()
                    reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                             text='Регістрація успішна')
                    logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
            else:
                curs.execute('INSERT INTO chats VALUES (?,?)', (message.chat.id, message.chat.title))
                conn.commit()
                reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                         text='Регістрація успішна')
                logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
        except Exception:
            reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id, text='Ошибка')
            logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
    else:
        reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                 text='У вас недостатньо прав')
        logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
    conn.close()


@run_async
def registration_applications_list(updater, context):
    message = updater.message
    bot = context.bot
    conn = sqlite3.connect(config.DBNAME, timeout=10)
    curs = conn.cursor()
    curs.execute("SELECT rights FROM users WHERE id = {}".format(message.from_user.id))
    sender_rights = curs.fetchone()[0]
    if sender_rights > 0:
        curs.execute('SELECT * FROM registration_applications')
        raw_applications_list = curs.fetchall()
        text = ''
        for application in raw_applications_list:
            text += f'{application[0]}  {application[1]}\n'
        reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                 text=text)
        logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
        conn.close()


@run_async
def apply_for_registration(updater, context):
    message = updater.message
    bot = context.bot
    conn = sqlite3.connect(config.DBNAME, timeout=10)
    curs = conn.cursor()
    curs.execute('SELECT id FROM users WHERE id = {}'.format(message.from_user.id))
    user = curs.fetchone()
    curs.execute('SELECT id FROM registration_applications WHERE id = {}'.format(message.from_user.id))
    application = curs.fetchone()
    if not user and not application:
        if message.from_user.username:
            curs.execute('INSERT INTO registration_applications VALUES (?,?)', [message.from_user.id,
                                                                                message.from_user.username])
        else:
            curs.execute('INSERT INTO registration_applications VALUES (?,?)', [message.from_user.id,
                                                                                message.from_user.first_name])
        conn.commit()
        reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                 text='Ви відправили заявку на реєстрацію')
        logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
    conn.close()


@run_async
def apply_registration(updater, context):
    message = updater.message
    bot = context.bot
    conn = sqlite3.connect(config.DBNAME, timeout=10)
    curs = conn.cursor()
    curs.execute("SELECT rights FROM users WHERE id = {}".format(message.from_user.id))
    sender_rights = curs.fetchone()[0]
    if sender_rights > 0 and context.args:
        curs.execute(f'SELECT * FROM registration_applications WHERE id = {int(context.args[0])}')
        application = curs.fetchone()
        curs.execute('SELECT id FROM users WHERE id = {}'.format(int(context.args[0])))
        user = curs.fetchone()
        print(application)
        print(user)
        if application and not user:
            print(1)
            curs.execute('INSERT INTO users VALUES (?,?,?)', [application[0], application[1], 0])
            curs.execute(f'DELETE FROM registration_applications WHERE id = {application[0]}')
            conn.commit()
            reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                     text='Реєстрація успішна')
            logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
    conn.close()


@run_async
def promote(updater, context):
    message = updater.message
    bot = context.bot
    conn = sqlite3.connect(config.DBNAME, timeout=10)
    curs = conn.cursor()
    curs.execute("SELECT rights FROM users WHERE id = {}".format(message.from_user.id))
    sender_rights = curs.fetchone()[0]
    if message.reply_to_message:
        if message.from_user.id == message.reply_to_message.from_user.id:
            reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                     text='Не готово')
            logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
        else:
            if sender_rights > 1:
                curs.execute('SELECT rights FROM users WHERE id = {}'.format(message.reply_to_message.from_user.id))
                target_rights = curs.fetchone()
                if target_rights is None:
                    target_rights = 0
                else:
                    target_rights = target_rights[0]
                if target_rights > 0:
                    reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                             text='Максимальное завание')
                    logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
                else:
                    try:
                        curs.execute(
                            "SELECT rights FROM users WHERE id = {}".format(message.reply_to_message.from_user.id))
                        rights = curs.fetchone()[0]
                        curs.execute("UPDATE users SET rights = {1} WHERE id = {0}".format(
                            message.reply_to_message.from_user.id, rights + 1))
                        conn.commit()
                        reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                                 text='Повышение успешно')
                        logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
                    except:
                        reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                                 text='Ошибка')
                        logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
            else:
                reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                         text='У вас недостаточно прав')
                logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
    conn.close()


@run_async
def demote(updater, context):
    message = updater.message
    bot = context.bot
    conn = sqlite3.connect(config.DBNAME, timeout=10)
    curs = conn.cursor()
    curs.execute("SELECT rights FROM users WHERE id = {}".format(message.from_user.id))
    sender_rights = curs.fetchone()[0]
    if message.reply_to_message:
        if message.from_user.id == message.reply_to_message.from_user.id:
            reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                     text='Не готово')
            logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
        else:
            if sender_rights > 1:
                try:
                    curs.execute(
                        "SELECT rights FROM users WHERE id = {}".format(message.reply_to_message.from_user.id))
                    target_rights = curs.fetchone()
                    if target_rights is None:
                        target_rights = 0
                    else:
                        target_rights = target_rights[0]
                    if target_rights == 0:
                        reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                                 text='Минимальный ранг')
                        logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
                    else:
                        curs.execute('UPDATE users SET rights = {1} WHERE id = {0}'.format(
                            message.reply_to_message.from_user.id, target_rights - 1))
                        conn.commit()
                        reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                                 text='Понижение успешно')
                        logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
                except:
                    reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                             text='Ошибка')
                    logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
            else:
                reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                         text='У вас недостаточно прав')
                logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
    else:
        reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id, text='Не готово')
        logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
    conn.close()


@run_async
def pin(updater, context, timeout=10):
    message = updater.message
    bot = context.bot
    if message.reply_to_message:
        try:
            bot.pin_chat_message(chat_id=message.chat.id, message_id=message.reply_to_message.message_id)
        except:
            reply = bot.send_message(chat_id=message.chat.id, text='Ошибка')
            logging.info(eval(config.LOGGING_INFO_TEXT_FULL))


@run_async
def tsyts(updater, context):
    message = updater.message
    bot = context.bot
    restrictions = telegram.ChatPermissions(can_send_messages=False)
    if message.reply_to_message:
        conn = sqlite3.connect(config.DBNAME, timeout=10)
        curs = conn.cursor()
        curs.execute('SELECT rights FROM users WHERE id = {}'.format(message.reply_to_message.from_user.id))
        target_rights = curs.fetchone()
        if target_rights is None:
            target_rights = 0
        else:
            target_rights = target_rights[0]
        if target_rights == 0:
            try:
                if len(message.text) == 3:
                    bot.restrict_chat_member(chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id,
                                             permissions=restrictions, until_date=int(time.time() + 300))
                    reply = bot.send_message(chat_id=message.chat.id, text='Готово')
                    logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
                else:
                    until_date = time.time() + int(message.text[4:]) * 60
                    bot.restrict_chat_member(chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id,
                                             permissions=restrictions, until_date=until_date)
                    reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                             text='Готово')
                    logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
            except Exception:
                reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                         text='Не готово')
                logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
                print(Exception.args)
        else:
            reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id, text='Не готово')
            logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
        conn.close()


@run_async
def restrict_media(updater, context):
    message = updater.message
    bot = context.bot
    restrictions = telegram.ChatPermissions(can_send_messages=True)
    if message.reply_to_message:
        conn = sqlite3.connect(config.DBNAME, timeout=10)
        curs = conn.cursor()
        curs.execute('SELECT rights FROM users WHERE id = {}'.format(message.reply_to_message.from_user.id))
        target_rights = curs.fetchone()
        if target_rights is None:
            target_rights = 0
        else:
            target_rights = target_rights[0]
        if target_rights == 0:
            try:
                bot.restrict_chat_member(chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id,
                                         permissions=restrictions)
                reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id, text='Готово')
                logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
            except:
                reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                         text='Не готово')
                logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
        else:
            reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id, text='Не готово')
            logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
        conn.close()


@run_async
def kick(updater, context):
    message = updater.message
    bot = context.bot
    if message.reply_to_message:
        conn = sqlite3.connect(config.DBNAME, timeout=10)
        curs = conn.cursor()
        curs.execute('SELECT rights FROM users WHERE id = {}'.format(message.reply_to_message.from_user.id))
        target_rights = curs.fetchone()
        if target_rights is None:
            target_rights = 0
        else:
            target_rights = target_rights[0]
        if target_rights == 0:
            try:
                bot.kick_chat_member(chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id)
                bot.unban_chat_member(chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id)
                try:
                    bot.kick_chat_member(chat_id=-1001447327709, user_id=message.reply_to_message.from_user.id)
                    bot.unban_chat_member(chat_id=-1001447327709, user_id=message.reply_to_message.from_user.id)
                except Exception:
                    pass
                reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id, text='Готово')
                logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
            except:
                reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                         text='Не готово')
                logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
        else:
            reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id, text='Не готово')
            logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
        conn.close()


@run_async
def pomilovat(updater, context):
    message = updater.message
    bot = context.bot
    if message.reply_to_message:
        try:
            bot.promote_chat_member(chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id)
            reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id, text='Готово')
            logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
        except:
            reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id, text='Не готово')
            logging.info(eval(config.LOGGING_INFO_TEXT_FULL))


@run_async
def not_registered_user(updater, context):
    message = updater.message
    bot = context.bot
    try:
        bot.kick_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)
        bot.unban_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)
        reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                 text='Незареєстрований користувачи вилучений з чату')
        logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
        try:
            bot.kick_chat_member(chat_id=-1001447327709, user_id=message.from_user.id)
            reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                     text='Незареєстрований користувачи вилучений з каналу')
            logging.info(eval(config.LOGGING_INFO_TEXT_FULL))
        except Exception:
            pass
    except Exception:
        reply = bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.message_id,
                                 text='Незареєстрований користувач')
        logging.info(eval(config.LOGGING_INFO_TEXT_FULL))


@run_async
def not_registered_chat(updater, context):
    message = updater.message
    bot = context.bot
    reply = bot.send_message(chat_id=message.chat.id, text='Не зарегистрированный чат')
    logging.info(eval(config.LOGGING_INFO_TEXT_FULL))


@run_async
def no_text(updater, context):
    pass


def main():
    dispatcher.add_handler(MessageHandler(filters.no_text_filter, no_text))
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('authorise', authorise))
    dispatcher.add_handler(CommandHandler('apply_for_registration', apply_for_registration))
    dispatcher.add_handler(MessageHandler(filters.not_registered_user_filter, not_registered_user))
    dispatcher.add_handler(CommandHandler('add_chat', add_chat))
    dispatcher.add_handler(CommandHandler('registration_applications_list', registration_applications_list))
    dispatcher.add_handler(CommandHandler('apply', apply_registration))
    dispatcher.add_handler(MessageHandler(filters.not_registered_chat_filter, not_registered_chat))
    # dispatcher.add_handler(CommandHandler('promote', promote))
    # dispatcher.add_handler(CommandHandler('demote', demote))
    dispatcher.add_handler(MessageHandler(filters.pin_filter, pin))
    dispatcher.add_handler(MessageHandler(filters.tsyts_filter, tsyts))
    dispatcher.add_handler(MessageHandler(filters.restrict_media_filter, restrict_media))
    dispatcher.add_handler(MessageHandler(filters.pomilovat_filter, pomilovat))
    dispatcher.add_handler(MessageHandler(filters.kick_filter, kick))

    updater.start_polling(timeout=10)


if __name__ == '__main__':
    main()
