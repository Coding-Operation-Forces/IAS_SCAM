import sys
import os

# 1. НАЙПЕРШЕ додаємо кореневу папку проєкту до системи (ДО імпортів бази)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 2. ТЕПЕР імпортуємо все через правильні абсолютні шляхи (з префіксом db.)
from db.database import SessionLocal
from db.models import Users
from services.auth_service import hash_password


def update_admin_password():
    db = SessionLocal()

    # Шукаємо нашого тестового адміністратора
    admin = db.query(Users).filter(Users.email == "admin@skam.ua").first()

    if admin:
        # Замінюємо старий пароль на надійний хеш
        admin.password_hash = hash_password("admin123")
        db.commit()
        print("✅ Пароль адміністратора успішно оновлено на хешований!")
        print(f"Тепер у базі зберігається: {admin.password_hash}")
    else:
        print("❌ Адміністратора не знайдено. Спочатку створіть його.")

    db.close()


if __name__ == "__main__":
    update_admin_password()