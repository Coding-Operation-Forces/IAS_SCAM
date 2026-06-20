import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Завантажуємо змінні з файлу .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Створюємо рушій для зв'язку з PostgreSQL
engine = create_engine(DATABASE_URL)

# Створюємо фабрику сесій для виконання запитів
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовий клас, від якого будуть успадковуватися всі моделі
Base = declarative_base()