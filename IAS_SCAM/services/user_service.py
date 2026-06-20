# services/user_service.py
from db.database import SessionLocal
from db.models import Users, Roles
from services.auth_service import hash_password

def get_all_users():
    with SessionLocal() as db:
        try:
            users = db.query(Users).join(Roles, Users.role_id == Roles.id_role).order_by(Users.id_user.asc()).all()
            return [{
                "id": u.id_user,
                "role_name": u.role.role_name,
                "full_name": u.full_name,
                "email": u.email if u.email else ""
            } for u in users]
        except Exception as e:
            print(f"Помилка завантаження користувачів: {e}")
            return []

def get_all_roles():
    """Повертає список ролей для випадаючого списку при створенні користувача."""
    with SessionLocal() as db:
        try:
            roles = db.query(Roles).order_by(Roles.id_role.asc()).all()
            return [{"id": r.id_role, "name": r.role_name} for r in roles]
        except Exception:
            return []

def add_user(role_id, full_name, email, password):
    with SessionLocal() as db:
        try:
            new_user = Users(
                role_id=role_id,
                full_name=full_name,
                email=email,
                password_hash=hash_password(password) # Обов'язкове хешування!
            )
            db.add(new_user)
            db.commit()
            return True, "Користувача успішно додано!"
        except Exception as e:
            db.rollback()
            return False, f"Помилка БД: {str(e)}"

def update_user(user_id, role_id, full_name, email):
    with SessionLocal() as db:
        try:
            user = db.query(Users).filter(Users.id_user == user_id).first()
            if user:
                user.role_id = role_id
                user.full_name = full_name
                user.email = email
                db.commit()
                return True, "Дані користувача оновлено!"
            return False, "Користувача не знайдено."
        except Exception as e:
            db.rollback()
            return False, f"Помилка БД: {str(e)}"

def delete_user(user_id):
    with SessionLocal() as db:
        try:
            user = db.query(Users).filter(Users.id_user == user_id).first()
            if user:
                db.delete(user)
                db.commit()
                return True, "Користувача успішно видалено!"
            return False, "Користувача не знайдено."
        except Exception as e:
            db.rollback()
            return False, f"Помилка БД: {str(e)}"

def reset_password(user_id, new_password):
    with SessionLocal() as db:
        try:
            user = db.query(Users).filter(Users.id_user == user_id).first()
            if user:
                user.password_hash = hash_password(new_password)
                db.commit()
                return True, "Пароль успішно скинуто!"
            return False, "Користувача не знайдено."
        except Exception as e:
            db.rollback()
            return False, f"Помилка БД: {str(e)}"