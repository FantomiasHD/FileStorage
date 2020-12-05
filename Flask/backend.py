from flask import Flask
from flask import send_from_directory, request, render_template, make_response, redirect, g
from werkzeug.utils import secure_filename

from os import listdir, mkdir
from os.path import isfile, join

import sqlite3
import base64
import hashlib
import re
import random
import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "KHC2zY6tCH3ppS4BapA4bWFTrykm0eSJ"
app.config["UPLOAD_FOLDER"] = "public"

app.config["DATABASE"] = "database.db"

cookieCheck = r"^{'user': '[\w\.]{1,15}', 'perm': '(W|R|F)', 'web': '[\d]+'}$"

#cookieSaftyFeature
def generateKey():
    random.seed(int(datetime.datetime.now().strftime("%m")))
    cookieKey = int(int(datetime.datetime.now().strftime("%y"))*random.random()*100*random.random()*100*10000000)
    return cookieKey

#database Commands
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config["DATABASE"])
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

#simple Method to evaluate the cookie
def checkCookie(cookie):
    cookie = base64.b64decode(cookie)
    cookieDict = eval(cookie)
    username = saveString(cookieDict["user"])
    query = query_db("SELECT * FROM USER WHERE username = ?", [username], one=True)
    if re.match(cookieCheck, cookie.decode('utf-8')):
        if query:
            if cookieDict["web"] == str(generateKey()) and cookieDict["perm"] == query["permissions"]:
                return (True, query['permissions'], username)
    return (False, None, None)

def saveString(string):
    string = string.replace('\'', "")
    string = string.replace('\"', "")
    return string

#create account Method
def createAccount(username, password, permissions):
    username = saveString(username)
    password = saveString(password)
    password = hashlib.md5(password.encode()).hexdigest()
    try:
        if not query_db(f"SELECT * FROM USER WHERE username = '{username}'"):
            db = get_db()
            db.cursor().execute(f'INSERT INTO USER (username, password, permissions) VALUES ("{username}", "{password}", "{permissions}")')
            db.commit()
            mkdir(app.config["UPLOAD_FOLDER"]+"/"+username)
        else:
            return 1
    except Exception as e:
        print(e)
        return 0

#account managment
@app.route("/")
def main():
    cookie = request.cookies.get('auth')
    if cookie:
        perm = checkCookie(cookie)
        if perm[0] and not perm[1] == "W":
            return redirect('/download')
        elif perm[0] and not perm[1] == "R":
            return redirect("/upload")

    return render_template("Login.html")

@app.route('/signup')
def signup():
    return render_template("SignUp.html", err="")

@app.route('/signupper', methods=["POST", "GET"])
def signupper():
    user = request.form["user"]
    pass1 = request.form["pass"]
    pass2 = request.form["pass2"]
    perm = request.form["rights"]
    if pass1 == pass2:
        tmp = createAccount(user, pass1, perm)
        if tmp == 0:
            return render_template("SignUp.html", err="Something went wrong while creating an Account")
        elif tmp == 1:
            return render_template("SignUp.html", err="Username already exists")
        else:
            return redirect('/')
    else:
        return render_template("SignUp.html", err="Passwords don't match up!")

#download managment
@app.route('/download')
def download():
    cookie = request.cookies.get('auth')
    if cookie:
        perm = checkCookie(cookie)
        if perm[0] and not perm[1] == "W":
            onlyfiles = [f for f in listdir(app.config["UPLOAD_FOLDER"]+"/"+perm[2]) if isfile(join(app.config["UPLOAD_FOLDER"]+"/"+perm[2], f))]
            return render_template("test_temp.html", files=onlyfiles)
    return redirect('/', 403)

@app.route('/downloader/<path:filename>')
def downloader(filename):
    cookie = request.cookies.get('auth')
    if cookie:
        perm = checkCookie(cookie)
    if perm[0] and not perm[1] == "W":
        return send_from_directory(app.config["UPLOAD_FOLDER"]+"/"+perm[2], filename, as_attachment=True)
    return redirect('/', 403)

#upload managment
@app.route('/upload', methods=['GET', 'POST'])
def uploader():
    cookie = request.cookies.get('auth')
    if cookie:
        perm = checkCookie(cookie)
    if perm[0] and not perm[1] == "R":
        if request.method == 'POST':
            f = request.files['file']
            f.save(app.config["UPLOAD_FOLDER"]+'/'+perm[2] + '/' + secure_filename(f.filename))
        return render_template("uploader.html")
    return redirect('/', 403)

#cookie managment
@app.route('/setcookie', methods=['POST', 'GET'])
def setcookie():
    if request.method == 'POST':
        username = request.form["user"]
        password = request.form["pass"]
        username = saveString(username)
        password = saveString(password)
        password = hashlib.md5(password.encode()).hexdigest()
        query = query_db("SELECT * FROM USER WHERE username = ?", [username], one=True)
        if query:
            if query["password"] == password:
                resp = redirect('/download')
                resp.set_cookie('auth', base64.b64encode(f"{{'user': '{username}', 'perm': '{query['permissions']}', 'web': '{generateKey()}'}}".encode()))
                return resp
    return redirect('/')

@app.route('/removecookie')
def removecookie():
    resp = make_response(redirect('/'))
    resp.set_cookie('auth', "", expires=0)
    return resp