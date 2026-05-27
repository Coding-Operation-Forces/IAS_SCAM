import sys
import os
from PyQt6.QtCore import Qt

# --- ЦЕЙ РЯДОК МАЄ БУТИ ТУТ, ДО СТВОРЕННЯ QAPPLICATION ---
# Встановлюємо атрибут для сумісності з QtWebEngine
os.environ["QT_API"] =  "pyqt6"
from PyQt6.QtWidgets import QApplication, QSplashScreen, QProgressBar
from PyQt6.QtCore import QTimer, QRect
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont

# Тепер можна безпечно імпортувати інші компоненти
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView # Тестуємо доступність
except ImportError:
    pass

from login_window import LoginWindow

# Встановлюємо атрибут для Shared OpenGL Context перед створенням QApplication
QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

class DarkSplashScreen(QSplashScreen):
    """
    Класична корпоративна заставка, у ТЕМНІЙ темі.
    """
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
        painter.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        painter.drawText(QRect(190, 80, 350, 80), Qt.AlignmentFlag.AlignLeft, "Інформаційно-аналітична\nсистема СКАМ")

        painter.setPen(QColor("#A6ADC8"))
        painter.setFont(QFont("Segoe UI", 12))
        painter.drawText(QRect(190, 170, 350, 30), Qt.AlignmentFlag.AlignLeft, f"Версія комплексу: {version}")

        painter.end()
        super().__init__(pixmap)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(0, height - 34, width, 4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { border: none; background-color: transparent; } QProgressBar::chunk { background-color: #8B5CF6; }")

    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.showMessage(f"  {message}", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft, QColor("#F8F8F2"))
        QApplication.processEvents()

def main():
    # Створюємо об'єкт програми після налаштування атрибутів
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "icon.png")

    splash = DarkSplashScreen(icon_path, "1.0.11")
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