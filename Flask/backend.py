from flask import Flask
from flask import send_from_directory, request, render_template, make_response, redirect
from werkzeug.utils import secure_filename

from os import listdir
from os.path import isfile, join

app = Flask(__name__)
app.config["SECRET_KEY"] = "KHC2zY6tCH3ppS4BapA4bWFTrykm0eSJ"
app.config["UPLOAD_FOLDER"] = "public"

@app.route("/",  methods = ['POST', 'GET'])
def main():
    if request.cookies.get('auth') == 'TGVvSXN0RWluRHJlY2tzc2Fja1VuZEthbm5IaWVyTmljaHRSZWlu':
        return redirect('/downloader')
    else:
        return render_template("Login.html")


@app.route('/setcookie', methods=['POST', 'GET'])
def setcookie():
    if request.method == 'POST':
        if request.form['user'] == 'admin':
            if request.form['pass'] == 'FlaskRulz':
                resp = redirect('/downloader')
                resp.set_cookie('auth', 'TGVvSXN0RWluRHJlY2tzc2Fja1VuZEthbm5IaWVyTmljaHRSZWlu')
                return resp
    return redirect('/')

@app.route('/downloader')
def downloader():
    if request.cookies.get('auth') == 'TGVvSXN0RWluRHJlY2tzc2Fja1VuZEthbm5IaWVyTmljaHRSZWlu':
        onlyfiles = [f for f in listdir(app.config["UPLOAD_FOLDER"]) if isfile(join(app.config["UPLOAD_FOLDER"], f))]
        return render_template("test_temp.html", files=onlyfiles)
    return redirect('/', 403)

@app.route('/download/<path:filename>')
def download(filename):
    if request.cookies.get('auth') == 'TGVvSXN0RWluRHJlY2tzc2Fja1VuZEthbm5IaWVyTmljaHRSZWlu':
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)
    return redirect('/', 403)

@app.route('/upload', methods=['GET', 'POST'])
def uploader():
    if request.cookies.get('auth') == 'TGVvSXN0RWluRHJlY2tzc2Fja1VuZEthbm5IaWVyTmljaHRSZWlu':
        if request.method == 'POST':
            f = request.files['file']
            f.save(app.config["UPLOAD_FOLDER"] + '/' + secure_filename(f.filename))
        return render_template("uploader.html")
    return redirect('/', 403)
