import os
import logging
import psycopg2
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import datetime
import random

# Настройки
BOT_TOKEN = "7781228845:AAGqMyu-zxvN9tG0dEA9jmfnkkIKobeTyRI"
ADMIN_ID = 5450857649
CHANNEL_USERNAME = "@Ghost_FluX"

# Данные Supabase - ЗАМЕНИТЕ НА СВОИ!
DB_CONFIG = {
    "host": "db.ohosgqpsngnzgmexigtc.supabase.co",
    "database": "postgres",
    "user": "postgres", 
    "password": "Detroit2033Apex2077",
    "port": "5432"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0,
            last_bonus TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            item_name TEXT,
            item_price INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS withdrawal_requests (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            username TEXT,
            item_name TEXT,
            item_price INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(user_id, username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (user_id, username) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING', 
                   (user_id, username))
    conn.commit()
    conn.close()

def update_balance(user_id, amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = balance + %s WHERE user_id = %s', (amount, user_id))
    conn.commit()
    conn.close()

def add_to_inventory(user_id, item_name, item_price):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO inventory (user_id, item_name, item_price) VALUES (%s, %s, %s)', 
                   (user_id, item_name, item_price))
    conn.commit()
    conn.close()

def get_inventory(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inventory WHERE user_id = %s', (user_id,))
    inventory = cursor.fetchall()
    conn.close()
    return inventory

def remove_from_inventory(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM inventory WHERE id = %s', (item_id,))
    conn.commit()
    conn.close()

def create_withdrawal_request(user_id, username, item_name, item_price):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO withdrawal_requests (user_id, username, item_name, item_price) VALUES (%s, %s, %s, %s)',
                   (user_id, username, item_name, item_price))
    conn.commit()
    conn.close()

def get_pending_withdrawals():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM withdrawal_requests WHERE status = %s', ('pending',))
    requests = cursor.fetchall()
    conn.close()
    return requests

def complete_withdrawal(request_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE withdrawal_requests SET status = %s WHERE id = %s', ('completed', request_id))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    conn.close()
    return count

# Команды бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    create_user(user.id, user.username)
    
    keyboard = [
        [InlineKeyboardButton("🎮 Открыть Mini App", web_app={'url': 'https://your-netlify-url.netlify.app'})],
        [InlineKeyboardButton("📢 Наш канал", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton("💬 Поддержка", url="https://t.me/KXKXKXKXKXKXKXKXKXKXK")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Добро пожаловать в *Ghost FluX Casino*\\!\n\n"
        f"🎰 *Игровые режимы:*\n"
        f"• 🎁 Кейс Gift Box \\- 25 звезд\n"
        f"• 🎡 Рулетка Ghost Roulette \\- 50 звезд\n"
        f"• 🎁 Бонусный кейс \\- Бесплатно раз в 24 часа\n\n"
        f"💫 *Начните играть прямо сейчас!*",
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Доступ запрещен!")
        return
    
    keyboard = [
        [KeyboardButton("💰 Пополнить баланс")],
        [KeyboardButton("📊 Статистика")],
        [KeyboardButton("📋 Заявки на вывод")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "👑 *Админ-панель Ghost FluX*\n\n"
        "Выберите действие:",
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )

async def handle_admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    text = update.message.text
    
    if text == "💰 Пополнить баланс":
        await update.message.reply_text(
            "Введите данные для пополнения в формате:\n"
            "`@username количество_звезд`\n\n"
            "Пример: `@username 100`",
            parse_mode='Markdown'
        )
        context.user_data['awaiting_deposit'] = True
        
    elif text == "📊 Статистика":
        users_count = get_all_users()
        await update.message.reply_text(f"📊 Статистика:\n👥 Пользователей: {users_count}")
        
    elif text == "📋 Заявки на вывод":
        requests = get_pending_withdrawals()
        if not requests:
            await update.message.reply_text("✅ Нет pending заявок на вывод")
            return
            
        for req in requests:
            req_id, user_id, username, item_name, item_price, status, created_at = req
            keyboard = [[InlineKeyboardButton("✅ Выдано", callback_data=f"complete_{req_id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"📦 Заявка на вывод #{req_id}\n"
                f"👤 Пользователь: @{username}\n"
                f"🎁 Подарок: {item_name}\n"
                f"💫 Цена: {item_price} звезд\n"
                f"🕐 Время: {created_at}",
                reply_markup=reply_markup
            )

async def handle_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('awaiting_deposit'):
        return
        
    text = update.message.text
    if text.startswith('@'):
        try:
            parts = text.split()
            username = parts[0][1:]  # Убираем @
            amount = int(parts[1])
            
            # Находим user_id по username
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM users WHERE username = %s', (username,))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                user_id = user[0]
                update_balance(user_id, amount)
                await update.message.reply_text(f"✅ Баланс @{username} пополнен на {amount} звезд!")
                
                # Уведомляем пользователя
                try:
                    user_data = get_user(user_id)
                    await context.bot.send_message(
                        user_id,
                        f"🎉 Ваш баланс пополнен на *{amount} звезд*\\!\n\n"
                        f"💫 Теперь у вас: *{user_data[2] + amount} звезд*\n"
                        f"🎮 Можете продолжать играть в Mini App",
                        parse_mode='MarkdownV2'
                    )
                except:
                    pass  # Пользователь не начал диалог с ботом
            else:
                await update.message.reply_text("❌ Пользователь не найден!")
                
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Неверный формат! Используйте: `@username количество`")
    
    context.user_data['awaiting_deposit'] = False

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('complete_'):
        request_id = int(query.data.split('_')[1])
        complete_withdrawal(request_id)
        await query.edit_message_text("✅ Заявка на вывод выполнена!")

# Инициализация и запуск
init_db()

# Добавляем обработчики
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("admin", admin_panel))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_actions))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_deposit))
application.add_handler(CallbackQueryHandler(button_handler))

if __name__ == '__main__':
    application.run_polling()