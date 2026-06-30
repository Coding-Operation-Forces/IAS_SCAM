import bcrypt
from db.database import engine, Base, SessionLocal
from db.models import Roles, Users


def create_database_tables():
    print("[INIT] Перевірка та створення таблиць у PostgreSQL...")
    # Створює лише ті таблиці, яких ще немає в СУБД
    Base.metadata.create_all(bind=engine)

    seed_required_data()


def seed_required_data():
    """Автоматично створює базові ролі та супер-адміна, якщо база порожня."""
    with SessionLocal() as db:
        try:
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

                # дефолтний пароль: admin123
                default_password = "admin123"
                hashed_password = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

                admin_user = Users(
                    role_id=1,
                    full_name="Адміністратор",
                    email="admin@scam.ua",
                    password_hash=hashed_password,
                    is_active=1,
                    failed_attempts=0
                )
                db.add(admin_user)
                db.commit()
                print("=" * 60)
                print("🚀 ПЕРШОГО АДМІНІСТРАТОРА УСПІШНО СТВОРЕНО!")
                print("📧 Логін: admin@skam.ua")
                print("🔑 Пароль: admin123")
                print("=" * 60)
            else:
                pass

        except Exception as e:
            db.rollback()
            print(f"[INIT] Critical error during database seeding: {e}")


if __name__ == "__main__":
    create_database_tables()