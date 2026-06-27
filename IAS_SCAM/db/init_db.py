from db.database import engine, Base

def create_database_tables():
    print("Створення таблиць у PostgreSQL...")
    # Автоматична генерація таблиць на основі метаданих імпортованих моделей
    Base.metadata.create_all(bind=engine)
    print("Базу даних успішно створено!")

if __name__ == "__main__":
    create_database_tables()