import sys
import os
import traceback
import ctypes
from ctypes import wintypes
from dotenv import load_dotenv
from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtWidgets import QApplication, QSplashScreen, QProgressBar
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
from config import APP_VERSION

# Завантажуємо змінні з локального файлу .env на самому початку
load_dotenv()

# --- ЦЕЙ РЯДОК МАЄ БУТИ ТУТ, ДО СТВОРЕННЯ QAPPLICATION ---
os.environ["QT_API"] = "pyqt6"
# Додаткові налаштування для виведення внутрішніх логів Qt в консоль
os.environ["QT_FORCE_STDERR_LOGGING"] = "1"

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    pass

from ui.login_window import LoginWindow


# =====================================================================
#  АВТОМАТИЧНА АВТОРИЗАЦІЯ МЕРЕЖЕВОЇ ПАПКИ НА СЕРВЕРІ ЧЕРЕЗ WINDOWS API
# =====================================================================
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
    """Безпечно та автоматично авторизує клієнта в мережевому сховищі сервера"""
    if os.name != 'nt':  # Якщо це не Windows (наприклад, Linux), пропускаємо
        return

    # Динамічно зчитуємо зашифровані змінні з локального .env
    remote_path = os.getenv("NET_REMOTE_PATH")
    username = os.getenv("NET_USERNAME")
    password = os.getenv("NET_PASSWORD")

    # Якщо файлу .env немає або параметри порожні, перериваємо процес безпечно
    if not all([remote_path, username, password]):
        print("[NET] Попередження: Мережеві облікові дані відсутні або неповні у .env")
        return

    nr = NETRESOURCE()
    nr.dwType = 1  # RESOURCETYPE_DISK (Спільна мережева папка)
    nr.lpRemoteName = remote_path

    # Викликаємо функцію Windows mpr.dll
    mpr = ctypes.WinDLL('mpr', use_last_error=True)

    # CONNECT_TEMPORARY (0x4) — з'єднання існує, поки активний процес додатка
    result = mpr.WNetAddConnection2W(ctypes.byref(nr), password, username, 0x4)

    if result == 0:
        print(f"[NET] Успішно підключено до безпечного мережевого сховища сервера.")
    elif result == 1219:
        print("[NET] Мережева сесія вже була успішно авторизована раніше.")
    else:
        print(f"[NET] Попередження: Код мережевої відповіді системи Windows: {result}")


# =====================================================================
#  МАГІЧНИЙ ДЕБАГЕР: ПЕРЕХОПЛЮВАЧ КРИТИЧНИХ ПОМИЛОК EVENT LOOP PYQT
# =====================================================================
def qt_exception_hook(exctype, value, tb):
    """
    Примусово зупиняє «мовчазне» падіння 0xC0000409 і виводить у консоль
    повний шлях, назву файлу та номери рядків, де саме стався збій.
    """
    print("\n" + "=" * 80)
    print(" 🚨 КРИТИЧНА ПОМИЛКА ЯДРА PYQT ПЕРЕХОПЛЕНА ДЕБАГЕРОМ 🚨")
    print("=" * 80)
    traceback.print_exception(exctype, value, tb)
    print("=" * 80 + "\n")
    sys.__excepthook__(exctype, value, tb)
    sys.exit(1)


class DarkSplashScreen(QSplashScreen):
    """Класична корпоративна заставка, у ТЕМНІЙ темі."""

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


def main():
    # Підключаємо наш дебаг-хук перед запуском додатка
    sys.excepthook = qt_exception_hook

    # Автоматично піднімаємо мережеве з'єднання для клієнтів (персоналу)
    auto_connect_shared_folder()

    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "ui", "icon.png")

    splash = DarkSplashScreen(icon_path, APP_VERSION)
    splash.show()

    QTimer.singleShot(100, lambda: splash.update_progress(10, "Ініціалізація ядра системи..."))
    QTimer.singleShot(700, lambda: splash.update_progress(40, "Встановлення з'єднання з базою даних..."))
    QTimer.singleShot(1400, lambda: splash.update_progress(70, "Завантаження довідників та модулів..."))
    QTimer.singleShot(2100, lambda: splash.update_progress(100, "Запуск інтерфейсу..."))

    main_window = LoginWindow()
    QTimer.singleShot(2500, lambda: (main_window.show(), splash.finish(main_window)))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()