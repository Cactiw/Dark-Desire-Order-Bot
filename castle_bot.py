from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackQueryHandler

from castle_files.work_materials.globals import dispatcher, updater, conn


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Привет! Пришли мне форвард /hero из @chatwarsbot!")



def castle_bot_processing():
    dispatcher.add_handler(CommandHandler('start', start))

    updater.start_polling(clean=False)

    updater.idle()

    conn.close()
