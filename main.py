import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from login_window import LoginWindow


def main():
    app = QApplication(sys.argv)

    # Запуск вікна авторизації
    login_window = LoginWindow()
    login_window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()