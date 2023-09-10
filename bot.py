#!/usr/bin/python3
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging, random, time
import threading 
import os


TOKEN = os.environ['TOKEN']
bot_id = os.environ['BOTID']

draw_gifs = [
    "https://media.giphy.com/media/l0MYxttohtRUZkljy/giphy.gif",
    "https://media.giphy.com/media/WPuqO61XdwqNO2nTr6/giphy.gif"
]

winner_gifs = [
    "https://media1.giphy.com/media/JPsFUPp3vLS5q/giphy.gif?cid=549b592d64207b25e72da9abbcd9979343b9481ddc088d60&rid=giphy.gif",
    "https://media.giphy.com/media/lfmYxOkGpNtEk/giphy.gif",
    "https://media3.giphy.com/media/Jzxgefavt2aB2/giphy.gif",
    "https://media.giphy.com/media/S6qkS0ETvel6EZat45/giphy.gif"
]

sad_gifs = [
    'https://thumbs.gfycat.com/UltimateJoyfulAcornweevil-size_restricted.gif',
    "https://i.pinimg.com/originals/c3/93/24/c3932475a1a12d585d9f722adf0fb3b1.gif",
    "https://media.tenor.com/images/14d979625a1bcb15854d362bdea00790/tenor.gif",
    "https://media.tenor.com/images/9c4427af44ea18b12b0a2b029763c7fc/tenor.gif",
    "https://media1.giphy.com/media/2ROSG9dnHbqyA/giphy.gif",
]

solved_msgs = [
    'solved the word! 🥳🥳',
    'is on fire today! 🥵🔥',
    'is going places! 👏😮',
    'was born to unscramble. 💯💯',
    'is a walking vo·cab·u·lar·y 🤯',
    'could do it in their sleep 😴',
    'is a word whiz 🤓',
    "is wiiiiiildin' 😤",
    'knows it inside out 🙆🏽‍♂️',
    'is in a class of their own 🙅🏽‍♂️'
]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

games = {}

words = []

with open("wordlist.txt") as f:
    for w in f:
        words.append(w.strip())

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hi and welcome to the Ultimate Unscramble Game Bot!\n\nA bot for playing unscramble competitively in groups. Add this bot to your group to start playing.")

def players(update, context):
    chat_id = update.message.chat_id
    if chat_id not in games:
        return
    players = games[chat_id]["players"]
    finalPlayers = {k: v for k, v in sorted(players.items(), key=lambda item: item[1]['score'], reverse=True)}
    players = [(k, v) for k, v in finalPlayers.items()]
    message = 'Players:\n'
    for item in players:
        message += f'[{item[1]["data"]["first_name"]} {item[1]["data"]["last_name"] or ""}](tg://user?id={item[1]["data"]["id"]})\n'
    update.message.reply_markdown(message)

def sendEndTimer(update, context, remaining, index):
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text=f"{remaining} til the end of game")
    games[chat_id]["gameEndTimers"][index+1].start()

def gameEnder(update, context, timer=False):
    chat_id = update.message.chat_id
    user = update.message.from_user
    free = games[chat_id]["mode"] == "free"
    if chat_id not in games:
        update.message.reply_text("There's no active game, start one with /startGame")
        return
    if user["id"] not in games[chat_id]["players"] and not timer:
        update.message.reply_text("STHU you ain't even playin...")
        return
    games[chat_id]["active"] = False
    timers = games[chat_id]["gameEndTimers"]
    for item in timers:
        if(hasattr(item, 'cancel')):
            item.cancel()
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'The correct word is {games[chat_id]["correct"]}')
    if not free:
        games[chat_id]["timer"].cancel()
    players = games[chat_id]["players"]
    context.bot.send_message(chat_id=chat_id, text="Ending this game session, calculating scores...")
    finalPlayers = {k: v for k, v in sorted(players.items(), key=lambda item: item[1]['score'], reverse=True)}
    players = [(k, v) for k, v in finalPlayers.items()]
    if(len(players)):
        winner = players[0]
        if len(players) == 1 and winner[1]["score"] == 0:
            message = 'What a shame! Nobody played in this game...'
            animation = random.choice(sad_gifs)
        elif len(players) > 1 and players[0][1]["score"] == players[1][1]["score"]:
            animation = random.choice(draw_gifs)
            message = "*It's a draw!*"
        else:
            animation = random.choice(winner_gifs)
            message = f'*The Winner is* [{winner[1]["data"]["first_name"]} {winner[1]["data"]["last_name"] or ""}](tg://user?id={winner[1]["data"]["id"]})\nscore: {winner[1]["score"]}'
        message += '\n\nPlayers:\n'
        for item in players:
            message += f'{item[1]["data"]["first_name"]} {item[1]["data"]["last_name"] or ""}: {item[1]["score"]}\n'

        elapsed_time = time.time() - games[chat_id]["start_time"]
        duration = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
        message += f"\nGame duration: {duration}"
        context.bot.send_animation(chat_id=chat_id, animation=animation, caption=message, parse_mode='markdown')
    else:
        update.message.reply_text('What a shame! Nobody played in this game...')
    del games[chat_id]

