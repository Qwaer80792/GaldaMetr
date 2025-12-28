import random
import telebot
import json
import time
import threading
import os

TelegramBotToken = os.getenv('TELEGRAM_BOT_TOKEN', '8129099142:AAFIDgn3njqe3uTKV5pbJLH6Pypc8xsWuF8')

INITIAL_GALDA_SIZE = 50
COOKIE_GAME_DURATION = 120
COOKIE_COOLDOWN = 5400
USER_COOLDOWN = 1800
ROULETTE_DURATION = 10

bot = telebot.TeleBot(TelegramBotToken)

class GameState:
    def __init__(self):
        self.lock = threading.Lock()
        self.user_cooldowns = {}
        self.cookie_cooldown = 0
        self.active_cookie_game = {
            "active": False,
            "players": [],
            "chat_id": None,
            "end_time": None,
            "message_id": None,
            "game_id": None,
            "roulette_message_id": None,
            "roulette_active": False,
            "selected_player": None
        }

game_state = GameState()

def load_users():
    try:
        users_file = os.path.join(os.path.dirname(__file__), 'users.json')
        with open(users_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if content.strip():
                return json.loads(content)
    except Exception as e:
        print(f"Ошибка загрузки users.json: {e}")
    return {}

def save_users(users_data):
    try:
        users_file = os.path.join(os.path.dirname(__file__), 'users.json')
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения: {e}")

users_file = os.path.join(os.path.dirname(__file__), 'users.json')
if not os.path.exists(users_file):
    print(f"Создаю файл users.json: {users_file}")
    with open(users_file, 'w', encoding='utf-8') as f:
        json.dump({}, f)

users = load_users()
print(f"Загружено пользователей: {len(users)}")

def ensure_user_exists(user_id, username=None):
    if user_id not in users:
        users[user_id] = {
            "galda_size": INITIAL_GALDA_SIZE,
            "cookies_lost": 0,
            "username": username or f"user_{user_id}"
        }
        save_users(users)
        return True
    else:
        if username and users[user_id].get("username") != username:
            users[user_id]["username"] = username
            save_users(users)
    return False

def get_user_display_name(user_id):
    if user_id in users and "username" in users[user_id]:
        return users[user_id]["username"]
    return f"user_{user_id}"

def get_random_players(count=5):
    """Получает случайных игроков из всех пользователей"""
    user_list = list(users.keys())
    if len(user_list) <= count:
        return user_list.copy()
    return random.sample(user_list, min(count, len(user_list)))

def start_roulette_animation(chat_id, players, original_message_id):
    with game_state.lock:
        if not game_state.active_cookie_game["active"]:
            return
        game_state.active_cookie_game["roulette_active"] = True

    try:
        roulette_msg = bot.send_message(chat_id, "🎰 Рулетка запускается...")
        roulette_message_id = roulette_msg.message_id

        with game_state.lock:
            game_state.active_cookie_game["roulette_message_id"] = roulette_message_id
    except Exception as e:
        print(f"Ошибка рулетки: {e}")
        return

    player_names = [get_user_display_name(player_id) for player_id in players]
    duration = ROULETTE_DURATION
    start_time = time.time()

    acceleration_phase = duration * 0.3
    while time.time() - start_time < acceleration_phase:
        if not game_state.active_cookie_game["roulette_active"]:
            return

        current_player = random.choice(player_names)
        try:
            bot.edit_message_text(
                f"🎰 На печеньку дрочит...\n\n🔹 {current_player}",
                chat_id,
                roulette_message_id
            )
        except:
            pass
        time.sleep(0.2)

    deceleration_phase = duration * 0.5
    while time.time() - start_time < acceleration_phase + deceleration_phase:
        if not game_state.active_cookie_game["roulette_active"]:
            return

        current_player = random.choice(player_names)
        try:
            bot.edit_message_text(
                f"🎰 На печеньку дрочит...\n\n🔸 {current_player}",
                chat_id,
                roulette_message_id
            )
        except:
            pass
        time.sleep(0.4)

    final_phase = duration * 0.2
    interval = 0.6
    selected_index = random.randint(0, len(players) - 1)

    for i in range(3):
        if not game_state.active_cookie_game["roulette_active"]:
            return

        if i < 2:
            temp_player = random.choice([p for p in player_names if p != player_names[selected_index]])
        else:
            temp_player = player_names[selected_index]

        try:
            if i < 2:
                bot.edit_message_text(
                    f"🎰 На печеньку дрочит...\n\n🔹 {temp_player}",
                    chat_id,
                    roulette_message_id
                )
            else:
                bot.edit_message_text(
                    f"🎯 Печенька в конче!\n\n🎯 ВЫБРАН: {temp_player}",
                    chat_id,
                    roulette_message_id
                )
        except:
            pass
        time.sleep(interval)

    loser_id = players[selected_index]
    with game_state.lock:
        game_state.active_cookie_game["selected_player"] = loser_id
        game_state.active_cookie_game["roulette_active"] = False

    apply_cookie_penalty(chat_id, loser_id, players)

def apply_cookie_penalty(chat_id, loser_id, players):
    if loser_id in users:
        penalty = random.randint(15, 35)
        old_size = users[loser_id]["galda_size"]
        users[loser_id]["galda_size"] = max(5, old_size - penalty)
        users[loser_id]["cookies_lost"] = users[loser_id].get("cookies_lost", 0) + 1
        loser_name = get_user_display_name(loser_id)

        participants_text = "Участники рулетки:\n"
        for i, player_id in enumerate(players, 1):
            player_name = get_user_display_name(player_id)
            marker = "🎯" if player_id == loser_id else "🔹"
            participants_text += f"{marker} {i}. {player_name}\n"

        result = (
            f"🍪 Печенька cъедена!\n\n"
            f"{participants_text}\n"
            f"💀 Проиграл: {loser_name}\n"
            f"📉 Его галда уменьшилась на {penalty} анечек!\n"
            f"🍪 Теперь у него {users[loser_id]['cookies_lost']} проигранных печенек!"
        )

        save_users(users)

        try:
            bot.send_message(chat_id, result)
            loser_mention = f"💀 <a href='tg://user?id={loser_id}'>Проигравший</a>, твоя галда уменьшилась! 🍪"
            bot.send_message(chat_id, loser_mention, parse_mode='HTML')
        except Exception as e:
            print(f"Ошибка отправки: {e}")

    with game_state.lock:
        game_state.active_cookie_game.update({
            "active": False,
            "players": [],
            "chat_id": None,
            "end_time": None,
            "message_id": None,
            "game_id": None,
            "roulette_message_id": None,
            "roulette_active": False,
            "selected_player": None
        })
        game_state.cookie_cooldown = time.time() + COOKIE_COOLDOWN

def check_cooldown(user_id, cooldown_time=USER_COOLDOWN):
    current_time = time.time()

    with game_state.lock:
        if user_id in game_state.user_cooldowns:
            elapsed_time = current_time - game_state.user_cooldowns[user_id]
            if elapsed_time < cooldown_time:
                remaining_time = cooldown_time - elapsed_time
                hours = int(remaining_time // 3600)
                minutes = int((remaining_time % 3600) // 60)
                return False, f"Нельзя так часто! Попробуй через {hours} ч. {minutes} мин."

        game_state.user_cooldowns[user_id] = current_time
        return True, None

@bot.message_handler(commands=["start"])
def send_start_message(message):
    user_id = str(message.from_user.id)
    username = message.from_user.first_name
    if message.from_user.last_name:
        username += " " + message.from_user.last_name
    ensure_user_exists(user_id, username)
    bot.reply_to(message, "Привет это бот мерит твою галду!\nДобавь его в группу что бы соревноваться в размере с кентами!")

@bot.message_handler(commands=["help"])
def send_help_message(message):
    help_text = (
        "<<Основные команды>>\n"
        "/start, /help, /galda, /galdafon, /galdishechka, /galdazaraza\n"
        "/my_stat, /all_stat, /cookie, /cookie_stats\n\n"
    )
    bot.reply_to(message, help_text)

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
        response = f"Твоя галда {random_phrase} на {change} анечек! Теперь она {users[user_id]['galda_size']} анечек!"
    elif "уменьшилась" in random_phrase or "сдулась" in random_phrase:
        change = random.randint(5, 15)
        users[user_id]["galda_size"] = max(0, users[user_id]["galda_size"] - change)
        response = f"Твоя галда {random_phrase} на {change} анечек! Теперь она {users[user_id]['galda_size']} анечек!"
    else:
        response = f"Твоя галда {random_phrase}! Размер: {users[user_id]['galda_size']} анечек"

    save_users(users)
    bot.reply_to(message, response)

@bot.message_handler(commands=["cookie"])
def start_cookie_game(message):
    global users
    users = load_users()

    current_time = time.time()

    with game_state.lock:
        cookie_cd = game_state.cookie_cooldown
        active_game = game_state.active_cookie_game.copy()

    if current_time < cookie_cd:
        remaining_time = cookie_cd - current_time
        hours = int(remaining_time // 3600)
        minutes = int((remaining_time % 3600) // 60)
        bot.reply_to(message, f"Игру в печеньку можно будет начать через {hours} ч. {minutes} мин.")
        return

    if active_game["active"]:
        if active_game["roulette_active"]:
            bot.reply_to(message, "Дождись окончания текущей игры!")
        else:
            bot.reply_to(message, "Игра уже идет!")
        return

    player_count = random.randint(3, 7)
    players = get_random_players(player_count)

    if len(players) < 2:
        bot.reply_to(message, "Недостаточно игроков в базе для начала игры! Нужно минимум 2.")
        return

    current_time = time.time()
    with game_state.lock:
        game_state.active_cookie_game.update({
            "active": True,
            "players": players,
            "chat_id": message.chat.id,
            "end_time": current_time + COOKIE_GAME_DURATION,
            "message_id": message.message_id,
            "game_id": current_time,
            "roulette_message_id": None,
            "roulette_active": False,
            "selected_player": None
        })

    players_text = "Участники рулетки:\n"
    for i, player_id in enumerate(players, 1):
        player_name = get_user_display_name(player_id)
        players_text += f"🔹 {i}. {player_name}\n"

    response = (
        f"🍪 Начинается игра в печеньку!\n\n"
        f"{players_text}\n"
        f"🎰 Начинается выбор проигравшего...\n"
        f"💀 Проигравший получит уменьшение галды!"
    )

    try:
        sent_message = bot.reply_to(message, response)
        with game_state.lock:
            game_state.active_cookie_game["message_id"] = sent_message.message_id
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        with game_state.lock:
            game_state.active_cookie_game.update({
                "active": False,
                "players": [],
                "chat_id": None,
                "end_time": None,
                "message_id": None,
                "game_id": None,
                "roulette_message_id": None,
                "roulette_active": False,
                "selected_player": None
            })
        return

    roulette_thread = threading.Thread(
        target=start_roulette_animation,
        args=(message.chat.id, players, sent_message.message_id)
    )
    roulette_thread.daemon = True
    roulette_thread.start()

@bot.message_handler(commands=["cookie_stats"])
def show_cookie_stats(message):
    with game_state.lock:
        active_game = game_state.active_cookie_game.copy()

    if not active_game["active"]:
        bot.reply_to(message, "Сейчас нет активной игры с печенькой! Начни игру командой /cookie")
        return

    players_text = "Участники:\n"
    for i, player_id in enumerate(active_game["players"], 1):
        player_name = get_user_display_name(player_id)
        players_text += f"{i}. {player_name}\n"

    if active_game["roulette_active"]:
        status = "🎰 Выбирается проигравший..."
    else:
        status = "⏳ Ожидание..."

    stats = (
        f"🍪 Текущая игра в печеньку:\n\n"
        f"{players_text}\n"
        f"{status}\n"
        f"💀 Случайный участник получит уменьшение галды!"
    )
    bot.reply_to(message, stats)

@bot.message_handler(commands=["my_stat"])
def show_my_stat(message):
    user_id = str(message.from_user.id)
    username = message.from_user.first_name
    if message.from_user.last_name:
        username += " " + message.from_user.last_name
    ensure_user_exists(user_id, username)
    user_data = users[user_id]
    response = (
        f"📊 Твоя статистика:\n"
        f"👤 Имя: {user_data['username']}\n"
        f"📏 Размер галды: {user_data['galda_size']} анечек\n"
        f"🍪 Проиграно печенек: {user_data.get('cookies_lost', 0)}"
    )
    bot.reply_to(message, response)

@bot.message_handler(commands=["all_stat"])
def show_all_stat(message):
    # Обновляем данные перед показом статистики
    global users
    users = load_users()

    if not users:
        bot.reply_to(message, "Пока нет данных о пользователях")
        return

    sorted_users_list = sorted(users.items(),
                         key=lambda x: x[1].get('galda_size', 0),
                         reverse=True)

    stat_text = "🏆 Топ галдунов:\n\n"

    # Убираем ограничение в 10 пользователей
    for idx, (user_id, user_data) in enumerate(sorted_users_list, 1):
        username = get_user_display_name(user_id)
        size = user_data.get('galda_size', 0)
        cookies_lost = user_data.get('cookies_lost', 0)
        stat_text += f"{idx}. {username}: {size} анечек ({cookies_lost}🍪)\n"
        if len(stat_text) > 3000:
            stat_text += f"\n... и еще {len(sorted_users_list) - idx} пользователей"
            break

    bot.reply_to(message, stat_text)

@bot.message_handler(commands=["reload_users"])
def reload_users_command(message):
    global users
    users = load_users()
    bot.reply_to(message, f"База пользователей обновлена! Всего пользователей: {len(users)}")

# Главный блок запуска
if __name__ == "__main__":
    print("=" * 50)
    print("Бот запускается на PythonAnywhere...")
    print(f"Токен: {'установлен' if TelegramBotToken else 'не найден'}")
    print(f"Пользователей в базе: {len(users)}")
    print(f"Текущая директория: {os.getcwd()}")
    print(f"Файл users.json: {os.path.join(os.path.dirname(__file__), 'users.json')}")
    print("=" * 50)

    try:
        print("Запуск infinity_polling...")
        bot.infinity_polling()
    except Exception as e:
        print(f"Критическая ошибка в работе бота: {e}")
        import traceback
        traceback.print_exc()