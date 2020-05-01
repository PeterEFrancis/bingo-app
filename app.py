from flask import Flask, render_template, url_for, redirect
import re
import random
import html
import os
import sys
import numpy as np
import random as r


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




@app.route('/card')
def card():

    B = r.sample(range(1,16), 5)
    I = r.sample(range(16,31), 5)
    N = r.sample(range(31,46), 5)
    G = r.sample(range(46,61), 5)
    O = r.sample(range(61,76), 5)

    cardArray = np.array([B, I, N, G, O]).T
    cardArray[2][2] = 0

    return render_template('card.html', cardArray=cardArray.tolist())




if __name__ == "__main__":
    app.debug = True
    app.run(port=5002)
