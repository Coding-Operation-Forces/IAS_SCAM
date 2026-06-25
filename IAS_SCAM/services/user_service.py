# services/user_service.py
from db.database import SessionLocal
from db.models import Users, Roles
from services.auth_service import hash_password
import services.audit_service as audit_service  # Підключаємо аудит


def get_all_users():
    """Повертає тільки АКТИВНИХ користувачів для виведення в АРМ Адміністратора."""
    with SessionLocal() as db:
        try:
            # Фільтруємо за умовою is_active == 1
            users = db.query(Users).join(Roles, Users.role_id == Roles.id_role)\
                     .filter(Users.is_active == 1)\
                     .order_by(Users.id_user.asc()).all()
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
    with SessionLocal() as db:
        try:
            roles = db.query(Roles).order_by(Roles.id_role.asc()).all()
            return [{"id": r.id_role, "name": r.role_name} for r in roles]
        except Exception:
            return []


def add_user(role_id, full_name, email, password, admin_id=1):
    with SessionLocal() as db:
        try:
            new_user = Users(
                role_id=role_id,
                full_name=full_name,
                email=email,
                password_hash=hash_password(password)
            )
            db.add(new_user)
            db.flush()

            # Атомарне логування створення кожного параметра користувача окремо
            user_fields = [
                ("full_name", "Не існувало", full_name),
                ("email", "Не існувало", email),
                ("role_id", "Не існувало", role_id)
            ]
            for f_name, old_f, new_f in user_fields:
                audit_service.log_action(
                    user_id=admin_id,
                    event_type="INSERT",
                    table_name=f"users.{f_name}",
                    record_id=new_user.id_user,
                    old_value=old_f,
                    new_value=str(new_f)
                )

            db.commit()
            return True, "Користувача успішно додано!"
        except Exception as e:
            db.rollback()
            return False, f"Помилка БД: {str(e)}"


def update_user(user_id, role_id, full_name, email, admin_id=1):
    with SessionLocal() as db:
        try:
            user = db.query(Users).filter(Users.id_user == user_id).first()
            if user:
                # Перевіряємо та атомарно логуємо тільки ПІБ, якщо воно було змінене
                if user.full_name != full_name:
                    audit_service.log_action(
                        user_id=admin_id, event_type="UPDATE", table_name="users.full_name",
                        record_id=user_id, old_value=user.full_name, new_value=full_name
                    )
                    user.full_name = full_name

                # Перевіряємо та атомарно логуємо тільки новий Email
                if user.email != email:
                    audit_service.log_action(
                        user_id=admin_id, event_type="UPDATE", table_name="users.email",
                        record_id=user_id, old_value=user.email or "—", new_value=email
                    )
                    user.email = email

                # Перевіряємо та атомарно логуємо тільки Роль
                if user.role_id != role_id:
                    audit_service.log_action(
                        user_id=admin_id, event_type="UPDATE", table_name="users.role_id",
                        record_id=user_id, old_value=str(user.role_id), new_value=str(role_id)
                    )
                    user.role_id = role_id

                db.commit()
                return True, "Дані користувача оновлено!"  # <--- ВИПРАВЛЕНО: Додано логічний успішний ретурн вікна
            return False, "Користувача не знайдено."
        except Exception as e:
            db.rollback()
            return False, f"Помилка БД: {str(e)}"


def delete_user(user_id, admin_id=1):
    """Виконує безпечне м'яке видалення (Soft Delete). Зберігає всі логи та заявки в БД."""
    with SessionLocal() as db:
        try:
            user = db.query(Users).filter(Users.id_user == user_id).first()
            if user:
                # Замість видалення з бази — деактивуємо обліковий запис!
                user.is_active = 0

                # АТОМАРНО ЛОГУЄМО ДЕАКТИВАЦІЮ (користувач ніби видалений, але дані на місці)
                audit_service.log_action(
                    user_id=admin_id,
                    event_type="DELETE",
                    table_name="users.is_active",
                    record_id=user_id,
                    old_value="1 (Активний)",
                    new_value="0 (Видалений/Деактивований)"
                )

                db.commit()
                return True, "Користувача успішно видалено з системи!"
            return False, "Користувача не знайдено."
        except Exception as e:
            db.rollback()
            return False, f"Помилка БД: {str(e)}"


def reset_password(user_id, new_password, admin_id=1):
    with SessionLocal() as db:
        try:
            user = db.query(Users).filter(Users.id_user == user_id).first()
            if user:
                user.password_hash = hash_password(new_password)

                # Атомарне логування скидання пароля
                audit_service.log_action(
                    user_id=admin_id,
                    event_type="RESET_PASSWORD",
                    table_name="users.password_hash",
                    record_id=user_id,
                    old_value="Дійсний хеш анульовано",
                    new_value="Встановлено новий безпечний пароль"
                )

                db.commit()
                return True, "Пароль успішно скинуто!"
            return False, "Користувача не знайдено."
        except Exception as e:
            db.rollback()
            return False, f"Помилка БД: {str(e)}"