def pauseGame(update, context):
    chat_id = update.message.chat_id
    user = update.message.from_user
    if chat_id not in games:
        update.message.reply_text("There's no active game, start one with /startGame")
        return
    free = games[chat_id]["mode"] == "free"
    if user["id"] not in games[chat_id]["players"]:
        update.message.reply_text("STHU you ain't even playin...")
        return

    if chat_id in games and not games[chat_id]["active"]:
        update.message.reply_text("There's a paused game, /resume it and continue playing.")
        return

    # cancelling the word time out timer
    if not free:
        games[chat_id]["timer"].cancel()
        
    # set game status to NOT active
    games[chat_id]["active"] = False


    # cancel game end timers 
    timers = games[chat_id]["gameEndTimers"]
    for item in timers:
        if(hasattr(item, 'cancel')):
            item.cancel()

    # note call setAndSendWord() on resume 
    update.message.reply_text("Game paused. You can /resume playing whenever you're ready.")

def resumeGame(update, context):
    chat_id = update.message.chat_id
    user = update.message.from_user
    if chat_id not in games:
        update.message.reply_text("There's no paused game, start one with /startGame")
        return
    free = games[chat_id]["mode"] == "free"
    
    if chat_id in games and games[chat_id]["active"]:
        update.message.reply_text("Your game session is not paused. You can /pause it, and /resume it later when you're ready.")
        return

    # check if user is permitted to resume
    if user["id"] not in games[chat_id]["players"]:
        update.message.reply_text("STHU you ain't even playin...")
        return

    # change game status to active and resuming game
    games[chat_id]["active"] = True
    update.message.reply_text("Resuming game...")

    if games[chat_id]["solved"]:
        # the timer has ended before pausing the game
        # call setAndSendWord(), that automatically sets the word time out timers
        setAndSendWord(update, context, free)
    else:
        # the timer hasn't ended at the time of pausing
        # hence, we'll just send the word again and set a timeout timer
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"The word to solve is: \n{games[chat_id]['current']}")
        if not free:
            games[chat_id]["timer"] = threading.Timer(25.0, wordTimeOut, args=(update,context))
            games[chat_id]["timer"].start()


    # set game end timers
    games[update.message.chat_id]["gameEndTimers"] = [
                threading.Timer(60, sendEndTimer, args=(update,context,'two minutes',0)),
                threading.Timer(60, sendEndTimer, args=(update,context, 'one minute', 1)),
                threading.Timer(30, sendEndTimer, args=(update,context, '30 seconds', 2)),
                threading.Timer(20, sendEndTimer, args=(update,context, '10 seconds', 3)),
                threading.Timer(10, gameEnder, args=(update,context, True)),
            ]
    games[chat_id]["gameEndTimers"][0].start()

    


def wordTimeOut(update, context, solve=False):
    chat_id = update.message.chat_id
    games[chat_id]["solved"] = True
    if solve:
        update.message.reply_text(f'The correct word is {games[chat_id]["correct"]}')
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'The correct word is {games[chat_id]["correct"]}')
    return setAndSendWord(update, context, free=solve)

def shuffle(word):
    original = word
    same = True
    while(same):
        word = list(word)
        random.shuffle(word)
        word = "".join(word)
        same = word == original
    return word


def setAndSendWord(update, context, free=False):
    chat_id = update.message.chat_id
    if games[chat_id]["solved"] and games[chat_id]["active"]:
        new_w = random.choice(words)
        games[chat_id]["correct"] = new_w
        games[chat_id]["current"] = shuffle(new_w)
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"The word to solve is: \n{games[chat_id]['current']}")

        games[chat_id]["solved"] = False
        if not free:
            games[chat_id]["timer"] = threading.Timer(25.0, wordTimeOut, args=(update,context))
            games[chat_id]["timer"].start()

def welcome_group_addition(update, context):
    new_members = update.message.new_chat_members
    for member in new_members:
        if(member.id==bot_id):
            context.bot.send_message(chat_id=update.effective_chat.id, text="Hi! You just added the Ultimate Unscramble Game bot to your group. \n\nTo start a game, just use the /startGame command and start solving!\n\nBy continuing to use this bot, you are agreeing to the /terms of service. Enjoy!")
            

def checkGroupAddition(update, context):
    if(len(update.message.new_chat_members)):
        return welcome_group_addition(update, context)

