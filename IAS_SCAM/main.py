import sys
import os

import traceback
import ctypes
from ctypes import wintypes
from dotenv import load_dotenv
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtWidgets import QApplication, QSplashScreen, QProgressBar
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
from config import APP_VERSION

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

os.environ["QT_API"] = "pyqt6"
os.environ["QT_FORCE_STDERR_LOGGING"] = "1"

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    pass

from ui.login_window import LoginWindow


class NETRESOURCE(ctypes.Structure):
    """Структура Windows API для ідентифікації мережевого ресурсу."""
    _fields_ = [
        ('dwScope', wintypes.DWORD),
        ('dwType', wintypes.DWORD),
        ('dwDisplayType', wintypes.DWORD),
        ('dwUsage', wintypes.DWORD),
        ('lpLocalName', wintypes.LPWSTR),
        ('lpRemoteName', wintypes.LPWSTR),
        ('lpComment', wintypes.LPWSTR),
        ('lpProvider', wintypes.LPWSTR)
    ]


def auto_connect_shared_folder():
    """Автоматичне монтування віддаленого каталогу за допомогою функції WNetAddConnection2W."""
    if os.name != 'nt':
        return

    remote_path = os.getenv("NET_REMOTE_PATH")
    username = os.getenv("NET_USERNAME")
    password = os.getenv("NET_PASSWORD")

    if not all([remote_path, username, password]):
        print("[NET] Попередження: Мережеві облікові дані відсутні або неповні у .env")
        return

    nr = NETRESOURCE()
    nr.dwType = 1
    nr.lpRemoteName = remote_path

    mpr = ctypes.WinDLL('mpr', use_last_error=True)
    result = mpr.WNetAddConnection2W(ctypes.byref(nr), password, username, 0x4)  # CONNECT_TEMPORARY

    if result == 0:
        print(f"[NET] Успішно підключено до мережевого сховища.")
    elif result == 1219:
        print("[NET] Мережева сесія вже була авторизована раніше.")
    else:
        print(f"[NET] Попередження: Код помилки Windows API: {result}")


def qt_exception_hook(exctype, value, tb):
    """Перехоплювач необроблених винятків для забезпечення коректного логування збоїв Event Loop."""
    print("\n" + "=" * 80)
    print(" КРИТИЧНА ПОМИЛКА ЯДРА PYQT ")
    print("=" * 80)
    traceback.print_exception(exctype, value, tb)
    print("=" * 80 + "\n")
    sys.__excepthook__(exctype, value, tb)
    sys.exit(1)


class DarkSplashScreen(QSplashScreen):
    """Графічний екран заставки (Splash Screen) із вбудованим індикатором прогресу ініціалізації."""

    def __init__(self, icon_path, version):
        width, height = 560, 320
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor("#1E1E2E"))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(0, 0, width, 4, QColor("#8B5CF6"))
        painter.fillRect(0, height - 30, width, 30, QColor("#181825"))

        logo = QPixmap(icon_path)
        if not logo.isNull():
            logo = logo.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            painter.drawPixmap(40, 80, logo)

        painter.setPen(QColor("#F8F8F2"))
        painter.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        painter.drawText(QRect(180, 70, 360, 100), Qt.AlignmentFlag.AlignLeft, "Інформаційно-аналітична\nсистема СКАМ")

        painter.setPen(QColor("#A6ADC8"))
        painter.setFont(QFont("Segoe UI", 12))
        painter.drawText(QRect(180, 170, 360, 30), Qt.AlignmentFlag.AlignLeft, f"Версія комплексу: {version}")

        painter.end()
        super().__init__(pixmap)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(0, height - 34, width, 4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            "QProgressBar { border: none; background-color: transparent; } QProgressBar::chunk { background-color: #8B5CF6; }")

    def update_progress(self, value, message):
        """Оновлення прогрес-бару із примусовим викликом циклу обробки подій вікна."""
        self.progress_bar.setValue(value)
        self.showMessage(f"  {message}", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft, QColor("#F8F8F2"))
        QApplication.processEvents()


def main():
    sys.excepthook = qt_exception_hook

    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "ui", "icon.png")

    splash = DarkSplashScreen(icon_path, APP_VERSION)
    splash.show()

    splash.update_progress(15, "Ініціалізація підсистем середовища...")

    splash.update_progress(35, "Авторизація доступу до файлового сервера...")
    auto_connect_shared_folder()
    
    splash.update_progress(60, "Валідація структури та первинних даних БД...")
    try:
        from db.init_db import create_database_tables
        create_database_tables()
    except Exception as db_err:
        print(f"[INIT] Попередження під час автоініціалізації СУБД: {db_err}")

    splash.update_progress(80, "Перевірка доступності сервера PostgreSQL...")
    try:
        from services.monitoring_service import check_db_status
        if check_db_status():
            print("[INIT] З'єднання з базою даних успішно встановлено.")
        else:
            print("[INIT] Попередження: База даних недоступна.")
    except Exception as e:
        print(f"[INIT] Помилка під час верифікації зв'язку з БД: {e}")

    splash.update_progress(95, "Кешування статичних довідників та мапінгів...")
    try:
        from services.worker_service import get_issue_mapping
        get_issue_mapping()
    except Exception as e:
        print(f"[INIT] Помилка попереднього завантаження довідників: {e}")

    splash.update_progress(100, "Підготовка інтерфейсу користувача...")

    main_window = LoginWindow()
    main_window.show()
    splash.finish(main_window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()