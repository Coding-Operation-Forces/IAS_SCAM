import os
import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLineEdit, QComboBox, QFormLayout,
                             QGroupBox, QTabWidget, QProgressBar,  QMessageBox,
                             QInputDialog, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from ui.base_arm import BaseArmWindow, StyledComboBox
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import APP_VERSION
import services.user_service as us
import services.monitoring_service as ms

class UserDialog(QDialog):
    def __init__(self, parent=None, user_data=None):
        super().__init__(parent)
        self.setWindowTitle("Додати користувача" if not user_data else "Редагувати користувача")
        self.setFixedSize(350, 250)
        self.setStyleSheet("font-size: 14px;")

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.role_combo = StyledComboBox()
        self.roles = us.get_all_roles()
        for r in self.roles:
            self.role_combo.addItem(r["name"], r["id"])

        self.name_input = QLineEdit()
        self.email_input = QLineEdit()

        form.addRow("Роль:", self.role_combo)
        form.addRow("ПІБ:", self.name_input)
        form.addRow("Email:", self.email_input)

        self.password_input = None
        if not user_data:  # Пароль вводимо тільки при створенні
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            form.addRow("Пароль:", self.password_input)

        layout.addLayout(form)

        self.btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.btns.accepted.connect(self.accept)
        self.btns.rejected.connect(self.reject)
        layout.addWidget(self.btns)

        # Якщо це редагування, заповнюємо поля існуючими даними
        if user_data:
            self.name_input.setText(user_data['full_name'])
            self.email_input.setText(user_data['email'])
            idx = self.role_combo.findText(user_data['role_name'])
            if idx >= 0:
                self.role_combo.setCurrentIndex(idx)

    def get_data(self):
        data = {
            "role_id": self.role_combo.currentData(),
            "full_name": self.name_input.text().strip(),
            "email": self.email_input.text().strip()
        }
        if self.password_input:
            data["password"] = self.password_input.text().strip()
        return data
