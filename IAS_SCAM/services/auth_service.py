import bcrypt
from db.database import SessionLocal
from db.models import Users
import services.audit_service as audit_service
import datetime


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
    """
    Серверна автентифікація із захистом від Brute-Force атак на рівні БД.
    """
    with SessionLocal() as db:
        try:
            user = db.query(Users).filter(Users.email == login_text, Users.is_active == 1).first()

            if not user:
                return {"status": "error", "message": "Невірний логін або пароль!"}

            if user.lock_until and user.lock_until > datetime.datetime.now():
                time_left = int((user.lock_until - datetime.datetime.now()).total_seconds())

                audit_service.log_action(
                    user_id=user.id_user, event_type="LOGIN_REJECTED", table_name="users",
                    record_id=user.id_user, old_value="Locked", new_value=f"Brute-force blocked for next {time_left}s"
                )
                return {
                    "status": "locked",
                    "message": f"Цей обліковий запис тимчасово заблоковано на сервері!\nСпробуйте знову через {time_left} сек."
                }

            if verify_password(password_text, user.password_hash):
                user.failed_attempts = 0
                user.lock_until = None
                db.commit()

                audit_service.log_action(
                    user_id=user.id_user, event_type="LOGIN", table_name="users",
                    record_id=user.id_user, old_value="Не авторизований", new_value="Авторизований (Успішний вхід)"
                )

                return {
                    "status": "success",
                    "data": {
                        "id": user.id_user,
                        "full_name": user.full_name,
                        "role_id": user.role_id,
                        "role_name": user.role.role_name
                    }
                }
            else:
                user.failed_attempts += 1
                message = f"Невірний логін або пароль!\nЗалишилось спроб: {3 - user.failed_attempts}"

                if user.failed_attempts >= 3:
                    user.lock_until = datetime.datetime.now() + datetime.timedelta(minutes=1)
                    message = "Перевищено ліміт спроб! Обліковий запис заблоковано на сервері на 1 хвилину."

                    audit_service.log_action(
                        user_id=user.id_user, event_type="ACCOUNT_LOCKED", table_name="users",
                        record_id=user.id_user, old_value="Active", new_value="Locked for 1 min due to 3 failed entries"
                    )
                else:
                    audit_service.log_action(
                        user_id=user.id_user, event_type="LOGIN_FAILED", table_name="users",
                        record_id=user.id_user, old_value="Active", new_value=f"Failed attempt #{user.failed_attempts}"
                    )

                db.commit()
                return {"status": "error", "message": message}

        except Exception as e:
            db.rollback()
            print(f"Помилка БД під час авторизації: {e}")
            return {"status": "error", "message": f"Помилка сервера бази даних: {str(e)}"}