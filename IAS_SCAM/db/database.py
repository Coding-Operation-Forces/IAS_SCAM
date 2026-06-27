import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Ініціалізація двигуна SQLAlchemy для роботи з PostgreSQL
engine = create_engine(DATABASE_URL)

# Налаштування фабрики сесій для взаємодії з транзакціями бази даних
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Декларативна база для побудови ORM-моделей
Base = declarative_base()