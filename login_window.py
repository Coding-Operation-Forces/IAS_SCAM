import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QFrame)
from PyQt6.QtCore import Qt, QPropertyAnimation
from PyQt6.QtGui import QPixmap, QIcon


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.is_dark_theme = True
        
        # МАГІЯ ТУТ: Визначаємо абсолютний шлях до папки, де лежить цей файл (тобто до папки UI)
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.icon_path = os.path.join(self.base_dir, "icon.png")
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Авторизація")
        # Використовуємо абсолютний шлях
        self.setWindowIcon(QIcon(self.icon_path))
        self.resize(400, 500)
        self.setObjectName("login_window")

        # Головний макет
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 30)
        main_layout.setSpacing(20)

        # Верхня панель з кнопкою зміни теми
        top_layout = QHBoxLayout()
        top_layout.addStretch()
        self.theme_btn = QPushButton("🌞 Світла тема")
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.clicked.connect(self.animate_theme_toggle)
        top_layout.addWidget(self.theme_btn)
        main_layout.addLayout(top_layout)

        main_layout.addStretch()

        # Логотип
        self.logo = QLabel()
        # Використовуємо абсолютний шлях для QPixmap
        pixmap = QPixmap(self.icon_path)
        if not pixmap.isNull():
            self.logo.setPixmap(
                pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.logo.setText("🏢")
            self.logo.setStyleSheet("font-size: 80px;")
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.logo)

        # Заголовок
        self.title_lbl = QLabel("Вхід у систему")
        self.title_lbl.setObjectName("title_label")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.title_lbl)

        # Форма вводу (Тільки логін та пароль)
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Логін або Email")
        self.login_input.setFixedHeight(45)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(45)

        main_layout.addWidget(self.login_input)
        main_layout.addWidget(self.password_input)

        main_layout.addSpacing(10)

        # Кнопка входу
        self.login_btn = QPushButton("Увійти")
        self.login_btn.setProperty("btn_type", "primary")
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setFixedHeight(50)
        self.login_btn.clicked.connect(self.perform_login)
        main_layout.addWidget(self.login_btn)

        main_layout.addStretch()

        # Застосовуємо тему при запуску
        self.apply_theme()

    # ==========================================
    # ЛОГІКА ВХОДУ (РОУТИНГ)
    # ==========================================
    def perform_login(self):
        login_text = self.login_input.text().lower()

        # Тимчасова логіка маршрутизації (до підключення бази даних)
        if "admin" in login_text:
            from arm_admin import ArmAdminWindow
            self.main_window = ArmAdminWindow()
        elif "manager" in login_text:
            from arm_manager import ArmManagerWindow
            self.main_window = ArmManagerWindow()
        else:
            from arm_worker import ArmWorkerWindow
            self.main_window = ArmWorkerWindow()

        # Передаємо поточну тему у нове вікно, щоб не було блимання кольорів
        if not self.is_dark_theme:
            self.main_window.is_dark_theme = False
            self.main_window.theme_btn.setText("🌙 Темна тема")
            self.main_window.apply_theme()

        self.main_window.show()
        self.close()

    # ==========================================
    # ЛОГІКА ЗМІНИ ТЕМИ
    # ==========================================
    def animate_theme_toggle(self):
        self.fade_out_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_anim.setDuration(200)
        self.fade_out_anim.setStartValue(1.0)
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.finished.connect(self.toggle_theme)
        self.fade_out_anim.start()

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        self.theme_btn.setText("🌞 Світла тема" if self.is_dark_theme else "🌙 Темна тема")
        self.apply_theme()

        self.fade_in_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_anim.setDuration(250)
        self.fade_in_anim.setStartValue(0.0)
        self.fade_in_anim.setEndValue(1.0)
        self.fade_in_anim.start()

    def apply_theme(self):
        if self.is_dark_theme:
            bg_color = "#1E1E2E"
            text_col = "#F8F8F2"
            input_bg = "#313244"
            border_col = "#44475A"
            accent_col = "#8B5CF6"
            placeholder_col = "rgba(205, 214, 244, 100)"
            btn_hover = "#44475A"
        else:
            bg_color = "#F8F9FA"
            text_col = "#2C3E50"
            input_bg = "#FFFFFF"
            border_col = "#DEE2E6"
            accent_col = "#8B5CF6"
            placeholder_col = "rgba(44, 62, 80, 100)"
            btn_hover = "#CED4DA"

        global_style = f"""
            QWidget#login_window {{ background-color: {bg_color}; font-family: 'Segoe UI', sans-serif; }}
            QLabel {{ color: {text_col}; }}
            QLabel#title_label {{ font-size: 26px; font-weight: bold; margin-bottom: 10px; color: {text_col}; }}

            /* Поля вводу */
            QLineEdit {{ 
                background-color: {input_bg}; color: {text_col}; 
                border: 2px solid {border_col}; border-radius: 6px; 
                padding: 6px 12px; font-size: 15px; 
            }}
            QLineEdit:focus {{ border: 2px solid {accent_col}; }}
            QLineEdit::placeholder {{ color: {placeholder_col}; }}

            /* Головна кнопка */
            QPushButton[btn_type="primary"] {{ 
                background-color: {accent_col}; color: #FFFFFF; 
                font-weight: bold; font-size: 16px; border-radius: 6px; border: none; 
            }}
            QPushButton[btn_type="primary"]:hover {{ background-color: #7C3AED; }}
        """
        self.setStyleSheet(global_style)

        # Стиль кнопки перемикання теми
        self.theme_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {text_col}; font-weight: 500; font-size: 13px; padding: 8px 12px; border-radius: 4px; border: none; }}
            QPushButton:hover {{ background-color: {btn_hover}; }}
        """)