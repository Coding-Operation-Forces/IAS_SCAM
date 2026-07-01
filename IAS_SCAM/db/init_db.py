import bcrypt
from sqlalchemy import text  
from db.database import engine, Base, SessionLocal
from db.models import Roles, Users, Status  


def create_database_tables():
    print("[INIT] Перевірка та створення таблиць у PostgreSQL...")
    Base.metadata.create_all(bind=engine)

    seed_required_data()


def seed_required_data():
    """Автоматично створює базові ролі, супер-адміна та довідники, якщо їх немає."""
    with SessionLocal() as db:
        try:
            print("[INIT] Перевірка та синхронізація довідника статусів...")
            required_statuses = ["Нова", "У роботі", "Виконано", "Скасовано"]
            
            existing_statuses = db.query(Status).all()
            existing_status_names = [s.status_name.strip().lower() for s in existing_statuses]

            for req_status in required_statuses:
                if req_status.lower() not in existing_status_names:
                    print(f"[INIT] Створення базового статусу: {req_status}")
                    new_status = Status(status_name=req_status)
                    db.add(new_status)

            db.commit()

            try:
                db.execute(text("SELECT setval('status_id_status_seq', COALESCE((SELECT MAX(id_status) FROM status), 1), true);"))
                db.commit()
                print("[INIT] Індекс автоінкременту для статусів успішно синхронізовано з MAX(id).")
            except Exception as seq_err:
                db.rollback()
                print(f"[INIT] Попередження при скиданні лічильника індексу: {seq_err}")

            if db.query(Roles).count() == 0:
                print("[INIT] Таблиця ролей порожня. Створюю базові ролі...")
                roles = [
                    Roles(id_role=1, role_name="Адміністратор"),
                    Roles(id_role=2, role_name="Керівник"),
                    Roles(id_role=3, role_name="Диспетчер")
                ]
                db.add_all(roles)
                db.flush()

            if db.query(Users).count() == 0:
                print("[INIT] Користувачів не знайдено. Створюю першого Адміністратора...")

                default_password = "admin123"
                hashed_password = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

                admin_user = Users(
                    role_id=1,
                    full_name="Шевчук Кирил Костянтинович",
                    email="admin@scam.ua",
                    password_hash=hashed_password,
                    is_active=1,
                    failed_attempts=0
                )
                db.add(admin_user)
                db.commit()
                print("=" * 60)
                print("🚀 ПЕРШОГО АДМІНІСТРАТОРА УСПІШНО СТВОРЕНО!")
                print("📧 Логін: admin@scam.ua")
                print("🔑 Пароль: admin123")
                print("=" * 60)

        except Exception as e:
            db.rollback()
            print(f"[INIT] Critical error during database seeding: {e}")


if __name__ == "__main__":
    create_database_tables()