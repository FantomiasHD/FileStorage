# Copyright Simon Felix Seeger


from flask import Flask
from flask import send_from_directory, request, render_template, make_response, redirect, g
from werkzeug.utils import secure_filename

from os import listdir, mkdir, remove
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
app.static_folder = 'static'

app.config["DATABASE"] = "database.db"

cookieCheck = r"^{'user': '[\w\.]{1,15}', 'web': '[\d]+'}$"


# cookieSaftyFeature
def generateKey():
    random.seed(int(datetime.datetime.now().strftime("%m")) + int(datetime.datetime.now().strftime("%d")[0]))
    cookieKey = int(
        int(datetime.datetime.now().strftime("%y")) * random.random() * 100 * random.random() * 100 * 1000000000000)
    return cookieKey


# database Commands
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


# simple Method to evaluate the cookie
def checkCookie(cookie):
    try:
        cookie = base64.b64decode(cookie)
        if re.match(cookieCheck, cookie.decode('utf-8')):
            cookieDict = eval(cookie)
            username = saveString(cookieDict["user"])
            query = query_db("SELECT * FROM USER WHERE username = ?", [username], one=True)
            if query:
                if cookieDict["web"] == str(generateKey()):
                    return (True, username)
        return (False, None)
    except:
        return (False, None)


def checkDirAccses(username, dir):
    try:
        dir = saveString(dir)
        query = query_db(f'SELECT * FROM ACCESS WHERE user = "{username}" AND folder = "{dir}"', one=True)
        return (query['folder'], query['perm'])
    except:
        return (None, None)


def saveString(string):
    string = string.replace('\'', "")
    string = string.replace('\"', "")
    return string


# create account Method
def createAccount(username, password):
    username = saveString(username)
    password = saveString(password)
    password = hashlib.md5(password.encode()).hexdigest()
    try:
        if not query_db(f"SELECT * FROM USER WHERE username = '{username}'"):
            db = get_db()
            db.cursor().execute(f'INSERT INTO USER (username, password) VALUES ("{username}", "{password}")')
            db.cursor().execute(f'INSERT INTO ACCESS (user, folder, perm) VALUES ("{username}", "{username}", "F")')
            db.commit()
            mkdir(app.config["UPLOAD_FOLDER"] + "/" + username)
        else:
            return 1
    except Exception as e:
        print(e)
        return 0


# account managment
@app.route("/")
def main():
    cookie = request.cookies.get('auth')
    if cookie:
        return redirect('/folder')

    return render_template("Login.html")


@app.route('/signup')
def signup():
    return render_template("SignUp.html", err="")


@app.route('/signupper', methods=["POST", "GET"])
def signupper():
    user = request.form["user"]
    pass1 = request.form["pass"]
    pass2 = request.form["pass2"]
    if pass1 == pass2:
        tmp = createAccount(user, pass1)
        if tmp == 0:
            return render_template("SignUp.html", err="Something went wrong while creating an Account")
        elif tmp == 1:
            return render_template("SignUp.html", err="Username already exists")
        else:
            return redirect('/')
    else:
        return render_template("SignUp.html", err="Passwords don't match up!")


@app.route('/invite/<path:dir>')
def invite(dir):
    cookie = request.cookies.get('auth')
    if cookie:
        perm = checkCookie(cookie)
        access = checkDirAccses(perm[1], dir)
        if perm[0] and access[0] == dir and access[1] == "F":
            return render_template('invite.html', dir=dir)
    return redirect('/missingCookie')


@app.route('/inviter/<path:dir>', methods=["POST", "GET"])
def inviter(dir):
    if request.method == 'POST':
        username = saveString(request.form["user"])
        permAcces = request.form["perm"]
        cookie = request.cookies.get('auth')
        if cookie:
            perm = checkCookie(cookie)
            access = checkDirAccses(perm[1], dir)
            if perm[0] and access[0] == dir and access[1] == "F":
                query = query_db(f'SELECT * FROM USER WHERE username="{username}"')
                query2 = query_db(f'SELECT * FROM ACCESS WHERE user="{username}" AND folder="{dir}"')
                if query and not query2:
                    db = get_db()
                    db.cursor().execute(f'INSERT INTO INVITES (user, folder, perm, inviter) VALUES ("{username}", "{dir}", "{permAcces}", "{perm[1]}")')
                    db.commit()
                    return redirect(f'/download/{dir}')
                else:
                    return "User already invited"
    return redirect('/missingCookie')


