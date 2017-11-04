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
except:
    print('Could not find a config file.')

# Main        
updater = Updater(token = config.get('telegram', 'token'))
dispatcher = updater.dispatcher
username = config.get('telegram', 'username')

class db_cursor:
    def __init__(self, update):
          self.update = update
    def __enter__(self):
        self.connfile = 'db/' + str(self.update.message.chat_id) + '.db'
        self.conn = sqlite3.connect(self.connfile)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS points (username TEXT PRIMARY KEY, adds INT, rms INT, total INT)''')
        return self.cursor
    def __exit__(self, type, value, traceback):
        self.conn.commit()
        self.cursor.close()

def addrmpoint(bot, update):
    with db_cursor(update) as cursor:
        entities = update.message.parse_entities()
        usernames = []
        for e in entities.keys():
            if e.type == 'mention' and entities[e].lower() not in [x.lower() for x in usernames]:
                usernames.append(entities[e])
            if e.type == 'text_mention':
                response = "I'm not touching " + entities[e] + "'s points, ya turkey, that goober needs a username!"
                bot.send_message(chat_id = update.message.chat_id, text = response)
                usernames.append(None)

        if not usernames:
            bot.send_message(chat_id = update.message.chat_id, text = 'No username(s) sent.')

        for u in usernames:
            if u is not None:
                cursor.execute("""SELECT adds, rms FROM points WHERE username = ?""", (u.lower(), ))
                points = cursor.fetchone()
                if points is None:
                    points = [0, 0, 0]
                adds = points[0]
                rms = points[1]
                if update.message.text.startswith('/add'):
                    adds = adds + 1
                else: #message.text.startswith('/rm'):
                    rms = rms + 1
                total = adds - rms
                cursor.execute("""REPLACE INTO points (username, adds, rms, total) VALUES (?, ?, ?, ?)""", (u.lower(), adds, rms, total))
                response = u + ' - ' + '+' + str(adds) + '/-' + str(rms) + ' total: ' + str(total)
                bot.send_message(chat_id = update.message.chat_id, text = response)

dispatcher.add_handler(CommandHandler(['addpoint', 'rmpoint'], addrmpoint))

updater.start_polling()
updater.idle()
