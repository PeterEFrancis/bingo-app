from flask import Flask, render_template, url_for, redirect, request, send_from_directory, jsonify, session, Response
from flask_sqlalchemy import SQLAlchemy
from flask_heroku import Heroku
import re
import random
import html
import os
import sys
import numpy as np
import random as r
from numba import njit
import json
import random
import time


app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/call-bingo'
heroku = Heroku(app)




#      _       _        _
#   __| | __ _| |_ __ _| |__   __ _ ___  ___
#  / _` |/ _` | __/ _` | '_ \ / _` / __|/ _ \
# | (_| | (_| | || (_| | |_) | (_| \__ \  __/
#  \__,_|\__,_|\__\__,_|_.__/ \__,_|___/\___|
#


db = SQLAlchemy(app)

class Game(db.Model):
    __tablename__ = "games"
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    players = db.Column(db.Text)
    board = db.Column(db.Text)
    host = db.Column(db.Text)
    date = db.Column(db.Text)
    last = db.Column(db.Text)

    def __init__(self, host):
        self.players = '{}'
        self.board = '0' * 75
        self.open = False
        self.host = host
        self.date = time.asctime(time.localtime(time.time()))
        self.last = '&nbsp;'

    def flip_square(self, num):
        b = list(self.board)
        b[num - 1] = str(1 - int(b[num - 1]))
        self.board = "".join(b)
        if b[num - 1] == '1':
            self.last = num_to_bingo(num)
        else:
            self.last = '&nbsp;'
        db.session.commit()

    def clear_board(self):
        self.board = '0' * 75
        self.last = '&nbsp;'
        db.session.commit()

    def add_player(self, player):
        pdict = eval(self.players)
        pdict[player] = []
        self.players = str(pdict)
        db.session.commit()

    def remove_player(self, player):
        pdict = eval(self.players)
        pdict.pop(player)
        self.players = str(pdict)
        db.session.commit()

    def deal(self, num_cards):
        pdict = eval(self.players)
        cardIDs = get_n_cards(len(pdict) * num_cards)
        for i, player in enumerate(pdict):
            pdict[player] = cardIDs[i * num_cards : (i + 1) * num_cards]
        self.players = str(pdict)
        db.session.commit()

    def get_code(self):
        return id_to_code(self.id)

    def has_player(self, player):
        print(eval(self.players))
        return player in eval(self.players)


def id_to_code(id):
    return base_10_to_26(100 * id + 26**3)

def code_to_id(code):
    return int((base_26_to_10(code) - 26**3) / 100)

def get_game(code):
    id = code_to_id(code)
    return db.session.query(Game).filter(Game.id == id)

def is_game(code):
    return len(list(get_game(code))) != 0


@app.route('/game_access/<string:s>', methods=['POST'])
def game_access(s):
    if request.method != 'POST':
        return 'Access Denied',403
    games = get_game(request.form['code'])
    if len(list(games)) == 0:
        return "No game found."
    game = games[0]
    if s == 'board':
        return jsonify({'success':'true', 'board':game.board, 'last':game.last})
    return 'Access Denied.'


@app.route('/host_access/<string:function>', methods=['POST'])
def host_access(function):
    if request.method != 'POST':
        'Access Denied.',403
    if 'username' not in session:
        return jsonify({'success':'false', 'error':"You are not signed in."})
    games = get_game(request.form['code'])
    if len(list(games)) == 0:
        return jsonify({'success':'false', 'error':'No Game Found.'})
    game = games[0]
    if not get_user(session['username']).has_game(game):
        return jsonify({'success':'false', 'error':"You don't have access to edit this game."})

    if function == "flip_square":
        game.flip_square(int(request.form['num']))
        return jsonify({'success':'true'})
    elif function == "clear_board":
        game.clear_board()
        return jsonify({'success':'true'})
    elif function == "get_players":
        return jsonify(eval(game.players))
    elif function == "remove_players":
        for p in request.form['players'].split(","):
            game.remove_player(p)
        return jsonify({'success':'true'})
    elif function == "check_for_bingo":
        bingo_dict = {}
        for p in request.form['players'].split(","):
            player_cardIDs = eval(game.players)[p]
            for cardID in player_cardIDs:
                check = check_card(cardID, game.board, BINGO_TYPES)
                if len(check) > 0:
                    if p not in bingo_dict:
                        bingo_dict[p] = []
                    bingo_dict[p].append([cardID, check])
        return jsonify({'success':'true', 'bingo_dict': bingo_dict})
    elif function == "deal":
        game.deal(int(request.form['num_cards']))
        return jsonify({'success':'true'})
    else:
        return 'Access Denied.',404