@app.route('/invites')
def invites():
    cookie = request.cookies.get('auth')
    if cookie:
        perm = checkCookie(cookie)
        if perm[0]:
            query = query_db(f'SELECT * FROM INVITES WHERE user="{perm[1]}"')
            val = []
            for row in query:
                val.append(row)
            return render_template('invites.html', data=val)
    return redirect('/missingCookie')


@app.route('/invites/accept/<path:inv>')
def inv_acc(inv):
    cookie = request.cookies.get('auth')
    if cookie:
        perm = checkCookie(cookie)
        inv = saveString(inv)
        if perm[0]:
            query = query_db(f'SELECT * FROM INVITES WHERE user="{perm[1]}" AND folder="{inv}"', one=True)
            if query:
                db = get_db()
                db.cursor().execute(
                    f'INSERT INTO ACCESS (user, folder, perm) VALUES ("{perm[1]}", "{inv}", "{query["perm"]}")')
                db.cursor().execute(f'DELETE FROM INVITES WHERE user="{perm[1]}" AND folder="{inv}"')
                db.commit()
                return redirect('/folder')
    return redirect('/missingCookie')


@app.route('/invites/decline/<path:inv>')
def inv_rej(inv):
    cookie = request.cookies.get('auth')
    if cookie:
        perm = checkCookie(cookie)
        inv = saveString(inv)
        if perm[0]:
            if query_db(f'SELECT * FROM INVITES WHERE user="{perm[1]}" AND folder="{inv}"'):
                db = get_db()
                db.cursor().execute(f'DELETE FROM INVITES WHERE user="{perm[1]}" AND folder="{inv}"')
                db.commit()
                return redirect('/folder')
    return redirect('/missingCookie')


@app.route('/folder')
def folder():
    cookie = request.cookies.get('auth')
    if cookie:
        perm = checkCookie(cookie)
        if perm[0]:
            val = []
            query = query_db(f'SELECT * from ACCESS WHERE user = "{perm[1]}"')
            for row in query:
                val.append(row["folder"])
            return render_template('folders.html', files=val)
    return redirect('/missingCookie')


# download managment
@app.route('/download/<path:dir>')
def download(dir):
    cookie = request.cookies.get('auth')
    if cookie:
        perm = checkCookie(cookie)
        access = checkDirAccses(perm[1], dir)
        if perm[0] and access[0] == dir and not access[1] == "W":
            onlyfiles = [f for f in listdir(app.config["UPLOAD_FOLDER"] + "/" + dir) if
                         isfile(join(app.config["UPLOAD_FOLDER"] + "/" + dir, f))]
            return render_template("test_temp.html", files=onlyfiles, dir=dir)
    return redirect('/missingCookie')


@app.route('/downloader/<path:dir>/<path:filename>')
def downloader(dir, filename):
    cookie = request.cookies.get('auth')
    if cookie:
        perm = checkCookie(cookie)
        access = checkDirAccses(perm[1], dir)
        if perm[0] and access[0] == dir and not access[1] == "W":
            return send_from_directory(app.config["UPLOAD_FOLDER"] + "/" + dir, filename, as_attachment=True)
    return redirect('/missingCookie')


@app.route('/delete/<path:dir>/<path:filename>')
def delete(dir, filename):
    cookie = request.cookies.get('auth')
    if cookie:
        perm = checkCookie(cookie)
        access = checkDirAccses(perm[1], dir)
        if perm[0] and access[0] == dir and not access[1] == "R":
            remove(app.config["UPLOAD_FOLDER"] + '/' + dir + '/' + filename)
            return redirect('/download/' + dir)
    return redirect('/missingCookie')


# upload managment
@app.route('/upload/<path:dir>', methods=['GET', 'POST'])
def uploader(dir):
    cookie = request.cookies.get('auth')
    if cookie:
        perm = checkCookie(cookie)
        access = checkDirAccses(perm[1], dir)
        if perm[0] and access[0] == dir and not access[1] == "R":
            if request.method == 'POST':
                f = request.files['file']
                f.save(app.config["UPLOAD_FOLDER"] + '/' + dir + '/' + secure_filename(f.filename))
            return render_template("uploader.html", dir=dir)
    return redirect('/missingCookie')


# cookie managment
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
                resp = redirect('/folder')
                resp.set_cookie('auth',
                                base64.b64encode(f"{{'user': '{username}', 'web': '{generateKey()}'}}".encode()))
                return resp
    return redirect('/')


@app.route('/removecookie')
def removecookie():
    resp = make_response(redirect('/'))
    resp.set_cookie('auth', "", expires=0)
    return resp


# 403
@app.route('/missingCookie')
def missingCookie():
    return render_template('UwUNoCookie.html')
