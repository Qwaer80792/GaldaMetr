import os
import random
import json
import time
import threading
from datetime import datetime
from flask import Flask, render_template_string
import telebot

# ===== НАСТРОЙКИ =====
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8129099142:AAFIDgn3njqe3uTKV5pbJLH6Pypc8xsWuF8")
PORT = 5000

# ===== FLASK СЕРВЕР =====
app = Flask(__name__)

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
            <p class="status">✅ БОТ АКТИВЕН</p>
            <p>Telegram бот для измерения галды</p>
            <p>Работает на Replit.com</p>
        </div>
    </body>
    </html>
    """)

@app.route('/health')
def health():
    return {"status": "ok", "time": datetime.now().isoformat()}

def run_web():
    app.run(host='0.0.0.0', port=PORT)

# ===== ТЕЛЕГРАМ БОТ =====
bot = telebot.TeleBot(TOKEN)

# ===== БАЗА ДАННЫХ =====
USERS_FILE = 'users.json'
COOLDOWN_FILE = 'cooldowns.json'

def load_data(filename, default={}):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default

def save_data(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

users = load_data(USERS_FILE)
cooldowns = load_data(COOLDOWN_FILE)
cookie_cooldown = load_data('cookie_cd.json', {}).get('time', 0)
active_game = None

# Автосохранение
def auto_save():
    while True:
        time.sleep(300)
        save_data(USERS_FILE, users)
        save_data(COOLDOWN_FILE, cooldowns)

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
def ensure_user_exists(user_id, username=None):
    if user_id not in users:
        users[user_id] = {
            "username": username or f"user_{user_id}",
            "galda_size": 50,
            "cookies_lost": 0,
            "created_at": datetime.now().isoformat()
        }
        save_data(USERS_FILE, users)
        return True
    elif username and users[user_id].get("username") != username:
        users[user_id]["username"] = username
        save_data(USERS_FILE, users)
    return False

def get_user_display_name(user_id):
    if user_id in users and "username" in users[user_id]:
        return users[user_id]["username"]
    return f"user_{user_id}"

def get_random_players(count=5):
    user_list = list(users.keys())
    if len(user_list) <= count:
        return user_list.copy()
    return random.sample(user_list, min(count, len(user_list)))

def check_cooldown(user_id, cooldown_time=1800):
    current_time = time.time()
    if user_id in cooldowns:
        elapsed = current_time - cooldowns[user_id]
        if elapsed < cooldown_time:
            remaining = cooldown_time - elapsed
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            return False, f"⏳ Нельзя так часто! Попробуй через {hours}ч {minutes}мин."
    cooldowns[user_id] = current_time
    save_data(COOLDOWN_FILE, cooldowns)
    return True, None

# ===== КОМАНДЫ БОТА =====

# 1. START
@bot.message_handler(commands=["start"])
def send_start_message(message):
    user_id = str(message.from_user.id)
    username = message.from_user.first_name
    if message.from_user.last_name:
        username += " " + message.from_user.last_name
    ensure_user_exists(user_id, username)

    welcome_text = """👋 Привет это бот мерит твою галду!
Добавь его в группу что бы соревноваться в размере с кентами!

📌 Основные команды:
/galda, /galdafon, /galdishechka, /galdazaraza - измерить галду
/my_stat - моя статистика
/all_stat - топ всех игроков
/cookie - игра в печеньку
/cookie_stats - статус игры

💡 Галда меняется случайно каждый раз!"""

    bot.reply_to(message, welcome_text)

# 2. HELP
@bot.message_handler(commands=["help"])
def send_help_message(message):
    help_text = """<<Основные команды>>
