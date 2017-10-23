#!/usr/bin/env python2
import logging,ConfigParser,io,sqlite3
from telegram.ext import Updater,CommandHandler

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

def editdb(bot, update):
    connfile = 'db/' + update.message.chat_id + '.db'
    conn = sqlite3.connect(connfile)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS points (username TEXT PRIMARY KEY, adds INT, rms INT, total INT)''')
    entities = update.message.parse_entities()
    usernames = []
    for e in entities.keys():
        if e == 'mention':
            usernames.append(entities[e])
        if e == 'text_mention':
            response = "I'm not touching " + entities[e] + "'s points, ya turkey, that goober needs a username!"
            bot.send_message(chat_id = update.message.chat_id, text = response)
            
    for u in usernames:
        cursor.execute("""SELECT adds, rms, total FROM points WHERE username = %s""", (u, ))
        points = cursor.fetchone()
        adds = points[0]
        rms = points[1]
        total = points[2]
        if entities['bot_command'] == 'addpoint':        
            adds = adds + 1
        if entities['bot_command'] == 'rmpoint':
            rms = rms + 1
        total = adds + rms
        cursor.execute("""UPDATE points SET adds = %d, total = %d WHERE username = %s""", (adds, total, u))
        cursor.commit()
        response = u + ' - ' + '+' + adds + '/-' + rms + ' total: ' + total
        bot.send_message(chat_id = update.message.chat_id, text = response)

    cursor.close()

dispatcher.add_handler(CommandHandler('addpoint', editdb))
dispatcher.add_handler(CommandHandler('rmpoint', editdb))

updater.start_polling()
updater.idle()
