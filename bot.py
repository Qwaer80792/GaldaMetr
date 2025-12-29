import os
import random
import time
import threading
from datetime import datetime
from flask import Flask, render_template_string
import telebot
from models import db, User, Cooldown

# ===== НАСТРОЙКИ =====
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PORT = 5000

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Galda Bot</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; background: #f0f0f0; }
            .container { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
            h1 { color: #4a00e0; }
            .status { color: green; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 Galda Bot</h1>
            <p class="status">✅ БОТ АКТИВЕН (PostgreSQL)</p>
            <p>Telegram бот для измерения галды</p>
            <p>Работает на Replit.com</p>
        </div>
    </body>
    </html>
    """)

# ===== ТЕЛЕГРАМ БОТ =====
bot = telebot.TeleBot(TOKEN)

def ensure_user_exists(user_id, username=None):
    user_id_str = str(user_id)
    with app.app_context():
        user = db.session.get(User, user_id_str)
        if not user:
            user = User(id=user_id_str, username=username or f"user_{user_id_str}")
            db.session.add(user)
            db.session.commit()
            return True
        elif username and user.username != username:
            user.username = username
            db.session.commit()
    return False

def check_cooldown(user_id, cooldown_time=1800):
    user_id_str = str(user_id)
    current_time = time.time()
    with app.app_context():
        cd = db.session.get(Cooldown, user_id_str)
        if cd:
            elapsed = current_time - cd.last_used
            if elapsed < cooldown_time:
                remaining = cooldown_time - elapsed
                return False, f"⏳ Попробуй через {int(remaining // 3600)}ч {int((remaining % 3600) // 60)}мин."
            cd.last_used = current_time
        else:
            cd = Cooldown(user_id=user_id_str, last_used=current_time)
            db.session.add(cd)
        db.session.commit()
    return True, None

@bot.message_handler(commands=["start"])
def send_start_message(message):
    ensure_user_exists(message.from_user.id, message.from_user.first_name)
    bot.reply_to(message, "👋 Привет! Я бот для измерения галды.\n/galda - измерить\n/my_stat - стата\n/all_stat - топ")

@bot.message_handler(commands=["galda", "galdafon", "galdishechka", "galdazaraza"])
def send_random_message(message):
    user_id = message.from_user.id
    ensure_user_exists(user_id, message.from_user.first_name)
    can_proceed, error_msg = check_cooldown(user_id)
    if not can_proceed:
        bot.reply_to(message, error_msg or "⏳ Попробуй позже.")
        return
    
    change = random.randint(-15, 15)
    with app.app_context():
        user = db.session.get(User, str(user_id))
        if user:
            user.galda_size = max(1, user.galda_size + change)
            db.session.commit()
            response = f"🎯 Твоя галда {'выросла' if change > 0 else 'уменьшилась'} на {abs(change)}!\n📏 Теперь она {user.galda_size} анечек!"
            bot.reply_to(message, response)

@bot.message_handler(commands=["my_stat"])
def show_my_stat(message):
    with app.app_context():
        user = db.session.get(User, str(message.from_user.id))
        if user:
            bot.reply_to(message, f"📊 Твоя стата:\n📏 Галда: {user.galda_size}\n🍪 Проиграно: {user.cookies_lost}")

@bot.message_handler(commands=["all_stat"])
def show_all_stat(message):
    with app.app_context():
        top_users = db.session.query(User).order_by(User.galda_size.desc()).limit(10).all()
        text = "🏆 ТОП ГАЛДУНОВ:\n"
        for i, u in enumerate(top_users, 1):
            text += f"{i}. {u.username}: {u.galda_size}\n"
        bot.reply_to(message, text)

def run_bot():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT), daemon=True).start()
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
