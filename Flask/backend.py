from flask import Flask
from flask import render_template, request
from flask import send_file, send_from_directory

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "public"

@app.route('/')
def hello_world():
    return render_template("login.html")

@app.route('/download')
def download():
    path = "./public/downloadable.txt"
    return send_file(path, as_attachment=True)

@app.route('/send_dir/<path:filename>')
def download_from_dir(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

@app.route('/login', methods=["POST","GET"])
def login(): 
    name = ""
    if request.method == "POST":
        name = request.form[name]
        print(name)