import os
import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLineEdit, QComboBox, QFormLayout,
                             QGroupBox, QTabWidget, QProgressBar, QMessageBox,
                             QInputDialog, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from ui.base_arm import BaseArmWindow, StyledComboBox

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import APP_VERSION
import services.user_service as us
import services.monitoring_service as ms
import services.dictionary_service as ds


class DirectoryDialog(QDialog):
    def __init__(self, parent=None, tab_index=0, current_data=None):
        super().__init__(parent)
        self.tab_index = tab_index
        self.setWindowTitle("Редагувати запис" if current_data else "Додати новий запис")
        self.setFixedSize(380, 260)
        self.setStyleSheet("font-size: 14px;")

        layout = QVBoxLayout(self)
        self.form = QFormLayout()

        self.inputs = {}

        # 0, 4, 5, 6, 7 — Прості довідники (Назва підприємства, ролі, статуси тощо)
        if tab_index in (0, 4, 5, 6, 7):
            self.inputs["name"] = QLineEdit()
            self.form.addRow("Назва:", self.inputs["name"])
            if current_data: self.inputs["name"].setText(current_data.get("name", ""))

        elif tab_index == 1:  # Типи аварій
            self.inputs["category_combo"] = StyledComboBox()
            try:
                self.cats = ds.get_categories()
                for c in self.cats: self.inputs["category_combo"].addItem(c["name"], c["id"])
            except Exception as e:
                print(f"Помилка діалогу категорій: {e}")

            self.inputs["incident_name"] = QLineEdit()
            self.form.addRow("Категорія системи:", self.inputs["category_combo"])
            self.form.addRow("Назва типу аварії:", self.inputs["incident_name"])

            if current_data:
                self.inputs["incident_name"].setText(current_data.get("incident_name", ""))
                idx = self.inputs["category_combo"].findText(current_data.get("category_name", ""))
                if idx >= 0: self.inputs["category_combo"].setCurrentIndex(idx)

        elif tab_index == 2:  # Матеріали
            self.inputs["name"] = QLineEdit()
            self.inputs["unit"] = QLineEdit()
            self.inputs["price"] = QLineEdit()
            self.form.addRow("Назва матеріалу:", self.inputs["name"])
            self.form.addRow("Один. виміру:", self.inputs["unit"])
            self.form.addRow("Вартість (грн):", self.inputs["price"])

            if current_data:
                self.inputs["name"].setText(current_data.get("name", ""))
                self.inputs["unit"].setText(current_data.get("unit", ""))
                self.inputs["price"].setText(current_data.get("price", ""))


        elif tab_index == 3:  # Бригади
            self.inputs["crew_number"] = QLineEdit()
            # Випадаючий список категорій (спеціалізацій)
            self.inputs["category_combo"] = StyledComboBox()
            try:
                self.cats = ds.get_categories()
                for c in self.cats: self.inputs["category_combo"].addItem(c["name"], c["id"])
            except Exception as e:
                print(f"Помилка діалогу бригад (категорії): {e}")
            # НОВЕ: Випадаючий список реальних статусів з бази даних!
            self.inputs["status_combo"] = StyledComboBox()
            try:
                self.statuses = ds.get_crew_statuses()
                for s in self.statuses: self.inputs["status_combo"].addItem(s["name"], s["id"])
            except Exception as e:
                print(f"Помилка діалогу бригад (статуси): {e}")
            self.form.addRow("Номер бригади:", self.inputs["crew_number"])
            self.form.addRow("Спеціалізація:", self.inputs["category_combo"])
            self.form.addRow("Поточний статус:", self.inputs["status_combo"])  # Додали поле на форму
            if current_data:
                self.inputs["crew_number"].setText(current_data.get("crew_number", ""))
                idx_cat = self.inputs["category_combo"].findText(current_data.get("category_name", ""))
                if idx_cat >= 0: self.inputs["category_combo"].setCurrentIndex(idx_cat)
                # Підставляємо збережений статус при редагуванні
                idx_stat = self.inputs["status_combo"].findText(current_data.get("status", ""))
                if idx_stat >= 0: self.inputs["status_combo"].setCurrentIndex(idx_stat)

        layout.addLayout(self.form)
        self.btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.btns.accepted.connect(self.accept)
        self.btns.rejected.connect(self.reject)
        layout.addWidget(self.btns)

    def get_data(self):
        """Збирає введені адміністратором дані та обов'язково повертає словник res."""
        res = {}

        # Захист: якщо inputs порожній, відразу повертаємо порожній словник
        if not self.inputs:
            return res

        if self.tab_index in (0, 4, 5, 6, 7):
            res["name"] = self.inputs["name"].text().strip() if "name" in self.inputs else ""
        elif self.tab_index == 1:
            res["category_id"] = self.inputs[
                "category_combo"].currentData() if "category_combo" in self.inputs else None
            res["incident_name"] = self.inputs["incident_name"].text().strip() if "incident_name" in self.inputs else ""
        elif self.tab_index == 2:
            res["name"] = self.inputs["name"].text().strip() if "name" in self.inputs else ""
            res["unit"] = self.inputs["unit"].text().strip() if "unit" in self.inputs else ""
            price_text = self.inputs["price"].text().strip() if "price" in self.inputs else "0"
            try:
                res["price"] = float(price_text or 0)
            except ValueError:
                res["price"] = 0.0
        elif self.tab_index == 3:
            res["crew_number"] = self.inputs["crew_number"].text().strip() if "crew_number" in self.inputs else ""
            res["category_id"] = self.inputs[
                "category_combo"].currentData() if "category_combo" in self.inputs else None
            res["status_id"] = self.inputs["status_combo"].currentData() if "status_combo" in self.inputs else None

        return res  # <--- ПЕРЕВІРТЕ: Цей рядок має бути строго під дефом без зайвих зміщень!