/start, /help, /galda, /galdafon, /galdishechka, /galdazaraza
/my_stat, /all_stat, /cookie, /cookie_stats"""
    bot.reply_to(message, help_text)

# 3. GALDA (основная команда)
@bot.message_handler(commands=["galda", "galdafon", "galdishechka", "galdazaraza"])
def send_random_message(message):
    user_id = str(message.from_user.id)
    username = message.from_user.first_name
    if message.from_user.last_name:
        username += " " + message.from_user.last_name
    ensure_user_exists(user_id, username)

    can_proceed, error_msg = check_cooldown(user_id)
    if not can_proceed:
        bot.reply_to(message, error_msg)
        return

    phrases = [
        "увеличилась", "уменьшилась", "сдулась", "выросла",
        "увеличилась в размерах", "немного уменьшилась"
    ]
    random_phrase = random.choice(phrases)
    current_size = users[user_id]["galda_size"]

    if "увеличилась" in random_phrase or "выросла" in random_phrase:
        change = random.randint(5, 15)
        users[user_id]["galda_size"] += change
        response = f"🎯 Твоя галда {random_phrase} на {change} анечек!\n📏 Теперь она {users[user_id]['galda_size']} анечек!"
    elif "уменьшилась" in random_phrase or "сдулась" in random_phrase:
        change = random.randint(5, 15)
        users[user_id]["galda_size"] = max(0, users[user_id]["galda_size"] - change)
        response = f"🎯 Твоя галда {random_phrase} на {change} анечек!\n📏 Теперь она {users[user_id]['galda_size']} анечек!"
    else:
        response = f"🎯 Твоя галда {random_phrase}!\n📏 Размер: {users[user_id]['galda_size']} анечек"

    save_data(USERS_FILE, users)
    bot.reply_to(message, response)

# 4. MY_STAT
@bot.message_handler(commands=["my_stat"])
def show_my_stat(message):
    user_id = str(message.from_user.id)
    username = message.from_user.first_name
    if message.from_user.last_name:
        username += " " + message.from_user.last_name
    ensure_user_exists(user_id, username)

    user_data = users[user_id]
    size = user_data['galda_size']

    # Определяем статус
    if size >= 100:
        status = "🏆 ГИГАНТСКАЯ ГАЛДА"
    elif size >= 70:
        status = "🔥 БОЛЬШАЯ ГАЛДА"
    elif size >= 50:
        status = "👍 НОРМАЛЬНАЯ ГАЛДА"
    elif size >= 30:
        status = "📏 СРЕДНЯЯ ГАЛДА"
    else:
        status = "💔 МАЛЕНЬКАЯ ГАЛДА"

    response = (
        f"📊 ТВОЯ СТАТИСТИКА:\n\n"
        f"👤 Имя: {user_data['username']}\n"
        f"{status}\n"
        f"📏 Размер галды: {user_data['galda_size']} анечек\n"
        f"🍪 Проиграно печенек: {user_data.get('cookies_lost', 0)}\n"
        f"📅 Зарегистрирован: {user_data.get('created_at', 'сегодня')[:10]}"
    )
    bot.reply_to(message, response)

# 5. ALL_STAT
@bot.message_handler(commands=["all_stat"])
def show_all_stat(message):
    if not users:
        bot.reply_to(message, "😔 Пока нет данных о пользователях")
        return

    sorted_users_list = sorted(users.items(),
                         key=lambda x: x[1].get('galda_size', 0),
                         reverse=True)

    stat_text = "🏆 ТОП ГАЛДУНОВ:\n\n"

    for idx, (user_id, user_data) in enumerate(sorted_users_list, 1):
        username = user_data.get('username', 'Unknown')[:20]
        size = user_data.get('galda_size', 0)
        cookies_lost = user_data.get('cookies_lost', 0)

        medal = ""
        if idx == 1: medal = "🥇 "
        elif idx == 2: medal = "🥈 "
        elif idx == 3: medal = "🥉 "
        elif idx <= 10: medal = "🔸 "
        else: medal = "🔹 "

        stat_text += f"{medal}{idx}. {username}: {size} анечек"
        if cookies_lost > 0:
            stat_text += f" ({cookies_lost}🍪)"
        stat_text += "\n"

        if len(stat_text) > 3500:
            stat_text += f"\n... и еще {len(sorted_users_list) - idx} пользователей"
            break

    # Добавляем общую статистику
    total_users = len(users)
    total_cookies = sum(u.get('cookies_lost', 0) for u in users.values())
    avg_size = sum(u.get('galda_size', 0) for u in users.values()) / total_users if total_users > 0 else 0

    stat_text += f"\n📊 ОБЩАЯ СТАТИСТИКА:\n"
    stat_text += f"👥 Всего игроков: {total_users}\n"
    stat_text += f"📏 Средний размер: {avg_size:.1f} анечек\n"
    stat_text += f"🍪 Всего проиграно печенек: {total_cookies}"

    bot.reply_to(message, stat_text)

# 6. COOKIE GAME
def start_roulette_animation(chat_id, players):
    global active_game

    # Отправляем начальное сообщение
    msg = bot.send_message(chat_id, "🎰 Запускается рулетка...")

    player_names = [get_user_display_name(p) for p in players]

    # Фаза ускорения (быстрая смена имен)
    for _ in range(5):
        if active_game is None:
            return
        current = random.choice(player_names)
        try:
            bot.edit_message_text(
                f"🎰 На печеньку дрочит...\n\n🔹 {current}",
                chat_id, msg.message_id
            )
        except:
            pass
        time.sleep(0.3)

    # Фаза замедления
    for _ in range(3):
        if active_game is None:
            return
        current = random.choice(player_names)
        try:
            bot.edit_message_text(
                f"🎰 На печеньку дрочит...\n\n🔸 {current}",
                chat_id, msg.message_id
            )
        except:
            pass
        time.sleep(0.6)

    # Финальный выбор
    loser_id = random.choice(players)
    loser_name = get_user_display_name(loser_id)

    try:
        bot.edit_message_text(
            f"🎯 ПЕЧЕНЬКА В КОНЧЕ!\n\n🎯 ВЫБРАН: {loser_name}",
            chat_id, msg.message_id
        )
    except:
        pass

    time.sleep(1)

    # Применяем штраф
    apply_cookie_penalty(chat_id, loser_id, players, msg.message_id)

def apply_cookie_penalty(chat_id, loser_id, players, msg_id):
    global active_game

    if loser_id in users:
        penalty = random.randint(15, 35)
        old_size = users[loser_id]["galda_size"]
        users[loser_id]["galda_size"] = max(5, old_size - penalty)
        users[loser_id]["cookies_lost"] = users[loser_id].get("cookies_lost", 0) + 1
        loser_name = get_user_display_name(loser_id)

        participants_text = "🎮 Участники рулетки:\n"
        for i, player_id in enumerate(players, 1):
            player_name = get_user_display_name(player_id)
            marker = "🎯" if player_id == loser_id else "🔹"
            participants_text += f"{marker} {i}. {player_name}\n"

        result = (
            f"🍪 ПЕЧЕНЬКА СЪЕДЕНА!\n\n"
            f"{participants_text}\n"
            f"💀 Проиграл: {loser_name}\n"
            f"📉 Его галда уменьшилась на {penalty} анечек!\n"
            f"🍪 Теперь у него {users[loser_id]['cookies_lost']} проигранных печенек!"
        )

        save_data(USERS_FILE, users)

        try:
            bot.edit_message_text(result, chat_id, msg_id)
            loser_mention = f"💀 <a href='tg://user?id={loser_id}'>Проигравший</a>, твоя галда уменьшилась! 🍪"
            bot.send_message(chat_id, loser_mention, parse_mode='HTML')
        except Exception as e:
            print(f"Ошибка отправки: {e}")

    active_game = None
    save_data('cookie_cd.json', {'time': time.time() + 5400})

@bot.message_handler(commands=["cookie"])
def start_cookie_game(message):
    global active_game, cookie_cooldown

    current_time = time.time()

    # Проверка кулдауна (1.5 часа)
    if current_time < cookie_cooldown:
        remaining = cookie_cooldown - current_time
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        bot.reply_to(message, f"⏳ Игру в печеньку можно будет начать через {hours}ч {minutes}мин.")
        return

    if active_game is not None:
        bot.reply_to(message, "🎮 Игра уже идет! Дождись окончания.")
        return

    player_count = random.randint(3, 7)
    players = get_random_players(player_count)

    if len(players) < 2:
        bot.reply_to(message, "❌ Недостаточно игроков в базе! Нужно минимум 2.")
        return

    active_game = {
        "players": players,
        "chat_id": message.chat.id
    }

    players_text = "🎮 Участники рулетки:\n"
    for i, player_id in enumerate(players, 1):
        player_name = get_user_display_name(player_id)
        players_text += f"🔹 {i}. {player_name}\n"

    response = (
        f"🍪 НАЧИНАЕТСЯ ИГРА В ПЕЧЕНЬКУ!\n\n"
        f"{players_text}\n"
        f"🎰 Начинается выбор проигравшего...\n"
        f"💀 Проигравший получит уменьшение галды!"
    )

    sent_message = bot.reply_to(message, response)

    # Запускаем рулетку в отдельном потоке
    roulette_thread = threading.Thread(
        target=start_roulette_animation,
        args=(message.chat.id, players)
    )
    roulette_thread.daemon = True
    roulette_thread.start()

# 7. COOKIE_STATS
@bot.message_handler(commands=["cookie_stats"])
def show_cookie_stats(message):
    global active_game, cookie_cooldown

    current_time = time.time()

    if active_game is not None:
        players_text = "🎮 Текущая игра:\n"
        for i, player_id in enumerate(active_game["players"], 1):
            player_name = get_user_display_name(player_id)
            players_text += f"{i}. {player_name}\n"

        bot.reply_to(message, f"🍪 Идет игра!\n{players_text}")
    elif current_time < cookie_cooldown:
        remaining = cookie_cooldown - current_time
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        bot.reply_to(message, f"⏳ Следующая игра через {hours}ч {minutes}мин")
    else:
        bot.reply_to(message, "✅ Игра доступна! Используй /cookie")

# 9. STATS
@bot.message_handler(commands=["stats"])
def stats_command(message):
    total_users = len(users)
    total_cookies = sum(u.get('cookies_lost', 0) for u in users.values())

    if users:
        avg_size = sum(u['galda_size'] for u in users.values()) / total_users
        max_size = max(u['galda_size'] for u in users.values())
        max_user = next(u['username'] for u in users.values() if u['galda_size'] == max_size)
    else:
        avg_size = 0
        max_size = 0
        max_user = "нет"

    response = (
        f"📈 ОБЩАЯ СТАТИСТИКА:\n\n"
        f"👥 Всего игроков: {total_users}\n"
        f"📏 Средний размер: {avg_size:.1f} анечек\n"
        f"🏆 Рекорд: {max_size} анечек ({max_user})\n"
        f"🍪 Всего проиграно печенек: {total_cookies}\n"
        f"⚙️ Бот работает на Replit.com"
    )

    bot.reply_to(message, response)

# ===== ЗАПУСК =====
def run_bot():
    print("=" * 60)
    print("🤖 GALDA BOT ЗАПУСКАЕТСЯ НА REPLIT")
    print("=" * 60)
    print(f"✅ Токен: {TOKEN[:10]}...")
    print(f"👥 Пользователей загружено: {len(users)}")
    print(f"🌐 Веб-сервер на порту {PORT}")
    print("=" * 60)

    # Запускаем автосохранение
    save_thread = threading.Thread(target=auto_save, daemon=True)
    save_thread.start()

    # Запускаем веб-сервер
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()

    time.sleep(2) 

    # Запускаем бота с перезапуском при ошибках
    while True:
        try:
            print("🔄 Запуск polling...")
            bot.polling(none_stop=True, interval=1, timeout=30)
        except KeyboardInterrupt:
            print("\n⏹ Остановлено пользователем")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            print("🔄 Перезапуск через 5 секунд...")
            time.sleep(5)
            continue

if __name__ == "__main__":
    run_bot()