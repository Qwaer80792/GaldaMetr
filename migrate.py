import os
import json
import time
from bot import app, db, User, Cooldown

def migrate():
    with app.app_context():
        # Migrate Users
        if os.path.exists('users.json'):
            try:
                with open('users.json', 'r', encoding='utf-8') as f:
                    users_data = json.load(f)
                    for user_id, data in users_data.items():
                        if not db.session.get(User, user_id):
                            new_user = User(
                                id=user_id,
                                username=data.get('username'),
                                galda_size=data.get('galda_size', 50.0),
                                cookies_lost=data.get('cookies_lost', 0)
                            )
                            db.session.add(new_user)
                print("Users migrated successfully.")
            except Exception as e:
                print(f"Error migrating users: {e}")

        # Migrate Cooldowns
        if os.path.exists('cooldowns.json'):
            try:
                with open('cooldowns.json', 'r', encoding='utf-8') as f:
                    cd_data = json.load(f)
                    for user_id, last_used in cd_data.items():
                        if not db.session.get(Cooldown, user_id):
                            new_cd = Cooldown(user_id=user_id, last_used=last_used)
                            db.session.add(new_cd)
                print("Cooldowns migrated successfully.")
            except Exception as e:
                print(f"Error migrating cooldowns: {e}")

        db.session.commit()
        print("Migration complete.")

if __name__ == "__main__":
    migrate()
