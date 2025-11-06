from flask import Flask, request, jsonify
import psycopg2
import random
import datetime
import os

app = Flask(__name__)

# CORS headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Данные Supabase - ДОЛЖНЫ БЫТЬ ТАКИЕ ЖЕ КАК В bot.py!
DB_CONFIG = {
    "host": "db.ohosgqpsngnzgmexigtc.supabase.co",
    "database": "postgres",
    "user": "postgres", 
    "password": "Detroit2033Apex2077",
    "port": "5432"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# Конфигурация игровых режимов
CASE_CONFIG = {
    'name': 'Gift Box',
    'price': 25,
    'items': [
        {'name': '🧸 Мишка', 'price': 15, 'chance': 35},
        {'name': '💝 Сердечко', 'price': 15, 'chance': 35},
        {'name': '🌹 Роза', 'price': 25, 'chance': 7.5},
        {'name': '🎁 Подарок', 'price': 25, 'chance': 7.5},
        {'name': '🚀 Ракета', 'price': 50, 'chance': 5},
        {'name': '🍾 Шампанское', 'price': 50, 'chance': 5},
        {'name': '🏆 Кубок', 'price': 100, 'chance': 2.5},
        {'name': '💍 Кольцо', 'price': 100, 'chance': 2.5}
    ]
}

ROULETTE_CONFIG = {
    'name': 'Ghost Roulette',
    'price': 50,
    'items': [
        {'name': '🧸 Мишка', 'price': 15, 'chance': 34.5},
        {'name': '💝 Сердечко', 'price': 15, 'chance': 34.5},
        {'name': '🌹 Роза', 'price': 25, 'chance': 7.5},
        {'name': '🎁 Подарок', 'price': 25, 'chance': 7.5},
        {'name': '🚀 Ракета', 'price': 50, 'chance': 5},
        {'name': '🍾 Шампанское', 'price': 50, 'chance': 5},
        {'name': '🏆 Кубок', 'price': 100, 'chance': 2.5},
        {'name': '💍 Кольцо', 'price': 100, 'chance': 2.5},
        {'name': '❔ Random NFT Gift', 'price': 500, 'chance': 1}
    ]
}

def get_user_data(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_user_balance(user_id, amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = balance + %s WHERE user_id = %s', (amount, user_id))
    conn.commit()
    conn.close()

def get_user_inventory(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inventory WHERE user_id = %s', (user_id,))
    inventory = cursor.fetchall()
    conn.close()
    return inventory

# API endpoints
@app.route('/api/user/<int:user_id>')
def get_user(user_id):
    user = get_user_data(user_id)
    if user:
        return jsonify({
            'user_id': user[0],
            'username': user[1],
            'balance': user[2]
        })
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/inventory/<int:user_id>')
def get_inventory(user_id):
    inventory = get_user_inventory(user_id)
    items = []
    for item in inventory:
        items.append({
            'id': item[0],
            'name': item[2],
            'price': item[3]
        })
    return jsonify(items)

@app.route('/api/open-case', methods=['POST'])
def open_case():
    data = request.json
    user_id = data.get('user_id')
    
    user = get_user_data(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user[2] < CASE_CONFIG['price']:
        return jsonify({'error': 'Недостаточно звезд'}), 400
    
    # Случайный выбор предмета по шансам
    rand = random.random() * 100
    current_chance = 0
    selected_item = None
    
    for item in CASE_CONFIG['items']:
        current_chance += item['chance']
        if rand <= current_chance:
            selected_item = item
            break
    
    if selected_item:
        # Обновляем баланс и добавляем в инвентарь
        update_user_balance(user_id, -CASE_CONFIG['price'])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO inventory (user_id, item_name, item_price) VALUES (%s, %s, %s)',
                    (user_id, selected_item['name'], selected_item['price']))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'item': selected_item['name'],
            'price': selected_item['price'],
            'new_balance': user[2] - CASE_CONFIG['price']
        })
    
    return jsonify({'error': 'Ошибка при открытии кейса'}), 500

@app.route('/api/spin-roulette', methods=['POST'])
def spin_roulette():
    data = request.json
    user_id = data.get('user_id')
    
    user = get_user_data(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user[2] < ROULETTE_CONFIG['price']:
        return jsonify({'error': 'Недостаточно звезд'}), 400
    
    # Случайный выбор предмета по шансам
    rand = random.random() * 100
    current_chance = 0
    selected_item = None
    
    for item in ROULETTE_CONFIG['items']:
        current_chance += item['chance']
        if rand <= current_chance:
            selected_item = item
            break
    
    if selected_item:
        # Обновляем баланс и добавляем в инвентарь
        update_user_balance(user_id, -ROULETTE_CONFIG['price'])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO inventory (user_id, item_name, item_price) VALUES (%s, %s, %s)',
                    (user_id, selected_item['name'], selected_item['price']))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'item': selected_item['name'],
            'price': selected_item['price'],
            'new_balance': user[2] - ROULETTE_CONFIG['price']
        })
    
    return jsonify({'error': 'Ошибка при вращении рулетки'}), 500

