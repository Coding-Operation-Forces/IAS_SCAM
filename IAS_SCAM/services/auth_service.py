import bcrypt
from db.database import SessionLocal
from db.models import Users
import services.audit_service as audit_service  


def hash_password(password: str) -> str:
    """Шифрує текстовий пароль за допомогою алгоритму bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Перевіряє відповідність пароля його зашифрованому хлібному зліпку."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        return False


def authenticate_user(login_text, password_text):
    """Проводить повну автентифікацію сесії користувача з перевіркою прапорця активності."""
    with SessionLocal() as db:
        try:
            user = db.query(Users).filter(Users.email == login_text, Users.is_active == 1).first()

            if user and verify_password(password_text, user.password_hash):
                audit_service.log_action(
                    user_id=user.id_user,
                    event_type="LOGIN",
                    table_name="users",
                    record_id=user.id_user,
                    old_value="Не авторизований",
                    new_value="Авторизований (Успішний вхід)"
                )
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