class ArmAdminWindow(BaseArmWindow):
    def __init__(self):
        super().__init__("АРМ Адміністратора системи")
        self.setup_menu()

    def setup_menu(self):
        self.add_menu_item("Моніторинг стану", self.build_monitoring_page())
        self.add_menu_item("Управління користувачами", self.build_users_page())
        self.add_menu_item("Ведення довідників", self.build_directories_page())
        self.add_menu_item("Журнал дій", self.build_audit_page())
        self.add_menu_item("Настройки системи", self.build_settings_page())
        self.add_menu_item("Про програму", self.build_about_page())
        self.finalize_menu()

    def build_monitoring_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        title = QLabel("Моніторинг технічного стану")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        servers_group = QGroupBox("Статус серверів")
        serv_layout = QVBoxLayout(servers_group)

        db_status = QHBoxLayout()
        db_status.addWidget(QLabel("Сервер бази даних:"))

        # ЗБЕРІГАЄМО ІНДИКАТОР В self
        self.db_indicator = QLabel("● Перевірка статусу...")
        self.db_indicator.setStyleSheet("color: #FFB86C; font-weight: bold;")
        db_status.addStretch()
        db_status.addWidget(self.db_indicator)
        serv_layout.addLayout(db_status)

        layout.addWidget(servers_group)

        backup_group = QGroupBox("Резервне копіювання")
        back_lay = QVBoxLayout(backup_group)

        # ДИНАМІЧНО ПІДТЯГУЄМО ЧАС ОСТАННЬОГО БЕКАПУ В self
        last_time = ms.get_last_backup_time()
        self.lbl_backup_time = QLabel(f"Останній бекап: {last_time}")
        back_lay.addWidget(self.lbl_backup_time)

        progress_lay = QHBoxLayout()
        progress_lay.addWidget(QLabel("Місце на диску для бекапів:"))

        # ЗБЕРІГАЄМО PROGRESS BAR В self
        self.pbar = QProgressBar()
        self.pbar.setStyleSheet(
            "QProgressBar { border: 1px solid #44475A; border-radius: 5px; text-align: center; color: white; } "
            "QProgressBar::chunk { background-color: #8B5CF6; }")
        progress_lay.addWidget(self.pbar)
        back_lay.addLayout(progress_lay)

        # ПРИВ'ЯЗУЄМО КНОПКУ ДО ОБРОБНИКА КЛІКІВ
        btn_backup = self.create_action_button("Створити бекап зараз")
        btn_backup.clicked.connect(self.action_run_backup)
        back_lay.addWidget(btn_backup, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addWidget(backup_group)
        layout.addStretch()

        # ОДРАЗУ ОНОВЛЮЄМО ДАНІ СТАНУ БД ТА ДИСКУ ПРИ ВІДКРИТТІ
        self.refresh_monitoring_data()
        # 2. ІНІЦІАЛІЗАЦІЯ ТАЙМЕРА ДЛЯ РЕАЛЬНОГО ЧАСУ (ДОДАЙТЕ ЦЕЙ БЛОК)
        self.monitor_timer = QTimer(self)
        # Прив'язуємо оновлення даних до таймера
        self.monitor_timer.timeout.connect(self.refresh_monitoring_data)
        # Запускаємо перевірку кожні 3000 мілісекунд (3 секунди)
        self.monitor_timer.start(3000)
        return page

    def build_users_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Управління користувачами та ролями")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        top_bar = QHBoxLayout()
        top_bar.addStretch()
        btn_add = self.create_action_button("Додати користувача", primary=True)
        btn_add.clicked.connect(self.action_add_user)  # ДОДАНО ЗВ'ЯЗОК
        top_bar.addWidget(btn_add)
        layout.addLayout(top_bar)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(4)
        self.users_table.setHorizontalHeaderLabels(["ID", "Роль", "Повне ім'я", "Електронна пошта"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.users_table.setRowCount(0)

        # 1. Отримуємо список ролей з нашого сервісу
        all_roles = [r["name"] for r in us.get_all_roles()]
        # 2. Передаємо їх у фільтр (Колонка 1 — це "Роль")
        filters = self.create_table_filters(self.users_table, filter_options={1: all_roles})
        layout.addWidget(filters)
        layout.addWidget(self.users_table)

        actions = QHBoxLayout()

        btn_edit = self.create_action_button("Редагувати дані")
        btn_edit.clicked.connect(self.action_edit_user)  # ДОДАНО ЗВ'ЯЗОК
        actions.addWidget(btn_edit)

        btn_reset = self.create_action_button("Скинути пароль")
        btn_reset.clicked.connect(self.action_reset_password)  # ДОДАНО ЗВ'ЯЗОК
        actions.addWidget(btn_reset)

        btn_block = self.create_action_button("Видалити", danger=True)
        btn_block.clicked.connect(self.action_delete_user)  # ВЖЕ БУЛО
        actions.addWidget(btn_block)

        actions.addStretch()
        layout.addLayout(actions)

        self.load_users_data()  # ВЖЕ БУЛО
        return page

    def build_directories_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        tabs = QTabWidget()

        tab_cat = QWidget()
        cat_lay = QVBoxLayout(tab_cat)
        self.table_cat = QTableWidget()
        self.table_cat.setColumnCount(2)
        self.table_cat.setHorizontalHeaderLabels(["Код", "Назва категорії"])
        self.table_cat.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_cat.setRowCount(0)
        cat_lay.addWidget(self.create_table_filters(self.table_cat))
        cat_lay.addWidget(self.table_cat)
        tabs.addTab(tab_cat, "Категорії")

        tab_issues = QWidget()
        iss_lay = QVBoxLayout(tab_issues)
        self.table_issues = QTableWidget()
        self.table_issues.setColumnCount(3)
        self.table_issues.setHorizontalHeaderLabels(["Код", "Категорія", "Назва аварії"])
        self.table_issues.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_issues.setRowCount(0)
        iss_lay.addWidget(self.create_table_filters(self.table_issues))
        iss_lay.addWidget(self.table_issues)
        tabs.addTab(tab_issues, "Типи аварій")

        tab_mat = QWidget()
        mat_lay = QVBoxLayout(tab_mat)
        self.table_mat = QTableWidget()
        self.table_mat.setColumnCount(4)
        self.table_mat.setHorizontalHeaderLabels(["Код", "Назва матеріалу", "Од. виміру", "Ціна"])
        self.table_mat.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_mat.setRowCount(0)
        mat_lay.addWidget(self.create_table_filters(self.table_mat))
        mat_lay.addWidget(self.table_mat)
        tabs.addTab(tab_mat, "Матеріали")

        # ОНОВЛЕНО: Таблиця бригад (Категорія та Статус)
        tab_crew = QWidget()
        crew_lay = QVBoxLayout(tab_crew)
        self.table_crew = QTableWidget()
        self.table_crew.setColumnCount(4)
        self.table_crew.setHorizontalHeaderLabels(["Код", "Номер бригади", "Категорія", "Статус (Зайнята/Вільна)"])
        self.table_crew.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_crew.setRowCount(0)
        crew_lay.addWidget(self.create_table_filters(self.table_crew))
        crew_lay.addWidget(self.table_crew)
        tabs.addTab(tab_crew, "Бригади")

        tab_roles = QWidget()
        roles_lay = QVBoxLayout(tab_roles)
        self.table_roles = QTableWidget()
        self.table_roles.setColumnCount(2)
        self.table_roles.setHorizontalHeaderLabels(["Код", "Назва ролі"])
        self.table_roles.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_roles.setRowCount(0)
        roles_lay.addWidget(self.create_table_filters(self.table_roles))
        roles_lay.addWidget(self.table_roles)
        tabs.addTab(tab_roles, "Ролі")

        layout.addWidget(tabs)

        dir_btns = QHBoxLayout()
        dir_btns.addWidget(self.create_action_button("Додати запис"))
        dir_btns.addWidget(self.create_action_button("Редагувати"))
        dir_btns.addWidget(self.create_action_button("Видалити", danger=True))
        dir_btns.addStretch()
        layout.addLayout(dir_btns)

        return page

    def build_audit_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Журнал дій користувачів")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        self.table_audit = QTableWidget()
        self.table_audit.setColumnCount(7)
        self.table_audit.setHorizontalHeaderLabels([
            "ID", "Користувач", "Час", "Дія", "Таблиця", "Старе значення", "Нове значення"
        ])
        self.table_audit.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_audit.setRowCount(0)

        filters = self.create_table_filters(self.table_audit)
        layout.addWidget(filters)
        layout.addWidget(self.table_audit)

        btn_export = self.create_action_button("Експорт журналу", primary=True)
        layout.addWidget(btn_export, alignment=Qt.AlignmentFlag.AlignRight)

        return page

    def build_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        group = QGroupBox("Глобальні конфігурації")
        form = QFormLayout(group)

        le_name = QLineEdit()
        le_name.setPlaceholderText("КП 'Київжитлоспецексплуатація'")

        le_ip = QLineEdit()
        le_ip.setPlaceholderText("127.0.0.1")

        form.addRow("Назва підприємства:", le_name)
        form.addRow("IP-адреса сервера бази даних:", le_ip)

        backup_freq = StyledComboBox()
        backup_freq.addItems(["Щодня", "Щотижня", "Кожні 12 годин"])
        form.addRow("Частота бекапів:", backup_freq)

        layout.addWidget(group)

        btn_save = self.create_action_button("Зберегти настройки", primary=True)
        layout.addWidget(btn_save, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addStretch()
        return page

    def build_about_page(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, "icon.png")
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo = QLabel()
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            logo.setPixmap(
                pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            logo.setText("Логотип не знайдено\n(Перевірте файл icon.png)")
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo.setStyleSheet("font-size: 16px; color: #FF5555;")

        layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)

        name = QLabel("Система управління комунальним підприємством")
        name.setStyleSheet("font-size: 22px; font-weight: bold; color: #8B5CF6; margin-top: 15px;")
        layout.addWidget(name, alignment=Qt.AlignmentFlag.AlignCenter)

        version = QLabel("Версія {APP_VERSION}")
        version.setStyleSheet("font-size: 14px;")
        layout.addWidget(version, alignment=Qt.AlignmentFlag.AlignCenter)

        return page

    # ==========================================
    # ЛОГІКА ЗВ'ЯЗКУ З БАЗОЮ ДАНИХ (БЕЗ ЗМІНИ UI)
    # ==========================================
    def load_users_data(self):
        """Завантажує користувачів з бекенду і вставляє в існуючу таблицю."""
        users_data = us.get_all_users()
        self.users_table.setRowCount(0)  # Очищаємо таблицю від старих даних

        for row_idx, user in enumerate(users_data):
            self.users_table.insertRow(row_idx)

            # Переводимо дані зі словника у формат клітинок PyQt
            item_id = QTableWidgetItem(str(user["id"]))
            item_role = QTableWidgetItem(user["role_name"])
            item_name = QTableWidgetItem(user["full_name"])
            item_email = QTableWidgetItem(user["email"])

            # Захищаємо клітинки від ручного редагування подвійним кліком
            for item in (item_id, item_role, item_name, item_email):
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # Вставляємо клітинки в таблицю
            self.users_table.setItem(row_idx, 0, item_id)
            self.users_table.setItem(row_idx, 1, item_role)
            self.users_table.setItem(row_idx, 2, item_name)
            self.users_table.setItem(row_idx, 3, item_email)

    def action_delete_user(self):
        """Логіка для кнопки 'Видалити'."""
        selected_rows = self.users_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Увага", "Спочатку оберіть користувача в таблиці!")
            return

        # Дістаємо ID користувача з першої колонки обраного рядка
        row = selected_rows[0].row()
        user_id = int(self.users_table.item(row, 0).text())

        # Запитуємо підтвердження через стандартне вікно
        reply = QMessageBox.question(self, "Підтвердження", "Ви впевнені, що хочете видалити цього користувача?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            success, msg = us.delete_user(user_id)  # Викликаємо бекенд
            if success:
                self.load_users_data()  # Оновлюємо таблицю, щоб видалений рядок зник
            else:
                QMessageBox.critical(self, "Помилка", msg)

    def get_selected_user_id(self):
        """Допоміжна функція: отримує ID користувача з виділеного рядка таблиці."""
        selected_rows = self.users_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Увага", "Будь ласка, оберіть користувача в таблиці.")
            return None
        row = selected_rows[0].row()
        return int(self.users_table.item(row, 0).text())

    def action_add_user(self):
        dialog = UserDialog(self)
        dialog.setStyleSheet(self.styleSheet())  # Стилізуємо під тему вікна
        if dialog.exec():
            data = dialog.get_data()
            if not data["full_name"] or not data["password"]:
                QMessageBox.warning(self, "Помилка", "ПІБ та Пароль є обов'язковими!")
                return

            success, msg = us.add_user(data["role_id"], data["full_name"], data["email"], data["password"])
            if success:
                self.load_users_data()  # Оновлюємо таблицю
            else:
                QMessageBox.critical(self, "Помилка", msg)

    def action_edit_user(self):
        user_id = self.get_selected_user_id()
        if not user_id: return

        # Читаємо поточні дані з таблиці, щоб передати у вікно
        row = self.users_table.selectedItems()[0].row()
        current_data = {
            "role_name": self.users_table.item(row, 1).text(),
            "full_name": self.users_table.item(row, 2).text(),
            "email": self.users_table.item(row, 3).text()
        }

        dialog = UserDialog(self, user_data=current_data)
        dialog.setStyleSheet(self.styleSheet())
        if dialog.exec():
            data = dialog.get_data()
            success, msg = us.update_user(user_id, data["role_id"], data["full_name"], data["email"])
            if success:
                self.load_users_data()
            else:
                QMessageBox.critical(self, "Помилка", msg)

    def action_reset_password(self):
        user_id = self.get_selected_user_id()
        if not user_id: return

        # Стандартне віконечко для вводу одного рядка тексту (пароля)
        new_password, ok = QInputDialog.getText(self, "Скидання пароля", "Введіть новий пароль:",
                                                QLineEdit.EchoMode.Password)
        if ok and new_password.strip():
            success, msg = us.reset_password(user_id, new_password.strip())
            if success:
                QMessageBox.information(self, "Успіх", msg)
            else:
                QMessageBox.critical(self, "Помилка", msg)

    # ==========================================
    # ЛОГІКА МОНІТОРИНГУ СИСТЕМИ
    # ==========================================
    def refresh_monitoring_data(self):
        """Зчитує реальний стан підключення до Postgres та місце на диску."""
        # 1. Перевірка статусу підключення до БД
        if ms.check_db_status():
            self.db_indicator.setText("● Працює")
            self.db_indicator.setStyleSheet("color: #50FA7B; font-weight: bold;")
        else:
            self.db_indicator.setText("● Відключено")
            self.db_indicator.setStyleSheet("color: #FF5555; font-weight: bold;")

        # 2. Оновлення реального стану завантаженості локального накопичувача
        disk_used = ms.get_disk_usage_percent()
        self.pbar.setValue(disk_used)

    def action_run_backup(self):
        """Викликає створення повного дампа бази та відображає точний час."""
        success, message = ms.create_system_backup()
        if success:
            # Оновлюємо текстову мітку часу на основі щойно записаного файлу статусів
            last_time = ms.get_last_backup_time()
            self.lbl_backup_time.setText(f"Останній бекап: {last_time}")

            QMessageBox.information(self, "Успіх", message)
            self.refresh_monitoring_data()  # Оновлюємо відсоток вільного простору
        else:
            QMessageBox.critical(self, "Помилка", message)