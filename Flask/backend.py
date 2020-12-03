from flask import Flask
from flask import send_from_directory, request, render_template
from werkzeug.utils import secure_filename

from os import listdir
from os.path import isfile, join

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "public"

@app.route("/")
def main():
    return '<a href="downloader">Test</a>'

@app.route('/downloader')
def downloader():
    onlyfiles = [f for f in listdir(app.config["UPLOAD_FOLDER"]) if isfile(join(app.config["UPLOAD_FOLDER"], f))]
    return render_template("test_temp.html", files=onlyfiles)

@app.route('/download/<path:filename>')
def download(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

@app.route('/upload', methods=['GET', 'POST'])
def uploader():
    if request.method == 'POST':
        f = request.files['the_file']
        f.save(app.config["UPLOAD_FOLER"] + secure_filename(f.filename))
        return render_template("uploader.html")
    