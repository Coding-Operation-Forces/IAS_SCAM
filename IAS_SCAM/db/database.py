from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from PyQt6.QtCore import QSettings
import keyring

settings = QSettings("COF", "IAS_SCAM")

db_user = settings.value("DB_USER", "postgres")
db_host = settings.value("DB_HOST", "localhost")
db_port = settings.value("DB_PORT", "5432")
db_name = settings.value("DB_NAME", "skam_db")

db_pass = keyring.get_password("IAS_SCAM_DB", db_user)

if not db_pass:
    db_pass = ""

DATABASE_URL = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

print(f"[DB] Використовується рядок підключення: {DATABASE_URL.split('@')[-1]} (пароль приховано)")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()