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
    return render_template('index.html', alreadyChosen=[])




@app.route('/play/<string:alreadyChosen>')
def draw(alreadyChosen):
    all = [i+1 for i in range(75)]
    alreadyChosen = [int(i) for i in re.split('_',alreadyChosen)[1:]]
    if len(alreadyChosen) == 75:
        return redirect('/index')


    open =  [i for i in all if i not in alreadyChosen]

    pick = open[r.randint(0,len(open)-1)]
    alreadyChosen = alreadyChosen + [pick]

    square = {1:'B',2:'I',3:'N',4:'G',5:'O'}[np.ceil(pick/15)] + f'{pick}'

    return render_template('index.html', square=square, alreadyChosen=alreadyChosen)




if __name__ == "__main__":
    app.debug = True
    app.run(port=5002)
