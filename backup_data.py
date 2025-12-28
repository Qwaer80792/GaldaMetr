import os
import shutil
from datetime import datetime

HOME_DIR = os.path.expanduser('~/')
BOT_DIR = os.path.join(HOME_DIR, 'galda_bot')
BACKUP_DIR = os.path.join(HOME_DIR, 'backups')

def create_backup():

    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f'bot_backup_{timestamp}.tar.gz')

    try:
        import tarfile

        files_to_backup = []
        users_file = os.path.join(BOT_DIR, 'users.json')
        if os.path.exists(users_file):
            files_to_backup.append(users_file)

        if files_to_backup:
            with tarfile.open(backup_file, 'w:gz') as tar:
                for file_path in files_to_backup:
                    arcname = os.path.basename(file_path)
                    tar.add(file_path, arcname=arcname)

            print(f"Резервная копия создана: {backup_file}")
            return True
        else:
            print("Нет файлов для резервного копирования")
            return False

    except Exception as e:
        print(f"Ошибка создания резервной копии: {e}")
        return False

if __name__ == "__main__":
    create_backup()
