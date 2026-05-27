from database import engine, Base
# Обов'язково імпортуємо моделі, щоб SQLAlchemy знала про їхнє існування
import models

def create_database_tables():
    print("Створення таблиць у PostgreSQL...")
    # Цей рядок автоматично знаходить всі класи, що успадкували Base,
    # і створює відповідні таблиці в базі даних в правильному порядку!
    Base.metadata.create_all(bind=engine)
    print("Базу даних успішно створено!")

if __name__ == "__main__":
    create_database_tables()