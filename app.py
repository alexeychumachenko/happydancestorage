from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

import requests
import os
import string

BOT_TOKEN = '8204513349:AAFzq5YLLbVeWQaAM5RA8Nf2F9nUscP8O3c'
CHANNEL_ID = '-1003107881093'

app = Flask(__name__)
app.secret_key = 'ae334a872681abbfad0326f883838c50aa2168923589462de1ebe99d0fe6a005'

app.config.from_pyfile('config.py')

mysql = MySQL(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id_, username, password, first_name, last_name, user_role):
        self.id = id_
        self.username = username
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.user_role = user_role
        
class File(UserMixin):
    def __init__(self, file_id, file_name, file_title, file_description, file_subject, file_supervisor_id, user_id, note, category_id, upload_date, release_year):
        self.file_id = file_id
        self.file_name = file_name
        self.file_title = file_title
        self.file_description = file_description
        self.file_subject = file_subject
        self.file_supervisor_id = file_supervisor_id
        self.user_id = user_id
        self.note = note
        self.category_id = category_id
        self.upload_date = upload_date
        self.release_year = release_year
        
class Dialog(UserMixin):
    def __init__(self, dialog_id, user_id_1, user_id_2):
        self.dialog_id = dialog_id
        self.user_id_1 = user_id_1
        self.user_id_2 = user_id_2
        
class Message(UserMixin):
    def __init__(self, message_id, caption, file_id, dialog_id, send_date):
        self.message_id = message_id
        self.caption = caption
        self.file_id = file_id
        self.dialogId = dialogId
        self.send_date = send_date
        
class Category(UserMixin):
    def __init__(self, category_id, category_name):
        self.category_id = category_id
        self.category_name = category_name

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, password, first_name, last_name, user_role FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    if user:
        return User(user[0], user[1], user[2], user[3], user[4], user[5])
    return None
    '''
@app.route('/', methods=['GET', 'POST'])
def index2():
    return f'LOGIN'
    '''
    
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    return render_template('index.html', current_user_account = current_user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        first_name = request.form['firstname']
        last_name = request.form['lastname']
        role = request.form['role']
        
        if role == 'Студент':
            role = 'student'
        elif role == 'Преподаватель':
            role = 'teacher'
        
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            flash("Пользователь с таким именем уже существует", "danger")
            cur.close()
            return redirect(url_for('register'))

        cur.execute("INSERT INTO users (username, password, first_name, last_name, user_role) VALUES (%s, %s, %s, %s, %s)", (username, hashed_pw, first_name, last_name, role))
        mysql.connection.commit()
        cur.close()

        flash("Регистрация прошла успешно!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.check_password_hash(user[2], password):
            user_obj = User(user[0], user[1], user[2], user[3], user[4], user[5])
            login_user(user_obj)
            flash("Вы вошли в систему", "success")
            return redirect(url_for('index'))
        else:
            flash("Неверное имя пользователя или пароль", "danger")

    return render_template('login.html')

@app.route('/user')
@login_required
def profile():
    id = request.args.get('id', default = current_user.id, type = int)
    show = request.args.get('show', default = 'files', type = string)
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (id,))
    user = cur.fetchone()
    cur.execute("SELECT * FROM Files WHERE user_id = %s", (id,))
    rows = cur.fetchall() 
    cur.close()
    
    profile = User(user[0], user[1], user[2], user[3], user[4], user[5])
    
    if user:
        return render_template('profile.html', current_profile = profile, current_user_account = current_user, files = rows, show_title = show)
    #    return render_template('profile.html', fn = profile.first_name, ln = profile.last_name, pr_id = profile.id, cur_id = current_user.id, files = rows, username = current_user.first_name)
    else:
        abort(404)
    # return f"Привет, {current_user.username}!"
    
@app.route('/user/<string:loggin>')
@login_required
def profile2(loggin):
    show = request.args.get('show', default = 'files', type = string)
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", (loggin,))
    user = cur.fetchone()
    profile = User(user[0], user[1], user[2], user[3], user[4], user[5])
    
    cur.execute("SELECT * FROM Files WHERE user_id = %s", (profile.id,))
    rows = cur.fetchall() 

    cur.close()
    
    if profile:
        return render_template('profile.html', current_profile = profile, current_user_account = current_user, files = rows, show_title = show)
    else:
        abort(404)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из системы", "info")
    return redirect(url_for('login'))

def send_file_to_channel(file_path, caption=None):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendDocument'
    with open(file_path, 'rb') as f:
        files = {'document': f}
        data = {'chat_id': CHANNEL_ID}
        if caption:
            data['caption'] = caption
        
        response = requests.post(url, files=files, data=data)
        return response.json()

'''
@app.route('/upload', methods=['POST'])
def upload_file():
    # ожидаем файл под ключом 'file' в запросе
    if 'file' not in request.files:
        return {'error': 'File not found'}, 400

    file = request.files['file']
    file.save(file.filename)  # временно сохраняем файл

    result = send_file_to_channel(file.filename, caption='Загруженный файл')
    
    # опционально - удалить файл после загрузки
    import os
    os.remove(file.filename)

    return result
'''
    
@app.route('/upload', methods=['POST'])
def upload():
    title = request.form['title']
    description = request.form['description']
    subject = request.form['subject']
    supervisor = request.form['supervisor']
    releaseYear = request.form['releaseYear']
    
    fio = supervisor.split()

    if 'file' not in request.files:
        return {'error': 'Файл не найден'}, 400
    file = request.files['file']
    if file.filename == '':
        return {'error': 'Имя файла пустое'}, 400
    file.save(f'{file.filename}')
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM Users WHERE user_role='teacher' AND first_name = %s AND last_name = %s", (fio[0], fio[1], ))
    supervisor_id = cur.fetchone()
    
    cur.execute("INSERT INTO Files (file_name, file_title, file_description, file_subject, file_supervisor_id, user_id, note, category_id, upload_date, release_year) VALUES (%s, %s, %s, %s, %s, %s, 'saved', 1, NOW(), %s)", (file.filename, title, description, subject, supervisor_id, current_user.id, releaseYear))
    
    cur.execute("SELECT * FROM Files WHERE file_name = %s AND user_id = %s", (file.filename, current_user.id,))
    f = cur.fetchone();
    cur_file = File(f[0], f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8], f[9], f[10]);
    
    result = send_file_to_channel(file.filename, caption = cur_file.file_id)
    
    mysql.connection.commit()
    cur.close()
    
    # опционально - удалить файл после загрузки
    os.remove(file.filename)

    return redirect(url_for('profile'))
    
    
