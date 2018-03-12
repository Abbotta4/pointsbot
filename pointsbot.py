#!/usr/bin/env python2
import logging,ConfigParser,io,sqlite3,time,os
from telegram.ext import Updater,CommandHandler,CallbackQueryHandler
from telegram import InlineKeyboardButton,InlineKeyboardMarkup
from telegram.error import BadRequest
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
    def __init__(self, message):
          self.message = message
    def __enter__(self):
        self.connfile = 'db/' + str(self.message.chat_id) + '.db'
        self.conn = sqlite3.connect(self.connfile)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS points (username TEXT PRIMARY KEY, adds INT, rms INT, total INT)''')
        return self.cursor
    def __exit__(self, type, value, traceback):
        self.conn.commit()
        self.cursor.close()

class vote_cursor:
    def __init__(self, update):
          self.update = update
    def __enter__(self):
        if self.update.callback_query is None:
            self.connfile = 'db/' + str(self.update.message.chat_id) + '_' + str(self.update.message.message_id) + '_vote.db'
        else:
            self.connfile = 'db/' + str(self.update.callback_query.message.chat_id) + '_' + str(self.update.callback_query.message.message_id - 1) + '_vote.db'
        self.conn = sqlite3.connect(self.connfile)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS votes (uid INT PRIMARY KEY, adds INT, rms INT)''')
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

    return usernames

@run_async
def addrmpoint(bot, update):
    with db_cursor(update.message) as cursor:
        usernames = get_users(bot, update, cursor)
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
    with db_cursor(update.message) as cursor:
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
def votepoint(bot, update, job_queue):
    def callback_countdown(bot, job):
        with vote_cursor(update) as v_cursor:
            job.context[1] = job.context[1] - 15
            v_cursor.execute("""SELECT sum(adds), sum(rms) FROM votes""")
            votes = v_cursor.fetchone()
            button_list = [[InlineKeyboardButton("add " + str(votes[0]), callback_data='add'), InlineKeyboardButton("rm " + str(votes[1]), callback_data='rm')]]
            reply_markup = InlineKeyboardMarkup(button_list)
            job.context[0].edit_text(text="Should " + u + " gain or lose a point? {}".format(str((job.context[1]//60)).zfill(2) + "m" + str((job.context[1]%60)).zfill(2) + "s"), reply_markup = reply_markup)

    def callback_finish(bot, job):
        with vote_cursor(update) as v_cursor, db_cursor(update.message) as cursor:
            job.context[1].schedule_removal()
            v_cursor.execute("""SELECT sum(adds), sum(rms) FROM votes""")
            votes = v_cursor.fetchone()
            add_votes = votes[0]
            rm_votes = votes[1]
            if add_votes != rm_votes:
                username = '@' + job.context[0].from_user.username
                cursor.execute("""SELECT adds, rms FROM points WHERE username = ?""", (u.lower(), ))
                points = cursor.fetchone()
                if points is None:
                    points = [0, 0, 0]
                adds = points[0]
                rms = points[1]
                job.context[0].edit_text(text="Vote finished\nAdds: " + str(add_votes) + "\nRms: " + str(rm_votes))
                if add_votes > rm_votes:
                    adds = adds + 1
                if add_votes < rm_votes:
                    rms = rms + 1
                total = adds - rms
                cursor.execute("""REPLACE INTO points (username, adds, rms, total) VALUES (?, ?, ?, ?)""", (u.lower(), adds, rms, total))
                response = u + ' - ' + '+' + str(adds) + '/-' + str(rms) + ' total: ' + str(total)
                bot.send_message(chat_id = update.message.chat_id, text = response)
        os.remove('db/' + str(update.message.chat_id) + '_' + str(update.message.message_id) + '_vote.db')

    with vote_cursor(update) as v_cursor:
        pass # must create database first
    
    with db_cursor(update.message) as cursor:
        usernames = get_users(bot, update, cursor)
        if not usernames:
            bot.send_message(chat_id = update.message.chat_id, text = 'No username(s) sent.')

        if len(usernames) <= 1:
            for u in usernames:
                cursor.execute("""SELECT adds, rms FROM points WHERE username = ?""", (u.lower(), ))
                points = cursor.fetchone()
                if points is None:
                    points = [0, 0, 0]
                adds = points[0]
                rms = points[1]
                button_list = [[InlineKeyboardButton("add 0", callback_data='add'), InlineKeyboardButton("rm 0", callback_data='rm')]]
                reply_markup = InlineKeyboardMarkup(button_list)
                votemessage = bot.send_message(chat_id = update.message.chat_id, text = "Should " + u + " gain or lose a point? 05m00s", reply_markup = reply_markup)

                counter = 300
                job_second = job_queue.run_repeating(callback_countdown, interval=15, context=[votemessage, counter], name='countdown')
                job_finish = job_queue.run_once(callback_finish, 300, context=[votemessage, job_second], name='countdown removal')
        else:
            bot.send_message(chat_id = update.message.chat_id, text = 'Cannot vote on more than one user at once')
                        
def button(bot, update):
    query = update.callback_query
    if os.path.isfile('db/' + str(query.message.chat_id) + '_' + str(query.message.message_id - 1) + '_vote.db'):
        with vote_cursor(update) as v_cursor:
            if query.data == 'add':
                v_cursor.execute("""REPLACE INTO votes (uid, adds, rms) VALUES (?, 1, 0)""", (query.from_user.id, ))
            else: # query.data is 'rm'
                v_cursor.execute("""REPLACE INTO votes (uid, adds, rms) VALUES (?, 0, 1)""", (query.from_user.id, ))
            v_cursor.execute("""SELECT sum(adds), sum(rms) FROM votes""")
            votes = v_cursor.fetchone()
            button_list = [[InlineKeyboardButton("add " + str(votes[0]), callback_data='add'), InlineKeyboardButton("rm " + str(votes[1]), callback_data='rm')]]
            reply_markup = InlineKeyboardMarkup(button_list)
            try:
                query.message.edit_reply_markup(reply_markup = reply_markup)
            except BadRequest:
                pass
                
    else:
        print('couldnt see file: db/' + str(query.message.chat_id) + '_' + str(query.message.message_id) + '_vote.db')
            

dispatcher.add_handler(CommandHandler(['addpoint', 'rmpoint'], addrmpoint))
dispatcher.add_handler(CommandHandler(['top10'], top10))
dispatcher.add_handler(CommandHandler(['votepoint'], votepoint, pass_job_queue=True))
dispatcher.add_handler(CallbackQueryHandler(button))

updater.start_polling()
updater.idle()