class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text)
    username = db.Column(db.Text)
    password = db.Column(db.Text)
    games = db.Column(db.Text)

    def __init__(self, email, username, password):
        self.email = email
        self.username = username
        self.password = password
        self.games = ''

    def add_game(self, game):
        self.games += str(game.id) + ','
        db.session.commit()

    def has_game(self, game):
        return str(game.id) in self.games.split(',')


def is_user(username):
    return len(list(db.session.query(User).filter(User.username == username))) != 0

def get_user(username):
    return db.session.query(User).filter(User.username == username)[0]


@app.route('/initialize')
def initialize():
    db.drop_all()
    db.create_all()

    for i in ['a','b','c','d']:
        db.session.add(User(f'{i}@{i}.com',i,i))
        db.session.commit()

    return 'done'







#  _          _
# | |__   ___| |_ __   ___ _ __ ___
# | '_ \ / _ | | '_ \ / _ | '__/ __|
# | | | |  __| | |_) |  __| |  \__ \
# |_| |_|\___|_| .__/ \___|_|  |___/
#              |_|



four = np.fromfile('board_encoding/four.dat', dtype=int).reshape(32760,4)
five = np.fromfile('board_encoding/five.dat', dtype=int).reshape(360360,5)


@njit
def base_10_to_26(n):
    digits = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    s = ""
    while n != 0:
        r = n % 26
        s = digits[r] + s
        n = n // 26
    return s

def base_26_to_10(s):
    s = s.upper()
    arr = [el for el in s][::-1]
    digits = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    n = 0
    while len(arr) != 0:
        n = digits.index(arr.pop()) + n * 26
    return n


@njit
def find(row):
    if len(row) == 4:
        for i in range(32760):
            if row[0] == four[i][0] and row[1] == four[i][1] and row[2] == four[i][2] and row[3] == four[i][3]:
                return i
    else:
        for i in range(360360):
            if row[0] == five[i][0] and row[1] == five[i][1] and row[2] == five[i][2] and row[3] == five[i][3] and row[4] == five[i][4]:
                return i

def to_base_62(n):
    digits = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    s = ""
    while n!=0:
        r = n % 62
        s = digits[r] + s
        n = n // 62
    return s

def to_base_10(base_62):
    base_62_arr = [el for el in base_62][::-1]
    digits = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    n = 0
    while len(base_62_arr) != 0:
        n = digits.index(base_62_arr.pop()) + n * 62
    return n

def encode(cardArray):
    card = cardArray.copy()

    for col in range(5):
        card.T[col] -= 15 * col + 1

    B = card.T[0]
    I = card.T[1]
    N = np.delete(card.T[2],2)
    G = card.T[3]
    O = card.T[4]

    num = 0
    for row in [B, I, N, G, O]:
        num = find(row) + 360360 * num

    return to_base_62(num)

def decode(base_62_num):
    card = np.zeros((5,5))
    base_10 = to_base_10(base_62_num)
    for i in range(5):
        num = base_10 % 360360
        if i == 2:
            card[2] = np.insert(four[num],2,-31)
        else:
            card[4 - i] = five[num]
        base_10 = base_10 // 360360

    cardArray = card.T
    for col in range(5):
        card[col] += 15 * col + 1

    return np.array(card, dtype=int).T

def get_random_card_id():

    B = r.sample(range(1,16), 5)
    I = r.sample(range(16,31), 5)
    N = r.sample(range(31,46), 5)
    G = r.sample(range(46,61), 5)
    O = r.sample(range(61,76), 5)

    cardArray = np.array([B, I, N, G, O]).T
    cardArray[2][2] = 0

    cardID = encode(cardArray)

    return cardID

