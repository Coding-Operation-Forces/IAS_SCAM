import datetime
from db.database import SessionLocal
from db.models import AuditLog, Users


def log_action(user_id, event_type, table_name, record_id=None, old_value=None, new_value=None):
    """
    Універсальна функція для збереження дій користувачів у базу даних.
    Можна викликати в будь-якому сервісі (user_service, dictionary_service тощо).
    """
    if not user_id:
        return False

    with SessionLocal() as db:
        try:
            log_item = AuditLog(
                user_id=user_id,
                event_type=str(event_type)[:45],
                table_name=str(table_name)[:45],
                record_id=record_id,
                old_value=str(old_value)[:255] if old_value else None,
                new_value=str(new_value)[:255] if new_value else None,
                log_time=datetime.datetime.now()  # Використовуємо локальний час сервера
            )
            db.add(log_item)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"[AUDIT ERROR] Не вдалося записати лог: {e}")
            return False


def get_all_audit_logs():
    """Витягує всі записи аудиту з використанням безпечного LEFT JOIN."""
    with SessionLocal() as db:
        try:
            # Використовуємо isouter=True для створення LEFT OUTER JOIN
            logs = db.query(AuditLog).join(Users, AuditLog.user_id == Users.id_user, isouter=True) \
                .order_by(AuditLog.log_time.desc()).all()

            result = []
            for l in logs:
                # Якщо користувача немає в системі (наприклад, системний лог або видалений),
                # замість падіння додатка виведемо "Система / Анонім"
                user_name = l.user.full_name if l.user else "Система / Анонім"

                result.append({
                    "id": l.id_log,
                    "user_name": user_name,
                    "time": l.log_time.strftime("%d.%m.%Y %H:%M:%S") if l.log_time else "—",
                    "event": l.event_type if l.event_type else "—",
                    "table": l.table_name if l.table_name else "—",
                    "old_val": l.old_value if l.old_value else "—",
                    "new_val": l.new_value if l.new_value else "—"
                })
            return result
        except Exception as e:
            print(f"[AUDIT ERROR] Помилка завантаження журналу подій: {e}")
            return []