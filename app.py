import os
import sqlite3
import urllib.parse as urlparse
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'ozon_secret_key'

# Функция для получения подключения к нужной базе данных
def get_db_connection():
    # Проверяем, есть ли ссылка на PostgreSQL от Render
    db_url = os.environ.get('DATABASE_URL')
    
    if db_url:
        # Если мы на сервере, подключаемся к PostgreSQL
        import psycopg2
        from psycopg2.extras import DictCursor
        
        # Исправляем схему URL, если требуется для psycopg2
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
        conn = psycopg2.connect(db_url, cursor_factory=DictCursor)
        return conn
    else:
        # Если мы запускаем на компьютере, используем SQLite
        conn = sqlite3.connect('users.db')
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Синтаксис создания таблицы для обеих БД
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # Для PostgreSQL
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                balance REAL DEFAULT 500.0
            )
        ''')
    else:
        # Для SQLite
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                balance REAL DEFAULT 500.0
            )
        ''')
        
    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if os.environ.get('DATABASE_URL'):
            cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        else:
            cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
            
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Неверное имя пользователя или пароль!', 'error')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if os.environ.get('DATABASE_URL'):
                cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, password))
            else:
                cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
                
            conn.commit()
            conn.close()
            flash('Регистрация успешна! Войдите в аккаунт.', 'success')
            return redirect(url_for('login'))
        except Exception:
            flash('Пользователь с таким именем уже существует или произошла ошибка!', 'error')
            return redirect(url_for('register'))
            
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        username = session['user']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if os.environ.get('DATABASE_URL'):
            cursor.execute('SELECT balance FROM users WHERE username = %s', (username,))
        else:
            cursor.execute('SELECT balance FROM users WHERE username = ?', (username,))
            
        row = cursor.fetchone()
        balance = row['balance'] if row else 0.0
        conn.close()
        
        products = [
            {"id": 1, "name": "Беспроводные наушники OzonPods", "price": 350.0, "img": "🎧"},
            {"id": 2, "name": "Стильный худи Ozon Over-size", "price": 600.0, "img": "🧥"},
            {"id": 3, "name": "Умная бутылка для воды SmartBottle", "price": 250.0, "img": "🍼"},
            {"id": 4, "name": "Фитнес-браслет Ozon Band 7", "price": 450.0, "img": "⌚"},
            {"id": 5, "name": "Механическая клавиатура Clicky Click", "price": 490.0, "img": "⌨️"},
            {"id": 6, "name": "Энергетический батончик Ozon Energy", "price": 80.0, "img": "🍫"},
            {"id": 7, "name": "Игровая компьютерная мышь RGB", "price": 190.0, "img": "🖱️"},
            {"id": 8, "name": "Рюкзак городской водонепроницаемый", "price": 420.0, "img": "🎒"},
            {"id": 9, "name": "Коврик для мыши игровой XL", "price": 120.0, "img": "🗺️"},
            {"id": 10, "name": "Термокружка для кофе стальная", "price": 280.0, "img": "☕"},
            {"id": 11, "name": "Настольная лампа с беспроводной зарядкой", "price": 480.0, "img": "💡"},
            {"id": 12, "name": "Мягкая подушка-игрушка Гусь", "price": 390.0, "img": "🦢"}
        ]
        
        return render_template('index.html', username=username, balance=balance, products=products)
    return redirect(url_for('login'))

@app.route('/buy/<int:product_id>/<float:price>')
def buy_product(product_id, price):
    if 'user' in session:
        username = session['user']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if os.environ.get('DATABASE_URL'):
            cursor.execute('SELECT balance FROM users WHERE username = %s', (username,))
        else:
            cursor.execute('SELECT balance FROM users WHERE username = ?', (username,))
            
        row = cursor.fetchone()
        current_balance = row['balance'] if row else 0.0
        
        if current_balance >= price:
            new_balance = current_balance - price
            if os.environ.get('DATABASE_URL'):
                cursor.execute('UPDATE users SET balance = %s WHERE username = %s', (new_balance, username))
            else:
                cursor.execute('UPDATE users SET balance = ? WHERE username = ?', (new_balance, username))
            conn.commit()
            flash(f'Успешная покупка! Списано {price} руб.', 'success')
        else:
            flash('Недостаточно средств на балансе Ozon Счёта!', 'error')
            
        conn.close()
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/add_money')
def add_money():
    if 'user' in session:
        username = session['user']
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if os.environ.get('DATABASE_URL'):
            cursor.execute('UPDATE users SET balance = balance + 500 WHERE username = %s', (username,))
        else:
            cursor.execute('UPDATE users SET balance = balance + 500 WHERE username = ?', (username,))
            
        conn.commit()
        conn.close()
        flash('Баланс пополнен на 500 руб.!', 'success')
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

