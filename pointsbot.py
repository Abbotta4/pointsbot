#!/usr/bin/env python2
import logging,ConfigParser,io,sqlite3,time
from telegram.ext import Updater,CommandHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext.dispatcher import run_async

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

def get_users(bot, update, cursor):
    entities = update.message.parse_entities()
    usernames = []
    for e in entities.keys():
        if e.type == 'mention' and entities[e].lower() not in [x.lower() for x in usernames]:
            usernames.append(entities[e])
        if e.type == 'text_mention':
            response = "I'm not touching " + entities[e] + "'s points, ya turkey, that goober needs a username!"
            bot.send_message(chat_id = update.message.chat_id, text = response)
            usernames.append(None)

    if update.message.reply_to_message:
        reply_user = '@' + update.message.reply_to_message.from_user.username
        if reply_user.lower() not in [x.lower() for x in usernames]:
            usernames.append(reply_user)

    if not usernames:
        bot.send_message(chat_id = update.message.chat_id, text = 'No username(s) sent.')

@run_async
def addrmpoint(bot, update):
    with db_cursor(update) as cursor:
        #usernames = get_users(bot, update, cursor)
        entities = update.message.parse_entities()
        usernames = []
        for e in entities.keys():
            if e.type == 'mention' and entities[e].lower() not in [x.lower() for x in usernames]:
                usernames.append(entities[e])
            if e.type == 'text_mention':
                response = "I'm not touching " + entities[e] + "'s points, ya turkey, that goober needs a username!"
                bot.send_message(chat_id = update.message.chat_id, text = response)
                usernames.append(None)

        if update.message.reply_to_message:
            reply_user = '@' + update.message.reply_to_message.from_user.username
            if reply_user.lower() not in [x.lower() for x in usernames]:
                usernames.append(reply_user)

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

@run_async
def top10(bot, update):
    with db_cursor(update) as cursor:
        cursor.execute('''SELECT * FROM points ORDER BY total ASC''')
        points = cursor.fetchall()
        top10 = []
        while points and len(top10) < 10:
            top10.append(points.pop())
        response = ''
        for username, x in zip(top10, range (1, 11)):
            response = response + str(x) + '. ' + username[0] + ' - ' + '+' + str(username[1]) + '/-' + str(username[2]) + ' total: ' + str(username[3]) + '\n'
        bot.send_message(chat_id = update.message.chat_id, text = response)
@run_async
def votepoint(bot, update):
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

        if update.message.reply_to_message:
            reply_user = '@' + update.message.reply_to_message.from_user.username
            if reply_user.lower() not in [x.lower() for x in usernames]:
                usernames.append(reply_user)

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
                button_list = [[InlineKeyboardButton("add", callback_data='add'), InlineKeyboardButton("rm", callback_data='rm')]]
                reply_markup = InlineKeyboardMarkup(button_list)
                votemessage = bot.send_message(chat_id = update.message.chat_id, text = "Should this be add or rm? 5m00s", reply_markup = reply_markup)

                def callback_countdown(bot, message, t):
                    message.edit_text(text="Should this be add or rm? {}".format(str(t//60) + "m" + str(t%60) + "s"))
                    
                for t in range(299, 0, -1):
                    time.sleep(1)
                    callback_countdown(bot, votemessage, t) 
                
#                for t in range(300, 0, -1):
 #                   time.sleep(1)
  #                  votemessage.edit_text(text="Should this be add or rm? {}".format(str(t//60) + "m" + str(t%60) + "s"))
   #                 query = update.callback_query
    #                if query:
     #                   query = query.data
      #              votemessage.edit_reply_markup(reply_markup = reply_markup)
                #if update.message.text.startswith('/add'):
                #    adds = adds + 1
                #else: #message.text.startswith('/rm'):
                #    rms = rms + 1
                total = adds - rms
                cursor.execute("""REPLACE INTO points (username, adds, rms, total) VALUES (?, ?, ?, ?)""", (u.lower(), adds, rms, total))
                response = u + ' - ' + '+' + str(adds) + '/-' + str(rms) + ' total: ' + str(total)
                bot.send_message(chat_id = update.message.chat_id, text = response)

dispatcher.add_handler(CommandHandler(['addpoint', 'rmpoint'], addrmpoint))
dispatcher.add_handler(CommandHandler(['top10'], top10))
dispatcher.add_handler(CommandHandler(['votepoint'], votepoint))
updater.start_polling()
updater.idle()
