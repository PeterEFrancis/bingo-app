from flask import Flask, render_template, url_for, redirect, request, send_from_directory, jsonify
import re
import random
import html
import os
import sys
import numpy as np
import random as r
from numba import njit
import json

app = Flask(__name__)


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')



@app.route('/caller/<string:alreadyChosen>')
def caller(alreadyChosen):

    alreadyChosenArray = []
    square = ""

    if alreadyChosen != "p":
         alreadyChosenArray = [int(i) for i in re.split('_',alreadyChosen)[1:]]
         pick = alreadyChosenArray[-1]
         square = {1:'B',2:'I',3:'N',4:'G',5:'O'}[np.ceil(pick/15)] + f'{pick}'

    return render_template('caller.html', square = square, alreadyChosenArray=alreadyChosenArray)



four = np.fromfile('board_encoding/four.dat', dtype=int).reshape(32760,4)
five = np.fromfile('board_encoding/five.dat', dtype=int).reshape(360360,5)

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


@app.route('/card')
def card():

    B = r.sample(range(1,16), 5)
    I = r.sample(range(16,31), 5)
    N = r.sample(range(31,46), 5)
    G = r.sample(range(46,61), 5)
    O = r.sample(range(61,76), 5)

    cardArray = np.array([B, I, N, G, O]).T
    cardArray[2][2] = 0

    cardID = encode(cardArray)

    return render_template('card.html', cardArray=cardArray.tolist(), cardID= cardID)



@app.route('/card/<string:cardID>')
def openCardID(cardID):

    cardArray = decode(cardID)

    return render_template('card.html', cardArray=cardArray.tolist(), cardID= cardID)










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



if __name__ == "__main__":
    app.debug = True
    app.run(port=5002)
