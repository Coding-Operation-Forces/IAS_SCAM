import sys
import os
import traceback
import ctypes
from ctypes import wintypes
import winreg 
import keyring
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt, QRect, QSettings
from PyQt6.QtWidgets import QApplication, QSplashScreen, QProgressBar
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
from config import APP_VERSION

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.environ["QT_API"] = "pyqt6"
os.environ["QT_FORCE_STDERR_LOGGING"] = "1"

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    pass

from ui.login_window import LoginWindow

class NETRESOURCE(ctypes.Structure):
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
    if os.name != 'nt':
        return

    settings = QSettings("COF", "IAS_SCAM")
    remote_path = settings.value("NET_REMOTE_PATH")
    username = settings.value("NET_USERNAME")

    if not remote_path or not username:
        print("[NET] Попередження: Мережеві облікові дані відсутні у налаштуваннях.")
        return
        
    password = keyring.get_password("IAS_SCAM_NET", username)

    if not password:
        print("[NET] Попередження: Мережевий пароль відсутній у системному сховищі.")
        return

    nr = NETRESOURCE()
    nr.dwType = 1
    nr.lpRemoteName = remote_path

    mpr = ctypes.WinDLL('mpr', use_last_error=True)
    result = mpr.WNetAddConnection2W(ctypes.byref(nr), password, username, 0x4) 

    if result == 0:
        print(f"[NET] Успішно підключено до мережевого сховища.")
    elif result == 1219:
        print("[NET] Мережева сесія вже була авторизована раніше.")
    else:
        print(f"[NET] Попередження: Код помилки Windows API: {result}")

def qt_exception_hook(exctype, value, tb):
    print("\n" + "=" * 80)
    print(" КРИТИЧНА ПОМИЛКА ЯДРА PYQT ")
    print("=" * 80)
    traceback.print_exception(exctype, value, tb)
    print("=" * 80 + "\n")
    sys.__excepthook__(exctype, value, tb)
    sys.exit(1)

class DarkSplashScreen(QSplashScreen):
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
        self.progress_bar.setValue(value)
        self.showMessage(f"  {message}", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft, QColor("#F8F8F2"))
        QApplication.processEvents()

def migrate_secrets_from_installer():
    if os.name != 'nt':
        return

    key_path = r"Software\COF\IAS_SCAM\TempSecrets"
    try:
        registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        
        db_pass, _ = winreg.QueryValueEx(registry_key, "DB_PASS")
        net_pass, _ = winreg.QueryValueEx(registry_key, "NET_PASS")
        winreg.CloseKey(registry_key)
        
        settings = QSettings("COF", "IAS_SCAM")
        db_user = settings.value("DB_USER")
        net_user = settings.value("NET_USERNAME")
        
        if db_user and db_pass:
            keyring.set_password("IAS_SCAM_DB", db_user, db_pass)
        if net_user and net_pass:
            keyring.set_password("IAS_SCAM_NET", net_user, net_pass)
            
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        print("[INIT] Міграція паролів з інсталятора до keyring пройшла успішно.")
        
    except FileNotFoundError:
        pass 
    except Exception as e:
        print(f"[INIT] Помилка міграції паролів: {e}")

def check_and_load_config():
    """Перевіряє, чи існують налаштування, створені інсталятором."""
    settings = QSettings("COF", "IAS_SCAM")
    db_host = settings.value("DB_HOST")
    
    if not db_host:
        print("[INIT] Критична помилка: Відсутні конфігураційні дані системи.")

        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Icon.Critical)
        error_box.setWindowTitle("Помилка ініціалізації")
        error_box.setText("Відсутні налаштування підключення!")
        error_box.setInformativeText("Схоже, програма була запущена без встановлення або конфігурацію пошкоджено.\nБудь ласка, запустіть офіційний інсталятор (Setup) системи СКАМ.")
        error_box.exec()
        
        sys.exit(1)

def main():
    sys.excepthook = qt_exception_hook
    
    migrate_secrets_from_installer()

    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    check_and_load_config()

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