#!/usr/bin/env python2
import logging,ConfigParser,io,sqlite3
from telegram.ext import Updater,MessageHandler,CommandHandler,Filters,BaseFilter

logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s', level = logging.INFO)

# Load the configuration file
try:
    with open("config.ini") as f:
        sample_config = f.read()
        config = ConfigParser.RawConfigParser(allow_no_value=True)
        config.readfp(io.BytesIO(sample_config))
except FileNotFoundError:
    print('Could not find a config file.')

# Main        
updater = Updater(token = config.get('telegram', 'token'))
dispatcher = updater.dispatcher
username = config.get('telegram', 'username')

class FilterUsername(BaseFilter):
    def filter(self, message):
        return username in message.text
filter_username = FilterUsername()

def addpoint(bot, update):
    connfile = update.message.chat_id + '.db'
    conn = sqlite3.connect(connfile)
    cursor = conn.cursor()
    if cursor.execute("""SELECT name FROM sqlite_master WHERE type='table'""").fetchall().empty():
        pass #create table
    

def rmpoint(bot, update):
    pass
    bot.send_message(chat_id = update.message.chat_id, text = response)

response_handler = MessageHandler(filter_username, respond)
dispatcher.add_handler(CommandHandler('addpoint', addpoint))
dispatcher.add_handler(CommandHandler('rmpoint', rmpoint))

updater.start_polling()
updater.idle()
