import os
import shutil
import datetime
from dotenv import load_dotenv
from sqlalchemy import text, create_engine
from sqlalchemy.schema import CreateTable
from db.database import engine, Base, SessionLocal

load_dotenv()

CONFIG_PATH = os.getenv("SHARED_BACKUP_CONFIG", "backup_settings.json")
CONFIG_DIR = os.path.dirname(CONFIG_PATH)

if not CONFIG_DIR:
    CONFIG_DIR = os.path.abspath(".")

STATUS_FILE = os.path.join(CONFIG_DIR, "backups_status.txt")

def check_db_status() -> bool:
    """Виконання тестового низькорівневого запиту для перевірки працездатності СУБД."""
    try:
        with engine.connect().execution_options(timeout=2.0) as connection:
            result = connection.execute(text("SELECT current_database();")).fetchone()
            if result and result[0] == "skam_db":
                return True
            return False
    except Exception:
        return False

def get_disk_usage_percent() -> int:
    """Вимірювання відносного відсотка заповненості дискового простору сервера."""
    try:
        total, used, free = shutil.disk_usage(CONFIG_DIR)
        return int((used / total) * 100)
    except Exception:
        return 0

def get_disk_free_kb() -> int:
    """Вимірювання обсягу доступного вільного місця на сервері в кілобайтах."""
    try:
        total, used, free = shutil.disk_usage(CONFIG_DIR)
        return int(free / 1024)
    except Exception:
        return 0

def get_last_backup_time() -> str:
    """Зчитування часової мітки проведення останнього бекапу з лог-файлу."""
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return "Ще не проводився"

def create_system_backup() -> tuple[bool, str]:
    """Генерація комплексного SQL-дампу (схема даних + записи) у сховище сервера."""
    if not check_db_status():
        return False, "Неможливо створити бекап: відсутнє підключення до БД!"

    try:
        backup_dir = os.path.join(CONFIG_DIR, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"backup_full_{timestamp}.sql"
        file_path = os.path.join(backup_dir, file_name)

        ordered_tables = Base.metadata.sorted_tables

        schema_statements = []
        for table in ordered_tables:
            create_table_sql = str(CreateTable(table).compile(dialect=engine.dialect)).strip()
            schema_statements.append(f"{create_table_sql};")

        data_statements = []

        with SessionLocal() as session:
            for table in ordered_tables:
                table_name = table.name
                columns = [col.name for col in table.columns]
                columns_str = ", ".join([f'"{c}"' for c in columns])

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
                                safe_val = str(val).replace("'", "''")
                                values.append(f"'{safe_val}'")

                        values_str = ", ".join(values)
                        data_statements.append(
                            f"INSERT INTO public.{table_name} ({columns_str}) VALUES ({values_str});")
                    data_statements.append("")

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

        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            f.write(formatted_now_text)

        return True, f"Повний бекап успішно збережено на сервері: 'BackSet/backups/{file_name}'"
    except Exception as e:
        return False, f"Помилка генерації повного бекапу: {str(e)}"