def num_to_bingo(num):
    return 'BINGO'[(num - 1) // 15] + ' ' + str(num)

def get_n_cards(n):
    cardIDs = []
    while len(cardIDs) < n:
        num = 0
        for i in range(5):
            num = r.randint(1,(32760 if i == 2 else 360360) - 1) + 360360 * num
        cardID = to_base_62(num)
        if cardID not in cardIDs:
            cardIDs.append(cardID)
    return cardIDs


BINGO_TYPES = {
    "classic":
        [[[r,c] for c in range(5)] for r in range(5)]
      + [[[r,c] for r in range(5)] for c in range(5)]
      + [[[0,0],[1,1],[2,2],[3,3],[4,4]]]
      + [[[0,4],[1,3],[2,2],[3,1],[4,0]]],
    "blackout": [[[r,c] for c in range(5) for r in range(5)]]
}

def check_card(cardID, board, types):
    # print(board)
    out = []
    cardArray = decode(cardID)
    # print(cardArray)
    for t in types:
        for square_set in BINGO_TYPES[t]:
            # print("square_set =", square_set)
            for square in square_set:
                # print("cardnum =", cardArray[square[0]][square[1]])
                # print("board @ cn = ", board[cardArray[square[0]][square[1]] - 1])
                if board[cardArray[square[0]][square[1]] - 1] != '1':
                    break
            else:
                out.append(t)
                break
    return out









#  _ __   __ _  __ _  ___    __ _  ___ ___ ___  ___ ___
# | '_ \ / _` |/ _` |/ _ \  / _` |/ __/ __/ _ \/ __/ __|
# | |_) | (_| | (_| |  __/ | (_| | (_| (_|  __/\__ \__ \
# | .__/ \__,_|\__, |\___|  \__,_|\___\___\___||___/___/
# |_|          |___/






@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', account_bar = get_account_bar())



@app.route('/all')
def all():
    return render_template('all.html', all_games=db.session.query(Game), all_users=db.session.query(User))




@app.route('/new_game', methods=['POST'])
def new_game():
    if request.method != 'POST':
        return 'Access Denied',403
    if 'username' in session:
        game = Game(host=session['username'])
        db.session.add(game)
        db.session.commit()
        get_user(session['username']).add_game(game)
        return jsonify({'success':'true', 'code':game.get_code()})
    else:
        return jsonify({'success':'false', 'error':"You're not logged in."})




@app.route('/game/<string:code>')
def game(code):
    if not is_game(code):
        return "No game found."
    game = get_game(code)[0]
    if 'username' in session:
        if get_user(session['username']).has_game(game):

            return render_template(
                'game.html',
                account_bar = get_account_bar(),
                mode = 'host',
                code = game.get_code(),
                board = game.board,
                players = game.players
            )
    return render_template(
        'game.html',
        account_bar = get_account_bar(),
        mode = 'player',
        code = game.get_code(),
        board = game.board
    )





def get_account_bar():
    username = ''
    if 'username' in session:
        username = session['username']
    return render_template(
        'account_bar.html',
        loggedin=('username' in session),
        username=username,
        games=db.session.query(Game).filter(Game.host == username)
    )



@app.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        if len(list(db.session.query(User).filter(User.email == request.form['email']))) != 0:
            return jsonify({'success':'false','error':'A user with this email already exists.'})
        elif len(list(db.session.query(User).filter(User.username == request.form['username']))) != 0:
            return jsonify({'success':'false','error':'A user with this username already exists.'})
        db.session.add(
            User(
                request.form['email'],
                request.form['username'],
                request.form['password']
            )
        )
        db.session.commit()
        return jsonify({'success':'true'})
    return 'Access Denied'




@app.route('/login', methods=['POST'])
def login():
    if request.method != 'POST':
        return 'Access Denied',403
    users = db.session.query(User).filter(User.username == request.form['username'])
    if len(list(users)) == 0:
        return jsonify({'success':'false','error':'No user with this username exists.'})
    elif users[0].password != request.form['password']:
        return jsonify({'success':'false','error':'The entered password is incorrect.'})
    session['username'] = request.form['username']
    return jsonify({'success':'true'})





@app.route('/logout', methods=['POST'])
def logout():
    if request.method != 'POST':
        return 'Access Denied',403
    session.pop('username', None)
    return jsonify({'success':'true'})







@app.route('/new_cards/<int:num>')
def new_cards(num):
    return redirect('/cards/' + ','.join(get_n_cards(num)))




def get_cardHTML(cardIDs):
    cardHTML = ""
    for cardID in cardIDs:
        cardHTML += ('<br>' * 5) + ('<br class="print">' * 5) + render_template('card.html', cardID=cardID, cardArray=decode(cardID).tolist())
        if cardID != cardIDs[-1]:
            cardHTML += '<div class="pagebreak"></div>'
    return cardHTML



@app.route('/cards/<string:cardIDstrings>')
def cards(cardIDstrings):
    cardIDs = cardIDstrings.split(',')
    return render_template(
        'cards.html',
        mode='blank',
        num=len(cardIDs),
        cardHTML=get_cardHTML(cardIDs)
    )




@app.route('/caller')
def caller():
    return render_template('caller.html')




@app.route('/join')
@app.route('/join/')
def join_free():
    return join('')

@app.route('/join/<string:code>')
def join(code):
    if is_game(code) or code == "":
        return render_template(
            'join.html',
            account_bar = get_account_bar(),
            code = code
        )
    return "No game found."




@app.route('/join_game', methods=['POST'])
def join_game():
    if request.method != 'POST':
        return 'Access Denied'
    if not is_game(request.form['code']):
        return jsonify({'success':'false', 'error':'No game found.'})
    game = get_game(request.form['code'])[0]
    if game.has_player(request.form['player']):
        return jsonify({'success':'false', 'error':'This username is already in use. Try another!'})
    session['player'] = request.form['player']
    game.add_player(request.form['player'])
    return jsonify({'success':'true', 'code':game.get_code()})



@app.route('/play/<string:code>')
def play(code):
    if not is_game(code):
        return jsonify({'success':'false', 'error':'No game found.'})
    game = get_game(code)[0]
    if 'player' not in session:
        return redirect('/join/' + code)
    if game.has_player(session['player']):
        cardIDs = eval(game.players)[session['player']]
        return render_template(
            'cards.html',
            mode='player',
            player=session['player'],
            num=len(cardIDs),
            cardHTML=get_cardHTML(cardIDs)
        )





















if __name__ == "__main__":
    secret = """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"""
    app.secret_key = secret
    app.debug = True
    app.run()

















































# @app.route('/new_game')
# def new_game():
#     game = Game()
#     db.session.add(game)
#     db.session.commit()
#     return redirect('/game/' + game.get_code())
#
#

#
#
#
#
# @app.route('/play')
# def play():
#     return 'play'
#
#
#
# @app.route('/join', methods=['POST'])
# def join_page():
#     if request.method == 'POST':
#         return request.form
#     return 'Access Denied'










































# @app.route('/caller/<string:alreadyChosen>')
# def caller(alreadyChosen):
#
#     alreadyChosenArray = []
#     square = ""
#
#     if alreadyChosen != "p":
#          alreadyChosenArray = [int(i) for i in re.split('_',alreadyChosen)[1:]]
#          pick = alreadyChosenArray[-1]
#          square = {1:'B',2:'I',3:'N',4:'G',5:'O'}[np.ceil(pick/15)] + f'{pick}'
#
#     return render_template('caller.html', square = square, alreadyChosenArray=alreadyChosenArray)








# @app.route('/cards/player=<string:player>/<string:cardIDs>')
# def openCardIDs(player, cardIDs):
#
#     cardIDs = cardIDs.split("&")
#
#     cardArrays = {}
#     for cardID in cardIDs:
#         cardArrays[cardID] = decode(cardID).tolist()
#
#     return render_template('cards.html', player=player, cardArrays = cardArrays, cardIDs = cardIDs)




#
# @app.route('/generate', methods=['POST'])
# def generate():
#     if request.method == 'POST':
#         name = request.form['name']
#         players = request.form['players'].split("&");
#         number = int(request.form['number'])
#
#         cards = []
#         while len(cards) < len(players) * number:
#             cards += [get_random_card_id()]
#             cards = list(set(cards))
#
#         URL = "https://call-bingo.herokuapp.com/game"
#         URL += "/name=" + name
#         URL += "/players=" + request.form['players']
#         URL += "/cardIDs=" + "&".join(cards)
#
#         return URL
#
#     return 'Access Denied'





# @app.route('/game/name=<string:gameName>/players=<string:players>/cardIDs=<string:cardIDs>')
# def game(gameName, players, cardIDs):
#
#     players = players.split("&")
#     cardIDs = cardIDs.split("&")
#     number = int(len(cardIDs)/len(players))
#
#     cardDict = {}
#     for player in players:
#         cardDict[player] = "&".join([cardIDs.pop() for i in range(number)])
#
#     return render_template("game.html", gameName=gameName, cardDict=cardDict)
#























# @app.route('/check', methods=['POST'])
# def check():
#     if request.method == 'POST':
#
#         cardID = request.form['cardID']
#         cardArray = decode(cardID)
#         alreadyChosenStr = request.form['alreadyChosenStr']
#         alreadyChosen = alreadyChosenStr.split("&")
#
#         standard = False
#
#         for i in range(5):
#             if all([num in alreadyChosen for num in cardArray[i]]):
#                 standard = True
#                 break
#             if all([num in alreadyChosen for num in cardArray.T[i]]):
#                 standard = True
#                 break
#         if all([cardArray.T[i][i] in alreadyChosen for i in range(5)]):
#             standard = True
#         if all([cardArray.T[4 - i][i] in alreadyChosen for i in range(5)]):
#             standard = True
#
#         return jsonify({'standard':str(standard)})
#
#     return 'Access Denied'
