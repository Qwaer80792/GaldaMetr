import os
import sys
import time
import subprocess
import signal
from datetime import datetime

HOME_DIR = os.path.expanduser('~/')
BOT_DIR = os.path.join(HOME_DIR, 'galda_bot')
LOG_DIR = os.path.join(BOT_DIR, 'logs')
PID_FILE = os.path.join(BOT_DIR, 'bot.pid')
LOG_FILE = os.path.join(LOG_DIR, 'bot.log')
ERROR_LOG = os.path.join(LOG_DIR, 'error.log')

def ensure_directories():
    for directory in [BOT_DIR, LOG_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Создана директория: {directory}")

def get_bot_pid():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
                os.kill(pid, 0)
                return pid
        except (ValueError, OSError, FileNotFoundError):
            return None
    return None

def stop_bot():
    pid = get_bot_pid()
    if pid:
        print(f"Останавливаем бота с PID {pid}...")
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)

            try:
                os.kill(pid, 0)
                print(f"Процесс {pid} все еще работает, принудительно завершаем...")
                os.kill(pid, signal.SIGKILL)
                time.sleep(1)
            except OSError:
                print("Бот успешно остановлен")

            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)

        except Exception as e:
            print(f"Ошибка при остановке бота: {e}")
            return False
    else:
        print("Бот не запущен")
    return True

def start_bot():
    print("Запускаем бота...")

    stop_bot()

    bot_script = os.path.join(BOT_DIR, 'bot.py')

    if not os.path.exists(bot_script):
        print(f"Ошибка: файл бота не найден: {bot_script}")
        return False

    try:
        with open(LOG_FILE, 'a') as log_file, open(ERROR_LOG, 'a') as error_file:
            process = subprocess.Popen(
                [sys.executable, bot_script],
                stdout=log_file,
                stderr=error_file,
                cwd=BOT_DIR
            )

        with open(PID_FILE, 'w') as f:
            f.write(str(process.pid))

        print(f"Бот запущен с PID {process.pid}")

        time.sleep(5)

        if process.poll() is None:
            print("Бот успешно запущен и работает")
            log_message(f"Бот перезапущен в {datetime.now()}")
            return True
        else:
            print("Ошибка: бот завершился сразу после запуска")
            return False

    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")
        log_message(f"Ошибка запуска: {e}", error=True)
        return False

def log_message(message, error=False):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"

    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)

    if error:
        with open(ERROR_LOG, 'a') as f:
            f.write(log_entry)

def restart_bot():
    print("=" * 50)
    print(f"Начало перезапуска: {datetime.now()}")
    print("=" * 50)

    ensure_directories()

    if stop_bot():
        if start_bot():
            print("Перезапуск успешно завершен")
            return True
        else:
            print("Не удалось запустить бота после остановки")
            return False
    else:
        print("Не удалось остановить бота")
        return False

def show_status():
    print("=" * 50)
    print(f"Статус бота: {datetime.now()}")
    print("=" * 50)

    pid = get_bot_pid()
    if pid:
        print(f"✓ Бот запущен (PID: {pid})")

        try:
            proc_file = f'/proc/{pid}/stat'
            if os.path.exists(proc_file):
                with open(proc_file, 'r') as f:
                    stats = f.read().split()
                    if len(stats) > 21:
                        start_time = int(stats[21])

                        print("  Статус: Активен")
        except:
            pass
    else:
        print("✗ Бот не запущен")

    if os.path.exists(LOG_FILE):
        size = os.path.getsize(LOG_FILE)
        print(f"  Размер лога: {size / 1024:.1f} KB")

    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 0:
        print("\nПоследние записи в логе:")
        try:
            with open(LOG_FILE, 'r') as f:
                lines = f.readlines()[-5:]
                for line in lines:
                    print(f"  {line.strip()}")
        except:
            pass

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'start':
            ensure_directories()
            start_bot()
        elif command == 'stop':
            stop_bot()
        elif command == 'restart':
            restart_bot()
        elif command == 'status':
            show_status()
        else:
            print("Использование:")
            print("  python restart_bot.py [команда]")
            print("\nКоманды:")
            print("  start    - запустить бота")
            print("  stop     - остановить бота")
            print("  restart  - перезапустить бота")
            print("  status   - показать статус")
    else:
        show_status()

if __name__ == "__main__":
    main()