@app.route('/work')
def work():
    id = request.args.get('id', default = 1, type = int)
    
    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM Files WHERE file_id = %s", (id,))
    
    f = cur.fetchone();
    cur_file = File(f[0], f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8], f[9], f[10]);
    
    cur.execute("SELECT * FROM users WHERE id = %s", (cur_file.user_id,))
    user = cur.fetchone()
    
    profile = User(user[0], user[1], user[2], user[3], user[4], user[5])
    
    mysql.connection.commit()
    cur.close()

    return render_template('work.html', current_file = cur_file, current_profile = profile, current_user_account = current_user)
    
@app.route('/im')
@login_required
def im():
    dialogId = request.args.get('dialogId', default = -1, type = int)
    
    cur = mysql.connection.cursor()

    cur.execute("SELECT dialog_id, user_id_1, user_id_2, first_name, last_name FROM Dialogs INNER JOIN Users ON user_id_1 = Users.id OR user_id_2 = Users.id WHERE (user_id_1 = %s OR user_id_2 = %s) AND Users.username != %s", (current_user.id, current_user.id, current_user.username,))
    dia = cur.fetchall()
  
    cur.execute("SELECT message_id, caption, file_id, Messages.dialog_id, send_date, user_from_id, Dialogs.dialog_id, user_id_1, user_id_2, id, username, password, first_name, last_name, user_role FROM Messages INNER JOIN Dialogs ON Messages.dialog_id = Dialogs.dialog_id INNER JOIN Users ON user_id_1 = Users.id OR user_id_2 = Users.id WHERE Messages.dialog_id = %s AND ((user_id_1 = user_from_id OR user_id_2 = user_from_id)) AND Users.id = user_from_id ORDER BY Messages.send_date", (dialogId,))
    msg = cur.fetchall()
  
    cur.close()
    
    return render_template('im.html', current_user_account = current_user, dialogs = dia, messages = msg, diaId = dialogId)
    
@app.route('/sendMessage', methods=['POST'])
@login_required
def sendMessage():
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO Messages (caption, file_id, dialog_id, send_date, user_from_id) Values(%s, 3, %s, NOW(), %s);", (caption, dialogId, current_user.id))
    cur.close()
    return redirect('/im')
    
@app.route('/settings')
@login_required
def profileSettings():
    return render_template('settings.html', current_user_account = current_user)
    

@app.route('/uploadFile')
def upload_file_html():
    cur = mysql.connection.cursor()

    cur.execute("SELECT first_name, last_name FROM Users WHERE user_role = 'teacher'")
    all_teachers = cur.fetchall()
    return render_template('uploadFile.html', teachers = all_teachers)


@app.route('/saveSettings', methods=['POST'])
def saveSettings():
    firstname = request.form['first_name']
    lastname = request.form['last_name']
    
    cur = mysql.connection.cursor()
    cur.execute("UPDATE Users SET first_name = %s, last_name = %s WHERE id = %s", (firstname, lastname, current_user.id))
    
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('profile'))

@app.errorhandler(404)
def page_not_found(error):
    return render_template('error/404.html'), 404