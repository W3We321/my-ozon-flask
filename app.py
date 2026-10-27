import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'ozon_secret_key'  # Нужен для всплывающих уведомлений flash


# Инициализация БД
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
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

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
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
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            conn.close()
            flash('Регистрация успешна! Войдите в аккаунт.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Пользователь с таким именем уже существует!', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')


# Главная страница (Маркетплейс)
# Замените только функцию dashboard в app.py (или весь app.py, если так удобнее)

@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        username = session['user']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE username = ?', (username,))
        balance = cursor.fetchone()
        conn.close()

        # Полный список из 12 крутых товаров без лишнего кода
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


# Маршрут для покупки товара
@app.route('/buy/<int:product_id>/<float:price>')
def buy_product(product_id, price):
    if 'user' in session:
        username = session['user']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        # Проверяем текущий баланс пользователя
        cursor.execute('SELECT balance FROM users WHERE username = ?', (username,))
        current_balance = cursor.fetchone()[0]

        if current_balance >= price:
            # Списываем деньги
            new_balance = current_balance - price
            cursor.execute('UPDATE users SET balance = ? WHERE username = ?', (new_balance, username))
            conn.commit()
            flash(f'Успешная покупка! Списано {price} руб.', 'success')
        else:
            flash('Недостаточно средств на балансе Ozon Счёта!', 'error')

        conn.close()
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


# Пополнение баланса
@app.route('/add_money')
def add_money():
    if 'user' in session:
        username = session['user']
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
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
