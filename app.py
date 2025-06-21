from flask import Flask, render_template, request, redirect, url_for, session, make_response
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'insecure_secret_key_123!'

# Инициализация БД
def init_db():
    if not os.path.exists('users.db'):
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

@app.route('/')
def home():
    return redirect(url_for('login'))

# Уязвимая регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        try:
            # Уязвимость: прямой INSERT без параметризации
            cursor.execute(f"INSERT INTO users (username, password) VALUES ('{username}', '{password}')")
            conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already exists", 400
        finally:
            conn.close()
    
    return render_template('register.html')

# Уязвимый вход с SQL-инъекциями
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        # Умышленная уязвимость: конкатенация строк
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        cursor.execute(query)
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['username'] = username
            response = make_response(redirect(url_for('welcome')))
            # Уязвимые куки
            response.set_cookie('auth_token', 'insecure_value_123', httponly=False, secure=False)
            return response
        return "Invalid credentials", 401
    
    return render_template('login.html')

# Защищенная страница
@app.route('/welcome')
def welcome():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('welcome.html', username=session['username'])

if __name__ == '__main__':
    init_db()
    # Уязвимый режим разработки
    app.run(host='0.0.0.0', port=5000, debug=True)
