import sqlite3
import json
import os
from datetime import datetime

class Database:
    def __init__(self, db_path: str = "galda_bot.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Создает соединение с базой данных"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Возвращает словари вместо кортежей
        return conn
    
    def init_database(self):
        """Инициализирует таблицы базы данных"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    galda_size INTEGER DEFAULT 50,
                    cookies_lost INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            print(f"База данных инициализирована: {self.db_path}")
    
    def ensure_user_exists(self, user_id: str, username: str = None) -> bool:
        """Создает пользователя если его нет"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                cursor.execute('''
                    INSERT INTO users (user_id, username, galda_size, cookies_lost)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, username or f"user_{user_id}", 50, 0))
                conn.commit()
                return True
            else:
                if username:
                    cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", 
                                 (username, user_id))
                    conn.commit()
                return False
    
    def get_user(self, user_id: str) -> dict:
        """Получает данные пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_user_galda(self, user_id: str, new_size: int):
        """Обновляет размер галды"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET galda_size = ? 
                WHERE user_id = ?
            ''', (new_size, user_id))
            conn.commit()
    
    def increment_cookies_lost(self, user_id: str):
        """Увеличивает счетчик проигранных печенек"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET cookies_lost = cookies_lost + 1 
                WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
    
    def get_all_users(self) -> list:
        """Получает всех пользователей"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY galda_size DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_random_users(self, count: int = 5) -> list:
        """Получает случайных пользователей"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users ORDER BY RANDOM() LIMIT ?", (count,))
            return [row['user_id'] for row in cursor.fetchall()]

# Глобальный экземпляр базы данных
db = Database()