class UserDialog(QDialog):
    def __init__(self, parent=None, user_data=None):
        super().__init__(parent)
        self.setWindowTitle("Додати користувача" if not user_data else "Редагувати користувача")
        self.setFixedSize(350, 250)
        self.setStyleSheet("font-size: 14px;")

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.role_combo = StyledComboBox()
        try:
            self.roles = us.get_all_roles()
            for r in self.roles:
                self.role_combo.addItem(r["name"], r["id"])
        except Exception as e:
            print(f"Помилка завантаження ролей: {e}")

        self.name_input = QLineEdit()
        self.email_input = QLineEdit()

        form.addRow("Роль:", self.role_combo)
        form.addRow("ПІБ:", self.name_input)
        form.addRow("Email:", self.email_input)

        self.password_input = None
        if not user_data:
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            form.addRow("Пароль:", self.password_input)

        layout.addLayout(form)

        self.btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.btns.accepted.connect(self.accept)
        self.btns.rejected.connect(self.reject)
        layout.addWidget(self.btns)

        if user_data:
            self.name_input.setText(user_data['full_name'])
            self.email_input.setText(user_data['email'])
            idx = self.role_combo.findText(user_data['role_name'])
            if idx >= 0: self.role_combo.setCurrentIndex(idx)

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
        self.init_static_table_filters()
        self.refresh_all_data()

    def setup_menu(self):
        self.add_menu_item("Моніторинг стану", self.build_monitoring_page())
        self.add_menu_item("Управління користувачами", self.build_users_page())
        self.add_menu_item("Ведення довідників", self.build_directories_page())
        self.add_menu_item("Журнал дій", self.build_audit_page())
        self.add_menu_item("Настройки системи", self.build_settings_page())
        self.add_menu_item("Про програму", self.build_about_page())
        self.finalize_menu()

    def clear_layout(self, layout):
        """ПОВЕРНЕНО НА МІСЦЕ: Допоміжний метод очищення макетів від старих фільтрів."""
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

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

        self.db_indicator = QLabel("● Перевірка статусу...")
        self.db_indicator.setStyleSheet("color: #FFB86C; font-weight: bold;")
        db_status.addStretch()
        db_status.addWidget(self.db_indicator)
        serv_layout.addLayout(db_status)

        layout.addWidget(servers_group)

        backup_group = QGroupBox("Резервне копіювання")
        back_lay = QVBoxLayout(backup_group)

        try:
            last_time = ms.get_last_backup_time()
        except:
            last_time = "Ще не проводився"

        self.lbl_backup_time = QLabel(f"Останній бекап: {last_time}")
        back_lay.addWidget(self.lbl_backup_time)

        progress_lay = QHBoxLayout()
        progress_lay.addWidget(QLabel("Місце на диску для бекапів:"))

        self.pbar = QProgressBar()
        self.pbar.setStyleSheet(
            "QProgressBar { border: 1px solid #44475A; border-radius: 5px; text-align: center; color: white; } "
            "QProgressBar::chunk { background-color: #8B5CF6; }")
        progress_lay.addWidget(self.pbar)
        back_lay.addLayout(progress_lay)

        btn_backup = self.create_action_button("Створити бекап зараз")
        btn_backup.clicked.connect(self.action_run_backup)
        back_lay.addWidget(btn_backup, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addWidget(backup_group)
        layout.addStretch()

        self.monitor_timer = QTimer(self)
        self.monitor_timer.timeout.connect(self.refresh_monitoring_data)
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
        btn_add.clicked.connect(self.action_add_user)
        top_bar.addWidget(btn_add)
        layout.addLayout(top_bar)

        self.users_filters_layout = QVBoxLayout()
        layout.addLayout(self.users_filters_layout)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(4)
        self.users_table.setHorizontalHeaderLabels(["ID", "Роль", "Повне ім'я", "Електронна пошта"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.users_table)

        actions = QHBoxLayout()
        btn_edit = self.create_action_button("Редагувати дані")
        btn_edit.clicked.connect(self.action_edit_user)
        actions.addWidget(btn_edit)

        btn_reset = self.create_action_button("Скинути пароль")
        btn_reset.clicked.connect(self.action_reset_password)
        actions.addWidget(btn_reset)

        btn_block = self.create_action_button("Видалити", danger=True)
        btn_block.clicked.connect(self.action_delete_user)
        actions.addWidget(btn_block)

        actions.addStretch()
        layout.addLayout(actions)
        return page

    def build_directories_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        self.directory_tabs = QTabWidget()

        self.lay_filter_cat = QVBoxLayout()
        self.lay_filter_issues = QVBoxLayout()
        self.lay_filter_mat = QVBoxLayout()
        self.lay_filter_crew = QVBoxLayout()
        self.lay_filter_roles = QVBoxLayout()
        self.lay_filter_status = QVBoxLayout()
        self.lay_filter_crit = QVBoxLayout()
        self.lay_filter_crew_stat = QVBoxLayout()

        # 0. Вкладка Категорії
        tab_cat = QWidget()
        cat_lay = QVBoxLayout(tab_cat)
        self.table_cat = QTableWidget()
        self.table_cat.setColumnCount(2)
        self.table_cat.setHorizontalHeaderLabels(["Код", "Назва категорії"])
        self.table_cat.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        cat_lay.addLayout(self.lay_filter_cat)
        cat_lay.addWidget(self.table_cat)
        self.directory_tabs.addTab(tab_cat, "Категорії")

        # 1. Вкладка Типи аварій
        tab_issues = QWidget()
        iss_lay = QVBoxLayout(tab_issues)
        self.table_issues = QTableWidget()
        self.table_issues.setColumnCount(3)
        self.table_issues.setHorizontalHeaderLabels(["Код", "Категорія", "Назва аварії"])
        self.table_issues.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        iss_lay.addLayout(self.lay_filter_issues)
        iss_lay.addWidget(self.table_issues)
        self.directory_tabs.addTab(tab_issues, "Типи аварій")

        # 2. Вкладка Матеріали
        tab_mat = QWidget()
        mat_lay = QVBoxLayout(tab_mat)
        self.table_mat = QTableWidget()
        self.table_mat.setColumnCount(4)
        self.table_mat.setHorizontalHeaderLabels(["Код", "Назва матеріалу", "Од. виміру", "Ціна"])
        self.table_mat.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        mat_lay.addLayout(self.lay_filter_mat)
        mat_lay.addWidget(self.table_mat)
        self.directory_tabs.addTab(tab_mat, "Матеріали")

        # 3. Вкладка Бригади
        tab_crew = QWidget()
        crew_lay = QVBoxLayout(tab_crew)
        self.table_crew = QTableWidget()
        self.table_crew.setColumnCount(4)
        self.table_crew.setHorizontalHeaderLabels(["Код", "Номер бригади", "Категорія", "Статус"])
        self.table_crew.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        crew_lay.addLayout(self.lay_filter_crew)
        crew_lay.addWidget(self.table_crew)
        self.directory_tabs.addTab(tab_crew, "Бригади")

        # 4. Вкладка Ролі
        tab_roles = QWidget()
        roles_lay = QVBoxLayout(tab_roles)
        self.table_roles = QTableWidget()
        self.table_roles.setColumnCount(2)
        self.table_roles.setHorizontalHeaderLabels(["Код", "Назва ролі"])
        self.table_roles.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        roles_lay.addLayout(self.lay_filter_roles)
        roles_lay.addWidget(self.table_roles)
        self.directory_tabs.addTab(tab_roles, "Ролі")

        # 5. Вкладка Статуси заявок
        tab_status = QWidget()
        status_lay = QVBoxLayout(tab_status)
        self.table_status = QTableWidget()
        self.table_status.setColumnCount(2)
        self.table_status.setHorizontalHeaderLabels(["Код", "Назва статусу"])
        self.table_status.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        status_lay.addLayout(self.lay_filter_status)
        status_lay.addWidget(self.table_status)
        self.directory_tabs.addTab(tab_status, "Статуси заявок")

        # 6. Вкладка Рівні критичності
        tab_crit = QWidget()
        crit_lay = QVBoxLayout(tab_crit)
        self.table_crit = QTableWidget()
        self.table_crit.setColumnCount(2)
        self.table_crit.setHorizontalHeaderLabels(["Код", "Рівень критичності"])
        self.table_crit.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        crit_lay.addLayout(self.lay_filter_crit)
        crit_lay.addWidget(self.table_crit)
        self.directory_tabs.addTab(tab_crit, "Критичність")

        # 7. Вкладка Статуси бригад
        tab_crew_stat = QWidget()
        crew_stat_lay = QVBoxLayout(tab_crew_stat)
        self.table_crew_status = QTableWidget()
        self.table_crew_status.setColumnCount(2)
        self.table_crew_status.setHorizontalHeaderLabels(["Код", "Статус бригади"])
        self.table_crew_status.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        crew_stat_lay.addLayout(self.lay_filter_crew_stat)
        crew_stat_lay.addWidget(self.table_crew_status)
        self.directory_tabs.addTab(tab_crew_stat, "Статуси бригад")

        layout.addWidget(self.directory_tabs)

        dir_btns = QHBoxLayout()
        btn_add = self.create_action_button("Додати запис")
        btn_add.clicked.connect(self.action_add_directory_item)
        dir_btns.addWidget(btn_add)

        btn_edit = self.create_action_button("Редагувати")
        btn_edit.clicked.connect(self.action_edit_directory_item)
        dir_btns.addWidget(btn_edit)

        btn_del = self.create_action_button("Видалити", danger=True)
        btn_del.clicked.connect(self.action_delete_directory_item)
        dir_btns.addWidget(btn_del)

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

        self.lay_filter_audit = QVBoxLayout()
        layout.addLayout(self.lay_filter_audit)
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

        version = QLabel(f"Версія {APP_VERSION}")
        version.setStyleSheet("font-size: 14px;")
        layout.addWidget(version, alignment=Qt.AlignmentFlag.AlignCenter)
        return page

    def init_static_table_filters(self):
        try:
            all_roles = [r["name"] for r in us.get_all_roles()]
            f_user = self.create_table_filters(self.users_table, filter_options={1: all_roles})
            self.users_filters_layout.addWidget(f_user)
        except Exception as e:
            print(f"Помилка створення статичного фільтра: {e}")

        self.lay_filter_cat.addWidget(self.create_table_filters(self.table_cat))
        self.lay_filter_issues.addWidget(self.create_table_filters(self.table_issues))
        self.lay_filter_mat.addWidget(self.create_table_filters(self.table_mat))
        self.lay_filter_crew.addWidget(self.create_table_filters(self.table_crew))
        self.lay_filter_roles.addWidget(self.create_table_filters(self.table_roles))
        self.lay_filter_status.addWidget(self.create_table_filters(self.table_status))
        self.lay_filter_crit.addWidget(self.create_table_filters(self.table_crit))
        self.lay_filter_crew_stat.addWidget(self.create_table_filters(self.table_crew_status))

    def refresh_all_data(self):
        try:
            self.load_users_data()
            self.load_all_directories()
            self.refresh_monitoring_data()
        except Exception as e:
            print(f"Помилка наповнення даних: {e}")

    def load_users_data(self):
        try:
            users_data = us.get_all_users()
            self.users_table.setRowCount(0)
            for row_idx, user in enumerate(users_data):
                self.users_table.insertRow(row_idx)
                item_id = QTableWidgetItem(str(user["id"]))
                item_role = QTableWidgetItem(user["role_name"])
                item_name = QTableWidgetItem(user["full_name"])
                item_email = QTableWidgetItem(user["email"])

                for item in (item_id, item_role, item_name, item_email):
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                self.users_table.setItem(row_idx, 0, item_id)
                self.users_table.setItem(row_idx, 1, item_role)
                self.users_table.setItem(row_idx, 2, item_name)
                self.users_table.setItem(row_idx, 3, item_email)
        except Exception as e:
            print(f"Помилка рендеру користувачів: {e}")

    def load_all_directories(self):
        # Перегенерація фільтрів у стабільному шарі
        for lay, tbl in [(self.lay_filter_cat, self.table_cat),
                         (self.lay_filter_issues, self.table_issues),
                         (self.lay_filter_mat, self.table_mat),
                         (self.lay_filter_crew, self.table_crew),
                         (self.lay_filter_roles, self.table_roles),
                         (self.lay_filter_status, self.table_status),
                         (self.lay_filter_crit, self.table_crit),
                         (self.lay_filter_crew_stat, self.table_crew_status)]:
            self.clear_layout(lay)
            lay.addWidget(self.create_table_filters(tbl))

        # 0. Категорії
        try:
            self.table_cat.setRowCount(0)
            for r, i in enumerate(ds.get_categories()):
                self.table_cat.insertRow(r)
                self.table_cat.setItem(r, 0, QTableWidgetItem(str(i["id"])))
                self.table_cat.setItem(r, 1, QTableWidgetItem(i["name"]))
        except Exception as e:
            print(f"Помилка категорій: {e}")

        # 1. Типи аварій
        try:
            self.table_issues.setRowCount(0)
            for r, i in enumerate(ds.get_incident_types()):
                self.table_issues.insertRow(r)
                self.table_issues.setItem(r, 0, QTableWidgetItem(str(i["id"])))
                self.table_issues.setItem(r, 1, QTableWidgetItem(i["category_name"]))
                self.table_issues.setItem(r, 2, QTableWidgetItem(i["incident_name"]))
        except Exception as e:
            print(f"Помилка типів аварій: {e}")

        # 2. Матеріали
        try:
            self.table_mat.setRowCount(0)
            for r, i in enumerate(ds.get_materials()):
                self.table_mat.insertRow(r)
                self.table_mat.setItem(r, 0, QTableWidgetItem(str(i["id"])))
                self.table_mat.setItem(r, 1, QTableWidgetItem(i["name"]))
                self.table_mat.setItem(r, 2, QTableWidgetItem(i["unit"]))
                self.table_mat.setItem(r, 3, QTableWidgetItem(str(i["price"])))
        except Exception as e:
            print(f"Помилка матеріалів: {e}")

        # 3. Бригади
        try:
            self.table_crew.setRowCount(0)
            for r, i in enumerate(ds.get_crews()):
                self.table_crew.insertRow(r)
                self.table_crew.setItem(r, 0, QTableWidgetItem(str(i["id"])))
                self.table_crew.setItem(r, 1, QTableWidgetItem(i["crew_number"]))
                self.table_crew.setItem(r, 2, QTableWidgetItem(i["category_name"]))
                self.table_crew.setItem(r, 3, QTableWidgetItem(i["status"]))
        except Exception as e:
            print(f"Помилка бригад: {e}")

        # 4. Ролі
        try:
            self.table_roles.setRowCount(0)
            for r, i in enumerate(ds.get_roles()):
                self.table_roles.insertRow(r)
                self.table_roles.setItem(r, 0, QTableWidgetItem(str(i["id"])))
                self.table_roles.setItem(r, 1, QTableWidgetItem(i["name"]))
        except Exception as e:
            print(f"Помилка ролей: {e}")

        # 5. Статуси заявок
        try:
            self.table_status.setRowCount(0)
            for r, i in enumerate(ds.get_statuses()):
                self.table_status.insertRow(r)
                self.table_status.setItem(r, 0, QTableWidgetItem(str(i["id"])))
                self.table_status.setItem(r, 1, QTableWidgetItem(i["name"]))
        except Exception as e:
            print(f"Помилка статусів: {e}")

        # 6. Критичність
        try:
            self.table_crit.setRowCount(0)
            for r, i in enumerate(ds.get_criticalities()):
                self.table_crit.insertRow(r)
                self.table_crit.setItem(r, 0, QTableWidgetItem(str(i["id"])))
                self.table_crit.setItem(r, 1, QTableWidgetItem(i["name"]))
        except Exception as e:
            print(f"Помилка критичності: {e}")

        # 7. Статуси бригад
        try:
            self.table_crew_status.setRowCount(0)
            for r, i in enumerate(ds.get_crew_statuses()):
                self.table_crew_status.insertRow(r)
                self.table_crew_status.setItem(r, 0, QTableWidgetItem(str(i["id"])))
                self.table_crew_status.setItem(r, 1, QTableWidgetItem(i["name"]))
        except Exception as e:
            print(f"Помилка статусів бригад: {e}")

        # Захист від редагування клітинок
        for table in (self.table_cat, self.table_issues, self.table_mat, self.table_crew,
                      self.table_roles, self.table_status, self.table_crit, self.table_crew_status):
            for row in range(table.rowCount()):
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    if item: item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

    def action_delete_user(self):
        selected_rows = self.users_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Увага", "Спочатку оберіть користувача в таблиці!")
            return
        row = selected_rows[0].row()
        user_id = int(self.users_table.item(row, 0).text())
        reply = QMessageBox.question(self, "Підтвердження", "Ви впевнені, що хочете видалити цього користувача?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = us.delete_user(user_id)
            if success:
                self.load_users_data()
            else:
                QMessageBox.critical(self, "Помилка", msg)

    def get_selected_user_id(self):
        selected_rows = self.users_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Увага", "Будь ласка, оберіть користувача в таблиці.")
            return None
        return int(self.users_table.item(selected_rows[0].row(), 0).text())

    def action_add_user(self):
        dialog = UserDialog(self)
        dialog.setStyleSheet(self.styleSheet())
        if dialog.exec():
            data = dialog.get_data()
            if not data["full_name"] or not data["password"]:
                QMessageBox.warning(self, "Помилка", "ПІБ та Пароль є обов'язковими!")
                return
            success, msg = us.add_user(data["role_id"], data["full_name"], data["email"], data["password"])
            if success:
                self.load_users_data()
            else:
                QMessageBox.critical(self, "Помилка", msg)

    def action_edit_user(self):
        user_id = self.get_selected_user_id()
        if not user_id: return
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
        new_password, ok = QInputDialog.getText(self, "Скидання пароля", "Введіть новий пароль:",
                                                QLineEdit.EchoMode.Password)
        if ok and new_password.strip():
            success, msg = us.reset_password(user_id, new_password.strip())
            if success:
                QMessageBox.information(self, "Успіх", msg)
            else:
                QMessageBox.critical(self, "Помилка", msg)

    def refresh_monitoring_data(self):
        try:
            if ms.check_db_status():
                self.db_indicator.setText("● Працює")
                self.db_indicator.setStyleSheet("color: #50FA7B; font-weight: bold;")
            else:
                self.db_indicator.setText("● Відключено")
                self.db_indicator.setStyleSheet("color: #FF5555; font-weight: bold;")
            self.pbar.setValue(ms.get_disk_usage_percent())
        except Exception as e:
            print(f"Помилка таймера моніторингу: {e}")

    def action_run_backup(self):
        success, message = ms.create_system_backup()
        if success:
            self.lbl_backup_time.setText(f"Останній бекап: {ms.get_last_backup_time()}")
            QMessageBox.information(self, "Успіх", message)
            self.refresh_monitoring_data()
        else:
            QMessageBox.critical(self, "Помилка", message)

    def get_active_directory_table_and_index(self):
        idx = self.directory_tabs.currentIndex()
        tables = {
            0: self.table_cat, 1: self.table_issues, 2: self.table_mat,
            3: self.table_crew, 4: self.table_roles,
            5: self.table_status, 6: self.table_crit, 7: self.table_crew_status
        }
        return idx, tables.get(idx)

    def action_add_directory_item(self):
        tab_idx, table = self.get_active_directory_table_and_index()
        dialog = DirectoryDialog(self, tab_index=tab_idx)
        dialog.setStyleSheet(self.styleSheet())
        if dialog.exec():
            success, msg = ds.save_directory_item(tab_idx, dialog.get_data())
            if success:
                self.load_all_directories()
            else:
                QMessageBox.critical(self, "Помилка", msg)

    def action_edit_directory_item(self):
        tab_idx, table = self.get_active_directory_table_and_index()
        selected = table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Увага", "Будь ласка, оберіть потрібний рядок у таблиці.")
            return

        row = selected[0].row()
        item_id = int(table.item(row, 0).text())
        current_data = {}

        if tab_idx in (0, 4, 5, 6, 7):
            current_data["name"] = table.item(row, 1).text()
        elif tab_idx == 1:
            current_data["category_name"] = table.item(row, 1).text()
            current_data["incident_name"] = table.item(row, 2).text()
        elif tab_idx == 2:
            current_data["name"] = table.item(row, 1).text()
            current_data["unit"] = table.item(row, 2).text()
            current_data["price"] = table.item(row, 3).text()
        elif tab_idx == 3:
            current_data["crew_number"] = table.item(row, 1).text()
            current_data["category_name"] = table.item(row, 2).text()
            # НОВЕ: Зчитуємо поточний текст статусу з таблиці, щоб передати у форму
            current_data["status"] = table.item(row, 3).text()

        dialog = DirectoryDialog(self, tab_index=tab_idx, current_data=current_data)
        dialog.setStyleSheet(self.styleSheet())
        if dialog.exec():
            success, msg = ds.save_directory_item(tab_idx, dialog.get_data(), item_id=item_id)
            if success:
                self.load_all_directories()
            else:
                QMessageBox.critical(self, "Помилка", msg)

    def action_delete_directory_item(self):
        tab_idx, table = self.get_active_directory_table_and_index()
        selected = table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Увага", "Будь ласка, спочатку оберіть запис у таблиці!")
            return
        row = selected[0].row()
        item_id = int(table.item(row, 0).text())
        reply = QMessageBox.question(self, "Підтвердження", "Ви впевнені, що хочете видалити цей довідниковий запис?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = ds.delete_directory_item(tab_idx, item_id)
            if success:
                self.load_all_directories()
            else:
                QMessageBox.critical(self, "Обмеження видалення", msg)