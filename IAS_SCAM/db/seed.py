import sys
import os

# Реєстрація кореневої директорії проєкту в системних шляхах пошуку модулів
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.database import SessionLocal
from db.models import Users
from services.auth_service import hash_password

def update_admin_password():
    db = SessionLocal()

    # Пошук запису адміністратора за фіксованою адресою електронної пошти
    admin = db.query(Users).filter(Users.email == "admin@skam.ua").first()

    if admin:
        # Безпечне оновлення пароля за допомогою хеш-функції
        admin.password_hash = hash_password("admin123")
        db.commit()
        print("✅ Пароль адміністратора успішно оновлено на хешований!")
        print(f"Тепер у базі зберігається: {admin.password_hash}")
    else:
        print("❌ Адміністратора не знайдено. Спочатку створіть його.")

    db.close()

if __name__ == "__main__":
    update_admin_password()