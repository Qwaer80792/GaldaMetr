import os
import random
import json
import time
from datetime import datetime
from threading import Thread
from flask import Flask
import telebot

# ===== CONFIGURATION =====
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    # Fallback to hardcoded token if environment variable is missing (not recommended for production)
    TOKEN = "8129099142:AAFIDgn3njqe3uTKV5pbJLH6Pypc8xsWuF8"

# ===== FLASK SERVER =====
app = Flask('')

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Galda Bot</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                text-align: center; 
                padding: 50px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: rgba(255,255,255,0.1);
                padding: 40px;
                border-radius: 20px;
                display: inline-block;
                backdrop-filter: blur(10px);
            }
            h1 { font-size: 3em; margin-bottom: 20px; }
            .status { 
                font-size: 1.5em; 
                color: #4ade80; 
                font-weight: bold;
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.7; }
                100% { opacity: 1; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 Galda Bot</h1>
            <div class="status">✅ БОТ АКТИВЕН</div>
            <p>Telegram бот для измерения галды</p>
            <p>Бот работает на Replit.com</p>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    return json.dumps({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "users_count": len(users)
    }), 200

def run_flask():
    app.run(host='0.0.0.0', port=5000)

# ===== TELEGRAM BOT =====
bot = telebot.TeleBot(TOKEN)
users = {}
cooldowns = {}
cookie_cooldown = 0
active_cookie_game = None

# Load/Save Database
def load_users():
    global users
    try:
        if os.path.exists('users.json'):
            with open('users.json', 'r', encoding='utf-8') as f:
                users = json.load(f)
            print(f"✅ Загружено {len(users)} пользователей")
    except Exception as e:
        print(f"⚠️ Ошибка загрузки: {e}")

def save_users():
    try:
        with open('users.json', 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Ошибка сохранения: {e}")

def auto_save():
    while True:
        time.sleep(300)
        if users:
            save_users()

# ===== HANDLERS =====
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = str(message.from_user.id)
    username = message.from_user.first_name or f"Галдун_{user_id[-4:]}"
    if message.from_user.last_name:
        username += f" {message.from_user.last_name}"

    if user_id not in users:
        users[user_id] = {
            "username": username,
            "galda_size": 50,
            "cookies_lost": 0,
            "created_at": datetime.now().isoformat()
        }
        save_users()
        welcome = f"👋 Привет, {username}!\n\n🎯 Я бот для измерения твоей галды!\n📏 Начальный размер: 50 анечек\n\n/galda - измерить галду\n/top - топ игроков"
    else:
        welcome = f"👋 С возвращением, {username}!\n📏 Твоя галда: {users[user_id]['galda_size']} анечек"
    bot.reply_to(message, welcome)

@bot.message_handler(commands=['galda'])
def galda_command(message):
    user_id = str(message.from_user.id)
    current_time = time.time()
    
    if user_id in cooldowns and current_time - cooldowns[user_id] < 1800:
        bot.reply_to(message, "⏳ Попробуй через 30 минут.")
        return

    cooldowns[user_id] = current_time
    if user_id not in users:
        users[user_id] = {"username": message.from_user.first_name, "galda_size": 50, "cookies_lost": 0, "created_at": datetime.now().isoformat()}

    change = random.randint(-15, 20)
    users[user_id]["galda_size"] = max(1, users[user_id]["galda_size"] + change)
    save_users()
    
    emoji = "📈" if change > 0 else "📉"
    bot.reply_to(message, f"{emoji} Твоя галда {'выросла' if change > 0 else 'уменьшилась'} на {abs(change)} анечек!\n🎯 Теперь она {users[user_id]['galda_size']} анечек!")

@bot.message_handler(commands=['top'])
def top_command(message):
    if not users:
        bot.reply_to(message, "😔 Пока нет игроков!")
        return
    sorted_users = sorted(users.items(), key=lambda x: x[1].get('galda_size', 0), reverse=True)
    response = "🏆 ТОП-20 ГАЛДУНОВ:\n\n"
    for i, (uid, data) in enumerate(sorted_users[:20], 1):
        response += f"{i}. {data['username']}: {data['galda_size']} анечек\n"
    bot.reply_to(message, response)

# ===== MAIN =====
def run_bot():
    print("🤖 Бот запущен...")
    while True:
        try:
            bot.infinity_polling()
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(5)

if __name__ == "__main__":
    load_users()
    Thread(target=run_flask, daemon=True).start()
    Thread(target=auto_save, daemon=True).start()
    run_bot()
