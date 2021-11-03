"""Приложение на загрузку файлов."""

import json
import os

from dotenv import load_dotenv
from flask import Flask, flash, redirect, url_for, render_template, request
from flask_autoindex import AutoIndex
from flask_login import login_user, login_required, logout_user, LoginManager, current_user
from werkzeug.utils import secure_filename

load_dotenv()
app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
tokens = json.loads(os.environ.get('tokens'))
app.secret_key = os.environ.get('secret_key')
UPLOAD_FOLDER = str(os.environ.get('DIR'))
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

files_index = AutoIndex(app, browse_root=os.path.abspath(UPLOAD_FOLDER), add_url_rules=False)


class User:
    def __init__(self, id, name):
        self.name = name
        self.id = id

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def __repr__(self):
        return '<User %r>' % (self.name)


users = {}
for token in tokens:
    users.update({token: User(token, tokens[token])})


@login_manager.user_loader
def load_user(token):
    return users.get(token)


@app.route("/", methods=["GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('autoindex'))
    return render_template("login.html")


@app.route("/", methods=["POST"])
def login_post():
    token = request.form["nm"]
    user = load_user(token)
    if user:
        login_user(user)
        return redirect(url_for("autoindex"))
    else:
        return redirect(url_for("login"))


@app.route('/autoindex')
@app.route('/autoindex/<path:path>')
@login_required
def autoindex(path='.'):
    return files_index.render_autoindex(path, template='autoindex.html', endpoint='.autoindex')


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect("/autoindex")
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect("/autoindex")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect("/autoindex")
    return '''
            <!doctype html>
            <title>Загрузка нового файла</title>
            <h1>Upload new File</h1>
            <form method=post enctype=multipart/form-data>
              <input type=file name=file>
              <input type=submit value=Upload>
            </form>
            '''


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