def checkSolution(update, context):
    chat_id = update.message.chat_id
    free = games[chat_id]["mode"] == "free"
    if chat_id in games and games[chat_id]["active"]:
        solution = update.message.text.strip().split()[0]
        user = update.message.from_user
        if(not games[chat_id]["solved"] and solution.lower()==games[chat_id]["correct"].lower()):
            games[chat_id]["solved"] = True
            if not free:
                games[chat_id]["timer"].cancel()
            celebrate_msg = random.choice(solved_msgs)
            update.message.reply_markdown(f'[{user["first_name"]} {user["last_name"] or ""}](tg://user?id={user["id"]}) {celebrate_msg}')
            if user["id"] not in games[chat_id]["players"]:
                games[chat_id]["players"][user['id']] = {"score":0, "data":user}
            games[chat_id]["players"][user["id"]]["score"] += 1
            return setAndSendWord(update, context, free)

def extendGameTime(update, context):
    chat_id = update.message.chat_id
    user = update.message.from_user
    if chat_id not in games:
        return
    if user["id"] in games[chat_id]["players"]:
        timers = games[chat_id]["gameEndTimers"]
        for item in timers:
            if(hasattr(item, 'cancel')):
                item.cancel()
        update.message.reply_text("Game time extended. You can /end the game when/if you feel like it.")
        games[update.message.chat_id]["gameEndTimers"] = [
                    threading.Timer(60, sendEndTimer, args=(update,context,'two minutes',0)),
                    threading.Timer(60, sendEndTimer, args=(update,context, 'one minute', 1)),
                    threading.Timer(30, sendEndTimer, args=(update,context, '30 seconds', 2)),
                    threading.Timer(20, sendEndTimer, args=(update,context, '10 seconds', 3)),
                    threading.Timer(10, gameEnder, args=(update,context, True)),
                ]
        games[chat_id]["gameEndTimers"][0].start()
    else:
        update.message.reply_text("STHU you ain't even playin...")
     
def gameStarter(update, context, free=False):
    chat_id = update.message.chat_id
    games[update.message.chat_id]["active"] = True
    games[update.message.chat_id]["gameEndTimers"] = [
                threading.Timer(60, sendEndTimer, args=(update,context,'two minutes',0)),
                threading.Timer(60, sendEndTimer, args=(update,context, 'one minute', 1)),
                threading.Timer(30, sendEndTimer, args=(update,context, '30 seconds', 2)),
                threading.Timer(20, sendEndTimer, args=(update,context, '10 seconds', 3)),
                threading.Timer(10, gameEnder, args=(update,context, True)),
            ]
    games[chat_id]["gameEndTimers"][0].start()
    update.message.reply_text('Starting game... Buckle Up!\n\nGame duration is 3 minutes, you can always /extend game time tho')
    return setAndSendWord(update, context, free)


def startGame(update, context):

    chat_id = update.message.chat_id
    user = update.message.from_user

    if chat_id not in games:
        games[chat_id] = {
            "mode": "normal",
            "current": "", 
            "correct": "", 
            "solved": True, 
            "active": False, 
            "players": {},
            "start_time": time.time()
        }
        # add whoever it's who started the game to players 
        games[chat_id]["players"][user['id']] = {"score":0, "data":user}
        gameStarter(update,context)

    elif chat_id in games and not games[chat_id]["active"]:
        update.message.reply_text("There's a paused game, /resume it and continue playing.")

    elif chat_id in games and games[chat_id]["active"]:
        update.message.reply_text("A game is already active...")


def startFreeGame(update, context):
    chat_id = update.message.chat_id
    if chat_id not in games:
        games[chat_id] = {
            "mode": "free",
            "current": "", 
            "correct": "", 
            "solved": True, 
            "active": False, 
            "players": {},
            "start_time": time.time()
        }
        gameStarter(update, context, free=True)

def solve(update, context):
    chat_id = update.message.chat_id

    if chat_id in games and (games[chat_id]["mode"] == "free" or len(games[chat_id]["players"]) == 1):
        wordTimeOut(update, context, solve=True)



def terms(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text='*Terms of Service:* \n\nI hereby agree to send @ahmedXabdeen a bag of homemade cookies whenever he asks for them.')

start_handler = CommandHandler('start', start)
terms_handler = CommandHandler('terms', terms)
end_handler = CommandHandler('end', gameEnder)
players_handler = CommandHandler('players', players)
startGame_handler = CommandHandler('startGame', startGame)
startFreeGame_handler = CommandHandler('startFreeGame', startFreeGame)
extendGameTime_handler = CommandHandler('extend', extendGameTime)
solve_handler = CommandHandler('solve', solve)
pauseGame_handler = CommandHandler('pause', pauseGame)
resumeGame_handler = CommandHandler('resume', resumeGame)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(terms_handler)
dispatcher.add_handler(end_handler)
dispatcher.add_handler(players_handler)
dispatcher.add_handler(startGame_handler)
dispatcher.add_handler(startFreeGame_handler)
dispatcher.add_handler(solve_handler)
dispatcher.add_handler(extendGameTime_handler)
dispatcher.add_handler(pauseGame_handler)
dispatcher.add_handler(resumeGame_handler)
dispatcher.add_handler(MessageHandler(Filters.text, checkSolution))
dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, checkGroupAddition), group=9)

updater.start_polling()
updater.idle()