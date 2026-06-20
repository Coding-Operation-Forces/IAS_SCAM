import bcrypt
from db.database import SessionLocal
from db.models import Users


def hash_password(password: str) -> str:
    """Генерує сіль та незворотно хешує пароль."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Перевіряє, чи збігається введений пароль зі збереженим хешем."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        # Якщо в базі зберігся старий нехешований пароль, bcrypt видасть помилку
        return False


def authenticate_user(login_text, password_text):
    """
    Перевіряє email та пароль у базі даних.
    Повертає словник з даними користувача або None.
    """
    with SessionLocal() as db:
        try:
            # Шукаємо користувача за email
            user = db.query(Users).filter(Users.email == login_text).first()

            # ВИКОРИСТОВУЄМО ФУНКЦІЮ ПЕРЕВІРКИ ХЕШУ ЗАМІСТЬ "=="
            if user and verify_password(password_text, user.password_hash):
                return {
                    "id": user.id_user,
                    "full_name": user.full_name,
                    "role_id": user.role_id,
                    "role_name": user.role.role_name
                }
            return None
        except Exception as e:
            print(f"Помилка БД під час авторизації: {e}")
            return None