@app.route('/api/claim-bonus', methods=['POST'])
def claim_bonus():
    data = request.json
    user_id = data.get('user_id')
    
    user = get_user_data(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Проверяем время последнего бонуса
    last_bonus = user[3]
    if last_bonus:
        last_bonus = datetime.datetime.fromisoformat(last_bonus)
        if (datetime.datetime.now() - last_bonus).total_seconds() < 24 * 3600:
            return jsonify({'error': 'Бонус можно получать раз в 24 часа'}), 400
    
    # Начисляем бонус (1-5 звезд)
    bonus = random.randint(1, 5)
    update_user_balance(user_id, bonus)
    
    # Обновляем время последнего бонуса
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET last_bonus = %s WHERE user_id = %s', 
                (datetime.datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'bonus': bonus,
        'new_balance': user[2] + bonus
    })

@app.route('/api/sell-item', methods=['POST'])
def sell_item():
    data = request.json
    user_id = data.get('user_id')
    item_id = data.get('item_id')
    
    # Получаем информацию о предмете
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inventory WHERE id = %s AND user_id = %s', 
                       (item_id, user_id))
    item = cursor.fetchone()
    
    if not item:
        return jsonify({'error': 'Предмет не найден'}), 404
    
    # Вычисляем цену продажи (цена * 1.2)
    sell_price = int(item[3] * 1.2)
    
    # Удаляем предмет и начисляем звезды
    cursor.execute('DELETE FROM inventory WHERE id = %s', (item_id,))
    cursor.execute('UPDATE users SET balance = balance + %s WHERE user_id = %s', 
                (sell_price, user_id))
    conn.commit()
    
    cursor.execute('SELECT balance FROM users WHERE user_id = %s', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    return jsonify({
        'success': True,
        'sold_price': sell_price,
        'new_balance': user[0]
    })

@app.route('/api/withdraw-item', methods=['POST'])
def withdraw_item():
    data = request.json
    user_id = data.get('user_id')
    item_id = data.get('item_id')
    
    # Получаем информацию о предмете
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inventory WHERE id = %s AND user_id = %s', 
                       (item_id, user_id))
    item = cursor.fetchone()
    cursor.execute('SELECT username FROM users WHERE user_id = %s', (user_id,))
    user = cursor.fetchone()
    
    if not item:
        return jsonify({'error': 'Предмет не найден'}), 404
    
    # Создаем заявку на вывод
    cursor.execute('INSERT INTO withdrawal_requests (user_id, username, item_name, item_price) VALUES (%s, %s, %s, %s)',
                (user_id, user[0], item[2], item[3]))
    
    # Удаляем предмет из инвентаря
    cursor.execute('DELETE FROM inventory WHERE id = %s', (item_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)