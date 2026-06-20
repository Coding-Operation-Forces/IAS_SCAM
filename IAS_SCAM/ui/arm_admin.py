import os

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLineEdit, QComboBox, QFormLayout,
                             QGroupBox, QTabWidget, QProgressBar)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from ui.base_arm import BaseArmWindow, StyledComboBox


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
        db_indicator = QLabel("● Працює")
        db_indicator.setStyleSheet("color: #50FA7B; font-weight: bold;")
        db_status.addStretch()
        db_status.addWidget(db_indicator)
        serv_layout.addLayout(db_status)

        layout.addWidget(servers_group)

        backup_group = QGroupBox("Резервне копіювання")
        back_lay = QVBoxLayout(backup_group)
        back_lay.addWidget(QLabel("Останній бекап: Сьогодні о 03:00"))

        progress_lay = QHBoxLayout()
        progress_lay.addWidget(QLabel("Місце на диску для бекапів:"))
        pbar = QProgressBar()
        pbar.setValue(45)
        pbar.setStyleSheet(
            "QProgressBar { border: 1px solid #44475A; border-radius: 5px; text-align: center; color: white; } "
            "QProgressBar::chunk { background-color: #8B5CF6; }")
        progress_lay.addWidget(pbar)
        back_lay.addLayout(progress_lay)

        btn_backup = self.create_action_button("Створити бекап зараз")
        back_lay.addWidget(btn_backup, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addWidget(backup_group)
        layout.addStretch()
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
        top_bar.addWidget(btn_add)
        layout.addLayout(top_bar)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(4)
        self.users_table.setHorizontalHeaderLabels(["ID", "Роль", "Повне ім'я", "Електронна пошта"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.users_table.setRowCount(0)

        filters = self.create_table_filters(self.users_table)
        layout.addWidget(filters)
        layout.addWidget(self.users_table)

        actions = QHBoxLayout()
        actions.addWidget(self.create_action_button("Редагувати дані"))
        actions.addWidget(self.create_action_button("Скинути пароль"))
        btn_block = self.create_action_button("Видалити", danger=True)
        actions.addWidget(btn_block)
        actions.addStretch()
        layout.addLayout(actions)

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

        version = QLabel("Версія 1.0.11")
        version.setStyleSheet("font-size: 14px;")
        layout.addWidget(version, alignment=Qt.AlignmentFlag.AlignCenter)

        return page