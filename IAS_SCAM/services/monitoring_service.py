# services/monitoring_service.py
import os
import shutil
import datetime
from dotenv import load_dotenv
from sqlalchemy import text, create_engine
from sqlalchemy.schema import CreateTable
from db.database import engine, Base, SessionLocal
import db.models  # Імпортуємо моделі для реєстрації в Base

# Завантажуємо змінні оточення для доступу до SHARED_BACKUP_CONFIG
load_dotenv()

# Визначаємо шлях до мережевого конфігураційного файлу
CONFIG_PATH = os.getenv("SHARED_BACKUP_CONFIG", "backup_settings.json")
CONFIG_DIR = os.path.dirname(CONFIG_PATH)

# Якщо шлях відносний або порожній, використовуємо поточну робочу директорію
if not CONFIG_DIR:
    CONFIG_DIR = os.path.abspath(".")

# Файл статусу бекапу тепер зберігається в спільній папці BackSet на сервері!
# Це дозволить колегам бачити реальний час бекапу, проведеного на сервері
STATUS_FILE = os.path.join(CONFIG_DIR, "backups_status.txt")


def check_db_status() -> bool:
    """
    Глибока перевірка: не просто підключення, а виконання
    тестового запиту для підтвердження активності СУБД.
    """
    try:
        # Встановлюємо короткий таймаут (2 секунди), щоб інтерфейс не зависав,
        # якщо служба дійсно повністю вимкнена.
        with engine.connect().execution_options(timeout=2.0) as connection:
            # Виконуємо легкий запит, який поверне назву поточної бази
            result = connection.execute(text("SELECT current_database();")).fetchone()
            if result and result[0] == "skam_db":
                return True
            return False
    except Exception:
        return False


def get_disk_usage_percent() -> int:
    """Повертає реальний відсоток зайнятого місця на диску СЕРВЕРА (де розташована папка BackSet)."""
    try:
        # Перевіряємо диск сервера за мережевим шляхом CONFIG_DIR
        total, used, free = shutil.disk_usage(CONFIG_DIR)
        return int((used / total) * 100)
    except Exception:
        return 0
def get_disk_free_kb() -> int:
    """Повертає точний обсяг вільного місця на диску СЕРВЕРА в кілобайтах (КБ)."""
    try:
        # Зчитуємо байти з сервера та переводимо в КБ (ділимо на 1024)
        total, used, free = shutil.disk_usage(CONFIG_DIR)
        return int(free / 1024)
    except Exception:
        return 0


def get_last_backup_time() -> str:
    """Зчитує дату й час останнього бекапу зі спільного статус-файлу."""
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return "Ще не проводився"


def create_system_backup() -> tuple[bool, str]:
    """Генерує повний SQL-дамп (структура + ВСІ ДАНІ) та зберігає його на сервері."""
    if not check_db_status():
        return False, "Неможливо створити бекап: відсутнє підключення до БД!"

    try:
        # Папка backups тепер створюється безпосередньо всередині спільної папки BackSet на сервері!
        backup_dir = os.path.join(CONFIG_DIR, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"backup_full_{timestamp}.sql"
        file_path = os.path.join(backup_dir, file_name)

        # Визначаємо правильний топологічний порядок таблиць (захист від Foreign Key помилок)
        ordered_tables = Base.metadata.sorted_tables

        # 1. ГЕНЕРУЄМО СТРУКТУРУ ТАБЛИЦЬ (CREATE TABLE)
        schema_statements = []
        for table in ordered_tables:
            # Компілюємо DDL під діалект PostgreSQL
            create_table_sql = str(CreateTable(table).compile(dialect=engine.dialect)).strip()
            schema_statements.append(f"{create_table_sql};")

        # 2. ВИВАНТАЖУЄМО ДАНІ З КОЖНОЇ ТАБЛИЦЬ (INSERT INTO)
        data_statements = []

        with SessionLocal() as session:
            for table in ordered_tables:
                table_name = table.name
                columns = [col.name for col in table.columns]
                columns_str = ", ".join([f'"{c}"' for c in columns])  # Екрануємо колонки

                # Читаємо всі рядки з бази
                result = session.execute(text(f"SELECT * FROM public.{table_name}")).fetchall()

                if result:
                    data_statements.append(f"-- Дані таблиці: public.{table_name}")
                    for row in result:
                        values = []
                        for val in row:
                            if val is None:
                                values.append("NULL")
                            elif isinstance(val, (int, float)):
                                values.append(str(val))
                            elif isinstance(val, bool):
                                values.append("TRUE" if val else "FALSE")
                            elif isinstance(val, (datetime.datetime, datetime.date)):
                                values.append(f"'{val.isoformat()}'")
                            else:
                                # Безпечно екрануємо одинарні лапки для SQL тексту
                                safe_val = str(val).replace("'", "''")
                                values.append(f"'{safe_val}'")

                        values_str = ", ".join(values)
                        data_statements.append(
                            f"INSERT INTO public.{table_name} ({columns_str}) VALUES ({values_str});")
                    data_statements.append("")  # Розділювач між таблицями

        # 3. ЗАПИСУЄМО ВСЕ У ФАЙЛ .SQL
        formatted_now_text = now.strftime("%d.%m.%Y %H:%M:%S")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"-- ==================================================\n")
            f.write(f"-- ПОВНИЙ БЕКАП БАЗИ ДАНИХ СКАМ (СТРУКТУРА + ДАНІ)\n")
            f.write(f"-- Створено: {formatted_now_text}\n")
            f.write(f"-- Сумісність: pgAdmin 4 / PostgreSQL Query Tool\n")
            f.write(f"-- ==================================================\n\n")

            f.write(f"-- --------------------------------------------------\n")
            f.write(f"-- ЧАСТИНА 1: СТВОРЕННЯ СХЕМИ ТА ТАБЛИЦЬ\n")
            f.write(f"-- --------------------------------------------------\n\n")
            # Спочатку додаємо видалення таблиць, якщо вони вже існують при відновленні (чистий запуск)
            for table in reversed(ordered_tables):
                f.write(f"DROP TABLE IF EXISTS public.{table.name} CASCADE;\n")
            f.write("\n")

            for statement in schema_statements:
                f.write(f"{statement}\n\n")

            f.write(f"\n-- --------------------------------------------------\n")
            f.write(f"-- ЧАСТИНА 2: НАПОВНЕННЯ ТАБЛИЦЬ ДАНИМИ\n")
            f.write(f"-- --------------------------------------------------\n\n")
            for statement in data_statements:
                f.write(f"{statement}\n")

        # Зберігаємо мітку часу в спільний статус-файл
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            f.write(formatted_now_text)

        return True, f"Повний бекап успішно збережено на сервері: 'BackSet/backups/{file_name}'"
    except Exception as e:
        return False, f"Помилка генерації повного бекапу: {str(e)}"