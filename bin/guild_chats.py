from telegram import ReplyKeyboardRemove

from work_materials.globals import *
from bin.order import recashe_order_chats


def add_pin(bot, update):
    mes = update.message
    request = "SELECT guild_chat_id FROM guild_chats WHERE chat_id = '{0}'".format(mes.chat_id)
    cursor.execute(request)
    row = cursor.fetchone()
    if row is not None:
        bot.send_message(chat_id=update.message.chat_id, text='Беседа уже подключена к рассылке')
        return
    request = "INSERT INTO guild_chats(chat_id, chat_name) VALUES('{0}', '{1}')".format(mes.chat_id, mes.chat.title)
    cursor.execute(request)
    bot.send_message(chat_id=update.message.chat_id, text='Беседа успешо подключена к рассылке')
    recashe_order_chats()



def pin_setup(bot, update):
    request = "SELECT guild_chat_id, chat_id, chat_name, enabled, pin, disable_notification, division FROM guild_chats"
    cursor.execute(request)
    row = cursor.fetchone()
    response = "Текущие рассылки пинов:\n"
    while row:
        response_new = '\n' + str(row[0]) + ': ' + row[2] + ', chat_id = ' + str(row[1]) + '\npin = ' + str(row[4]) + '\ndisabled_notification = ' + str(row[5]) + '\nenabled = ' + str(row[3])
        response_new += '\n'
        if row[3]:
            response_new += 'disable /pinset_{0}_0'.format(row[0]) + '\n'
        else:
            response_new += 'enable /pinset_{0}_1'.format(row[0]) + '\n'

        if row[4]:
            response_new += 'disable_pin /pinpin_{0}_0'.format(row[0]) + '\n'
        else:
            response_new += 'enable_pin /pinpin_{0}_1'.format(row[0]) + '\n'

        if row[5]:
            response_new += 'enable_notification /pinmute_{0}_0'.format(row[0]) + '\n'
        else:
            response_new += 'disable_notification /pinmute_{0}_1'.format(row[0]) + '\n'
        response_new += 'division: {0}\n'.format(row[6])
        response_new += 'Change division: /pindivision_{0}\n\n'.format(row[0])
        if len(response + response_new) >= 4096:  # Превышение лимита длины сообщения
            bot.send_message(chat_id=update.message.chat_id, text=response, parse_mode='HTML')
            response = ""
        response += response_new

        row = cursor.fetchone()
    bot.send_message(chat_id=update.message.chat_id, text=response, reply_markup=ReplyKeyboardRemove())


def pinset(bot, update):
    mes = update.message
    mes1 = mes.text.split("_")
    request = "UPDATE guild_chats SET enabled = %s WHERE guild_chat_id = %s"
    cursor.execute(request, (mes1[2], mes1[1]))
    conn.commit()
    bot.send_message(chat_id=update.message.chat_id, text='Выполнено')


def pinpin(bot, update):
    mes = update.message
    mes1 = mes.text.split("_")
    #print(mes1[0], mes1[1], mes1[2])
    request = "UPDATE guild_chats SET pin = %s WHERE guild_chat_id = %s"
    cursor.execute(request, (mes1[2], mes1[1]))
    conn.commit()
    bot.send_message(chat_id=update.message.chat_id, text='Выполнено')

def pinmute(bot, update):
    mes = update.message
    mes1 = mes.text.split("_")
    request = "UPDATE guild_chats SET disable_notification = %s WHERE guild_chat_id = %s"
    cursor.execute(request, (mes1[2], mes1[1]))
    conn.commit()
    bot.send_message(chat_id=update.message.chat_id, text='Выполнено')

def pindivision(bot, update):
    mes = update.message
    mes1 = mes.text.split("_")
    division = mes.text.partition(' ')[2]
    request = "UPDATE guild_chats SET division = %s WHERE guild_chat_id = %s"
    cursor.execute(request, (division, mes1[1]))
    conn.commit()
    bot.send_message(chat_id=update.message.chat_id, text='Выполнено')