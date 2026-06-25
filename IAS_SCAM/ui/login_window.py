import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QFrame, QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, QPropertyAnimation, QTimer
from PyQt6.QtGui import QPixmap, QIcon
from services.auth_service import authenticate_user


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.is_dark_theme = True
        self.failed_attempts = 0
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.icon_path = os.path.join(self.base_dir, "icon.png")
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Авторизація")
        self.setWindowIcon(QIcon(self.icon_path))
        self.resize(400, 500)
        self.setObjectName("login_window")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 30)
        main_layout.setSpacing(20)

        top_layout = QHBoxLayout()
        top_layout.addStretch()
        self.theme_btn = QPushButton("🌞 Світла тема")
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.clicked.connect(self.animate_theme_toggle)
        top_layout.addWidget(self.theme_btn)
        main_layout.addLayout(top_layout)

        main_layout.addStretch()

        self.logo = QLabel()
        pixmap = QPixmap(self.icon_path)
        if not pixmap.isNull():
            self.logo.setPixmap(
                pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.logo.setText("🏢")
            self.logo.setStyleSheet("font-size: 80px;")
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.logo)

        self.title_lbl = QLabel("Вхід у систему")
        self.title_lbl.setObjectName("title_label")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.title_lbl)

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

        self.login_btn = QPushButton("Увійти")
        self.login_btn.setProperty("btn_type", "primary")
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setFixedHeight(50)
        self.login_btn.clicked.connect(self.perform_login)
        main_layout.addWidget(self.login_btn)

        main_layout.addStretch()
        self.apply_theme()

    def perform_login(self):
        # Якщо локальний таймер блокування ще активний — ігноруємо клік
        if hasattr(self, 'lock_seconds_left') and self.lock_seconds_left > 0:
            return

        login_text = self.login_input.text().strip()
        password_text = self.password_input.text().strip()

        if not login_text or not password_text:
            QMessageBox.warning(self, "Помилка", "Будь ласка, введіть логін та пароль.")
            return

        # Запитуємо перевірку у сервера
        response = authenticate_user(login_text, password_text)

        if response["status"] == "success":
            self.failed_attempts = 0
            self.user_data = response["data"]
            self.show_loading_overlay()

        elif response["status"] == "locked":
            QMessageBox.critical(self, "Безпека системи", response["message"])

        else:
            # Обробка звичайної помилки (невірний пароль АБО неіснуючий логін)
            self.failed_attempts += 1

            # Якщо користувач помилився 3 рази підряд (неважливо, з існуючим чи вигаданим логіном)
            if self.failed_attempts >= 3:
                self.lock_client(60)  # Блокуємо інтерфейс на 1 хвилину
            else:
                # Виводимо повідомлення від сервера, додаючи кількість спроб, що залишилися
                current_msg = response["message"]
                if "Залишилось спроб" not in current_msg:
                    current_msg += f"\nЗалишилось спроб до блокування клієнта: {3 - self.failed_attempts}"
                QMessageBox.critical(self, "Відмова у доступі", current_msg)

    def lock_client(self, seconds):
        """Тимчасове блокування інтерфейсу на стороні клієнта."""
        self.lock_seconds_left = seconds
        self.login_input.setEnabled(False)
        self.password_input.setEnabled(False)
        self.login_btn.setEnabled(False)

        if not hasattr(self, 'lbl_lock_warning'):
            self.lbl_lock_warning = QLabel(self)
            self.lbl_lock_warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lbl_lock_warning.setStyleSheet("color: #FF5555; font-weight: bold;")
            self.layout().insertWidget(self.layout().count() - 2, self.lbl_lock_warning)

        self.lbl_lock_warning.setText(f"Перевищено ліміт спроб! Доступ заблоковано на {self.lock_seconds_left} сек.")

        self.lock_timer = QTimer(self)
        self.lock_timer.timeout.connect(self.update_lock_countdown)
        self.lock_timer.start(1000)

        QMessageBox.critical(self, "Безпека",
                             "Доступ тимчасово заблоковано на 1 хвилину через 3 помилкові спроби входу!")

    def update_lock_countdown(self):
        self.lock_seconds_left -= 1
        if self.lock_seconds_left <= 0:
            self.lock_timer.stop()
            self.failed_attempts = 0
            self.login_input.setEnabled(True)
            self.password_input.setEnabled(True)
            self.login_btn.setEnabled(True)
            self.lbl_lock_warning.setText("")
            self.password_input.clear()
        else:
            self.lbl_lock_warning.setText(
                f"Перевищено ліміт спроб! Доступ заблоковано на {self.lock_seconds_left} сек.")

    # ==========================================
    # ГЛОБАЛЬНИЙ ЕКРАН ЗАВАНТАЖЕННЯ (ПЕРЕНЕСЕНО СЮДИ)
    # ==========================================
    def show_loading_overlay(self):
        # Блокуємо всі кнопки, щоб користувач не натискав їх під час завантаження
        self.login_input.setEnabled(False)
        self.password_input.setEnabled(False)
        self.login_btn.setEnabled(False)
        self.theme_btn.setEnabled(False)

        self.loading_overlay = QWidget(self)
        bg_col = "#1E1E2E" if self.is_dark_theme else "#F8F9FA"
        self.loading_overlay.setStyleSheet(f"background-color: {bg_col};")
        self.loading_overlay.setGeometry(0, 0, self.width(), self.height())
        
        v_lay = QVBoxLayout(self.loading_overlay)
        v_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v_lay.setSpacing(15)
        
        text_color = '#8B5CF6'
        bar_bg = '#282A36' if self.is_dark_theme else '#E9ECEF'
        border_col = '#44475A' if self.is_dark_theme else '#DEE2E6'
        
        self.loading_lbl = QLabel("Авторизація успішна.\nПідключення до бази даних...")
        self.loading_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {text_color};")
        
        self.p_bar = QProgressBar()
        self.p_bar.setFixedWidth(300)
        self.p_bar.setStyleSheet(f"""
            QProgressBar {{ border: 2px solid {border_col}; border-radius: 6px; text-align: center; background-color: {bar_bg}; color: transparent; }}
            QProgressBar::chunk {{ background-color: {text_color}; border-radius: 4px; }}
        """)
        
        v_lay.addWidget(self.loading_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        v_lay.addWidget(self.p_bar, alignment=Qt.AlignmentFlag.AlignCenter)
        self.loading_overlay.show()
        self.loading_overlay.raise_()
        
        self.loading_step = 0
        self.loading_timer = QTimer(self)
        self.loading_timer.timeout.connect(self.perform_loading_ticks)
        self.loading_timer.start(35) # Швидкість заповнення

    def perform_loading_ticks(self):
        self.loading_step += 4
        self.p_bar.setValue(self.loading_step)
        
        if self.loading_step == 40:
            self.loading_lbl.setText("Ініціалізація робочого середовища...")
            self.instantiate_main_window()
        elif self.loading_step == 80:
            self.loading_lbl.setText("Підготовка інтерфейсу...")
        elif self.loading_step >= 100:
            self.loading_timer.stop()
            
            # Застосовуємо тему до створеного вікна
            if not self.is_dark_theme:
                self.main_window.is_dark_theme = False
                if hasattr(self.main_window, 'theme_btn'):
                    self.main_window.theme_btn.setText("🌙 Темна тема")
                self.main_window.apply_theme()
            
            # ЗМІНЕНО: Тепер саме робочий інтерфейс АРМ відкривається на весь екран!
            self.main_window.showMaximized()
            self.close()

    def instantiate_main_window(self):
        """Створює екземпляр АРМ-вікна відповідно до ролі користувача"""
        role_id = self.user_data["role_id"] if isinstance(self.user_data, dict) else getattr(self.user_data, "role_id", 3)
        
        if role_id == 1:
            from ui.arm_admin import ArmAdminWindow
            self.main_window = ArmAdminWindow()
        elif role_id == 2:
            from ui.arm_manager import ArmManagerWindow
            self.main_window = ArmManagerWindow()
        else:
            from ui.arm_worker import ArmWorkerWindow
            worker_id = None
            if isinstance(self.user_data, dict):
                worker_id = self.user_data.get("id_user", self.user_data.get("id"))
            else:
                worker_id = getattr(self.user_data, "id_user", getattr(self.user_data, "id", None))
            
            try:
                self.main_window = ArmWorkerWindow(user_id=worker_id)
            except TypeError:
                self.main_window = ArmWorkerWindow()
                self.main_window.user_id = worker_id

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

            QLineEdit {{ 
                background-color: {input_bg}; color: {text_col}; 
                border: 2px solid {border_col}; border-radius: 6px; 
                padding: 6px 12px; font-size: 15px; 
            }}
            QLineEdit:focus {{ border: 2px solid {accent_col}; }}
            QLineEdit::placeholder {{ color: {placeholder_col}; }}

            QPushButton[btn_type="primary"] {{ 
                background-color: {accent_col}; color: #FFFFFF; 
                font-weight: bold; font-size: 16px; border-radius: 6px; border: none; 
            }}
            QPushButton[btn_type="primary"]:hover {{ background-color: #7C3AED; }}
        """
        self.setStyleSheet(global_style)

        self.theme_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {text_col}; font-weight: 500; font-size: 13px; padding: 8px 12px; border-radius: 4px; border: none; }}
            QPushButton:hover {{ background-color: {btn_hover}; }}
        """)