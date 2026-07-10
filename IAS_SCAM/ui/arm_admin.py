import os
import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem,
                             QHeaderView, QLineEdit, QFormLayout,
                             QGroupBox, QTabWidget, QProgressBar, QMessageBox,
                             QInputDialog, QDialog, QDialogButtonBox, QTextEdit)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QShortcut, QKeySequence
from ui.base_arm import BaseArmWindow, StyledComboBox

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import services.user_service as us
import services.monitoring_service as ms
import services.dictionary_service as ds
import services.audit_service as audit_service


class DirectoryDialog(QDialog):
    """Діалогове вікно для створення та редагування записів у системних довідниках."""

    def __init__(self, parent=None, tab_index=0, current_data=None):
        super().__init__(parent)
        self.tab_index = tab_index
        self.setWindowTitle("Редагувати запис" if current_data else "Додати новий запис")
        self.setFixedSize(380, 260)
        self.setStyleSheet("font-size: 14px;")

        layout = QVBoxLayout(self)
        self.form = QFormLayout()
        self.inputs = {}

        if tab_index in (0, 4, 5, 6, 7):
            self.inputs["name"] = QLineEdit()
            self.form.addRow("Назва:", self.inputs["name"])
            if current_data:
                self.inputs["name"].setText(current_data.get("name", ""))

        elif tab_index == 1:
            self.inputs["category_combo"] = StyledComboBox()
            try:
                self.cats = ds.get_categories()
                for c in self.cats:
                    self.inputs["category_combo"].addItem(c["name"], c["id"])
            except Exception as e:
                print(f"Помилка завантаження категорій у діалог: {e}")

            self.inputs["incident_name"] = QLineEdit()
            self.form.addRow("Категорія системи:", self.inputs["category_combo"])
            self.form.addRow("Назва типу аварії:", self.inputs["incident_name"])

            if current_data:
                self.inputs["incident_name"].setText(current_data.get("incident_name", ""))
                idx = self.inputs["category_combo"].findText(current_data.get("category_name", ""))
                if idx >= 0:
                    self.inputs["category_combo"].setCurrentIndex(idx)

        elif tab_index == 2:
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

        elif tab_index == 3:
            self.inputs["crew_number"] = QLineEdit()
            self.inputs["category_combo"] = StyledComboBox()
            try:
                self.cats = ds.get_categories()
                for c in self.cats:
                    self.inputs["category_combo"].addItem(c["name"], c["id"])
            except Exception as e:
                print(f"Помилка завантаження спеціалізацій бригад: {e}")

            self.inputs["status_combo"] = StyledComboBox()
            try:
                self.statuses = ds.get_crew_statuses()
                for s in self.statuses:
                    self.inputs["status_combo"].addItem(s["name"], s["id"])
            except Exception as e:
                print(f"Помилка завантаження статусів бригад: {e}")

            self.form.addRow("Номер бригади:", self.inputs["crew_number"])
            self.form.addRow("Спеціалізація:", self.inputs["category_combo"])
            self.form.addRow("Поточний статус:", self.inputs["status_combo"])

            if current_data:
                self.inputs["crew_number"].setText(current_data.get("crew_number", ""))
                idx_cat = self.inputs["category_combo"].findText(current_data.get("category_name", ""))
                if idx_cat >= 0:
                    self.inputs["category_combo"].setCurrentIndex(idx_cat)
                idx_stat = self.inputs["status_combo"].findText(current_data.get("status", ""))
                if idx_stat >= 0:
                    self.inputs["status_combo"].setCurrentIndex(idx_stat)

        layout.addLayout(self.form)
        self.btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        btn_ok = self.btns.button(QDialogButtonBox.StandardButton.Ok)
        if btn_ok:
            btn_ok.setDefault(True)

        self.btns.accepted.connect(self.accept)
        self.btns.rejected.connect(self.reject)
        layout.addWidget(self.btns)

    def get_data(self):
        """Збирає введені в діалоговому вікні дані та повертає структурований словник."""
        res = {}
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

        return res
    
    def accept(self):
        """Перевизначений метод підтвердження для валідації даних перед закриттям діалогу."""
        if self.tab_index == 2 and "price" in self.inputs:
            price_text = self.inputs["price"].text().strip()
            
            if "," in price_text:
                QMessageBox.warning(self, "Помилка введення", "Ціну потрібно вводити через крапку, а не через кому (наприклад: 12.50)!")
                return
                
            try:
                if price_text:
                    float(price_text)
            except ValueError:
                QMessageBox.warning(self, "Помилка введення", "Введено некоректний формат ціни! Використовуйте лише цифри та крапку.")
                return

        super().accept()


class UserDialog(QDialog):
    """Діалогове вікно створення та редагування облікових записів користувачів."""

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
            print(f"Помилка завантаження системних ролей: {e}")

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
        btn_ok = self.btns.button(QDialogButtonBox.StandardButton.Ok)
        if btn_ok:
            btn_ok.setDefault(True)

        self.btns.accepted.connect(self.accept)
        self.btns.rejected.connect(self.reject)
        layout.addWidget(self.btns)

        if user_data:
            self.name_input.setText(user_data['full_name'])
            self.email_input.setText(user_data['email'])
            idx = self.role_combo.findText(user_data['role_name'])
            if idx >= 0:
                self.role_combo.setCurrentIndex(idx)

    def get_data(self):
        """Повертає інформацію про користувача, введену в поля діалогу."""
        data = {
            "role_id": self.role_combo.currentData(),
            "full_name": self.name_input.text().strip(),
            "email": self.email_input.text().strip()
        }
        if self.password_input:
            data["password"] = self.password_input.text().strip()
        return data


class ArmAdminWindow(BaseArmWindow):
    """Головне вікно автоматизованого робочого місця (АРМ) адміністратора системи."""

    def __init__(self, user_id=1):
        super().__init__("АРМ Адміністратора системи")
        self.current_admin_id = user_id
        self.setup_menu()
        self.init_static_table_filters()
        self.refresh_all_data()

        self.shortcut_refresh = QShortcut(QKeySequence("F5"), self)
        self.shortcut_refresh.activated.connect(self.refresh_all_data)

        self.shortcut_delete_user = QShortcut(QKeySequence("Delete"), self.users_table)
        self.shortcut_delete_user.activated.connect(self.action_delete_user)

        # 🚀 ДОДАНО СЮДИ: Гаряча клавіша для видалення елементів з довідників працюватиме прямо на вкладках!
        self.shortcut_delete_dir = QShortcut(QKeySequence("Delete"), self.directory_tabs)
        self.shortcut_delete_dir.activated.connect(self.action_delete_directory_item)

    def get_help_data(self):
        return {
            "Головне про модуль": """
                <h3>АРМ Адміністратора системи</h3>
                <p>Це центральний пульт керування всією інформаційною системою. Модуль надає адміністратору інструменти для повного контролю над користувачами, системними довідниками, безпекою та технічним станом інфраструктури.</p>
                <p>Основна мета АРМ — забезпечити стабільну, безпечну та коректну роботу всіх компонентів комплексу.</p>
            """,
            "Моніторинг стану": """
                <h3>Моніторинг технічного стану</h3>
                <p>Ця вкладка є дашбордом, що в реальному часі відображає ключові показники працездатності системи.</p>
                <ul>
                    <li><b>Сервер бази даних:</b> Індикатор показує, чи є зв'язок із сервером PostgreSQL. Перевірка відбувається автоматично кожні 3 секунди. Зелений колір означає, що все гаразд, червоний — є проблеми з підключенням.</li>
                    <li><b>Резервне копіювання:</b> Відображає дату й час створення останньої резервної копії. Кнопка <b>«Створити бекап зараз»</b> дозволяє негайно виконати повний дамп бази даних (схеми та даних) у спеціальну директорію на сервері.</li>
                    <li><b>Місце на диску:</b> Прогрес-бар візуалізує відсоток використання дискового простору на сервері, де зберігаються бекапи. Нижче вказано точний обсяг вільного місця в кілобайтах.</li>
                </ul>
            """,
            "Управління користувачами": """
                <h3>Користувачі та Ролі</h3>
                <p>Розділ для адміністрування персоналу, що має доступ до системи. Ви можете створювати, редагувати та видаляти облікові записи.</p>
                <ul>
                    <li><b>Додавання:</b> Кнопка <b>"Додати користувача"</b> відкриває діалог для створення нового облікового запису. Необхідно вказати роль, ПІБ, email (логін) та тимчасовий пароль.</li>
                    <li><b>Редагування:</b> Оберіть користувача в таблиці та натисніть <b>"Редагувати дані"</b>. Можна змінити ПІБ, email та роль.</li>
                    <li><b>Скидання пароля:</b> Якщо працівник забув пароль, оберіть його та натисніть <b>"Скинути пароль"</b>. Система запросить ввести новий пароль, не вимагаючи старого.</li>
                    <li><b>Видалення:</b> Оберіть користувача та натисніть <b>"Видалити"</b> (або клавішу <b>Delete</b> на клавіатурі). Обліковий запис буде не видалено фізично, а деактивовано (soft delete), щоб зберегти цілісність даних у журналі аудиту.</li>
                </ul>
            """,
            "Ведення довідників": {
                "Загальні правила": """
                    <h3>Робота з довідниками</h3>
                    <p>Довідники — це основа всієї системи. Дані з них (наприклад, статуси, категорії, матеріали) використовуються для заповнення випадаючих списків у всіх АРМах. Коректне ведення довідників забезпечує узгодженість даних.</p>
                    <p>Для роботи з довідниками оберіть потрібну вкладку, виділіть рядок у таблиці та скористайтесь кнопками <b>"Додати"</b>, <b>"Редагувати"</b> або <b>"Видалити"</b>. Видалення запису можливе лише в тому випадку, якщо він не використовується в інших таблицях (наприклад, не можна видалити статус "В роботі", якщо є заявки з таким статусом).</p>
                """,
                "Опис вкладок": """
                    <ul>
                        <li><b>Категорії та Типи аварій:</b> Формують ієрархію проблем (наприклад, "Сантехніка" -> "Прорив труби").</li>
                        <li><b>Матеріали:</b> База ТМЦ з вказанням одиниць виміру та вартості для списання при ремонті.</li>
                        <li><b>Бригади:</b> Перелік робочих груп. Для бригади обов'язково вказується спеціалізація (категорія) та статус (Вільна/Зайнята).</li>
                        <li><b>Ролі, Статуси, Критичність:</b> Базові системні довідники, що визначають логіку роботи системи. Редагування деяких з них може бути обмежено.</li>
                    </ul>
                """
            },
            "Журнал дій (Аудит)": """
                <h3>Журнал дій користувачів</h3>
                <p>Система веде безперервний запис всіх значущих дій, які виконують користувачі (створення, редагування, видалення записів, вхід у систему тощо). Це ключовий інструмент для забезпечення безпеки та розслідування інцидентів.</p>
                <ul>
                    <li><b>Перегляд деталей:</b> Якщо дані в колонках "Старе значення" або "Нове значення" занадто довгі, зробіть по них <b>подвійний клік</b>. Відкриється зручне вікно для перегляду повного тексту.</li>
                    <li><b>Кольорова індикація:</b> Для швидкого візуального аналізу, рядки в таблиці підсвічуються кольором залежно від типу дії:
                        <br>• <span style='color:#50FA7B;'>Зелений</span> — створення (INSERT), <span style='color:#FF5555;'>Червоний</span> — видалення/блокування (DELETE), <span style='color:#FFB86C;'>Помаранчевий</span> — зміна пароля.</li>
                    <li><b>Експорт:</b> Кнопка <b>"📋 Експорт журналу"</b> дозволяє зберегти всі відфільтровані на екрані події у детальний текстовий звіт (.txt) для подальшого аналізу або архівації.</li>
                </ul>
            """,
            "Настройки системи": """
                <h3>Глобальні конфігурації</h3>
                <p>Тут зібрані налаштування, що впливають на всю систему.</p>
                <ul>
                    <li><b>Назва підприємства:</b> Використовується при генерації офіційних звітів.</li>
                    <li><b>Частота авто-бекапів:</b> Дозволяє налаштувати, як часто серверний процес буде автоматично створювати резервні копії бази даних. Можна обрати готовий інтервал (наприклад, "Щодня") або задати свій у хвилинах.</li>
                </ul>
                <p>Ці налаштування зберігаються у спільному файлі `backup_settings.json` на сервері.</p>
            """,
            "Гарячі клавіші": """
                <h3>Гарячі клавіші</h3>
                <p>Для прискорення роботи ви можете використовувати наступні комбінації клавіш:</p>
                <ul>
                    <li><b>F1</b> — Відкрити цю довідку.</li>
                    <li><b>F5</b> — Примусово оновити дані на всіх вкладках.</li>
                    <li><b>Delete</b> — Видалити вибраний запис (працює на вкладці "Управління користувачами" та на всіх вкладках довідників).</li>
                    <li><b>Ctrl+T</b> — Змінити тему оформлення (світла/темна).</li>
                    <li><b>Ctrl+Q</b> — Вийти з поточного робочого місця (АРМ).</li>
                </ul>
            """
        }

    def setup_menu(self):
        """Ініціалізує навігаційне меню адміністратора та пов'язані сторінки."""
        self.add_menu_item("Моніторинг стану", self.build_monitoring_page())
        self.add_menu_item("Управління користувачами", self.build_users_page())
        self.add_menu_item("Ведення довідників", self.build_directories_page())
        self.add_menu_item("Журнал дій", self.build_audit_page())
        self.add_menu_item("Настройки системи", self.build_settings_page())
        self.finalize_menu()

    def clear_layout(self, layout):
        """Рекурсивно очищує макет від віджетів для динамічної зміни фільтрів."""
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

    def build_monitoring_page(self):
        """Створює інтерфейс сторінки моніторингу працездатності серверів."""
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

        self.lbl_free_space = QLabel("Вільне місце на сервері: Перевірка...")
        self.lbl_free_space.setStyleSheet("color: #A6ADC8; font-size: 13px; font-weight: 500; margin-top: -5px;")
        back_lay.addWidget(self.lbl_free_space)

        btn_backup = self.create_action_button("💾 Створити бекап зараз")
        btn_backup.clicked.connect(self.action_run_backup)
        back_lay.addWidget(btn_backup, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addWidget(backup_group)
        layout.addStretch()

        self.monitor_timer = QTimer(self)
        self.monitor_timer.timeout.connect(self.refresh_monitoring_data)
        self.monitor_timer.start(3000)
        return page

    def build_users_page(self):
        """Будує сторінку управління системними облікових записами."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Управління користувачами та ролями")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        top_bar = QHBoxLayout()
        top_bar.addStretch()
        btn_add = self.create_action_button("➕ Додати користувача", primary=True)
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
        btn_edit = self.create_action_button("✏️ Редагувати дані")
        btn_edit.clicked.connect(self.action_edit_user)
        actions.addWidget(btn_edit)

        btn_reset = self.create_action_button("🔑 Скинути пароль")
        btn_reset.clicked.connect(self.action_reset_password)
        actions.addWidget(btn_reset)

        btn_block = self.create_action_button("🗑️ Видалити", danger=True)
        btn_block.clicked.connect(self.action_delete_user)
        actions.addWidget(btn_block)

        actions.addStretch()
        layout.addLayout(actions)
        return page

    def build_directories_page(self):
        """Створює багатоокладковий інтерфейс для ведення нормативно-довідкової інформації."""
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

        tab_cat = QWidget()
        cat_lay = QVBoxLayout(tab_cat)
        self.table_cat = QTableWidget()
        self.table_cat.setColumnCount(2)
        self.table_cat.setHorizontalHeaderLabels(["Код", "Назва категорії"])
        self.table_cat.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        cat_lay.addLayout(self.lay_filter_cat)
        cat_lay.addWidget(self.table_cat)
        self.directory_tabs.addTab(tab_cat, "Категорії")

        tab_issues = QWidget()
        iss_lay = QVBoxLayout(tab_issues)
        self.table_issues = QTableWidget()
        self.table_issues.setColumnCount(3)
        self.table_issues.setHorizontalHeaderLabels(["Код", "Категорія", "Назва аварії"])
        self.table_issues.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        iss_lay.addLayout(self.lay_filter_issues)
        iss_lay.addWidget(self.table_issues)
        self.directory_tabs.addTab(tab_issues, "Типи аварій")

        tab_mat = QWidget()
        mat_lay = QVBoxLayout(tab_mat)
        self.table_mat = QTableWidget()
        self.table_mat.setColumnCount(4)
        self.table_mat.setHorizontalHeaderLabels(["Код", "Назва матеріалу", "Од. виміру", "Ціна"])
        self.table_mat.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        mat_lay.addLayout(self.lay_filter_mat)
        mat_lay.addWidget(self.table_mat)
        self.directory_tabs.addTab(tab_mat, "Матеріали")

        tab_crew = QWidget()
        crew_lay = QVBoxLayout(tab_crew)
        self.table_crew = QTableWidget()
        self.table_crew.setColumnCount(4)
        self.table_crew.setHorizontalHeaderLabels(["Код", "Номер бригади", "Категорія", "Статус"])
        self.table_crew.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        crew_lay.addLayout(self.lay_filter_crew)
        crew_lay.addWidget(self.table_crew)
        self.directory_tabs.addTab(tab_crew, "Бригади")

        tab_roles = QWidget()
        roles_lay = QVBoxLayout(tab_roles)
        self.table_roles = QTableWidget()
        self.table_roles.setColumnCount(2)
        self.table_roles.setHorizontalHeaderLabels(["Код", "Назва ролі"])
        self.table_roles.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        roles_lay.addLayout(self.lay_filter_roles)
        roles_lay.addWidget(self.table_roles)
        self.directory_tabs.addTab(tab_roles, "Ролі")

        tab_status = QWidget()
        status_lay = QVBoxLayout(tab_status)
        self.table_status = QTableWidget()
        self.table_status.setColumnCount(2)
        self.table_status.setHorizontalHeaderLabels(["Код", "Назва статусу"])
        self.table_status.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        status_lay.addLayout(self.lay_filter_status)
        status_lay.addWidget(self.table_status)
        self.directory_tabs.addTab(tab_status, "Статуси заявок")

        tab_crit = QWidget()
        crit_lay = QVBoxLayout(tab_crit)
        self.table_crit = QTableWidget()
        self.table_crit.setColumnCount(2)
        self.table_crit.setHorizontalHeaderLabels(["Код", "Рівень критичності"])
        self.table_crit.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        crit_lay.addLayout(self.lay_filter_crit)
        crit_lay.addWidget(self.table_crit)
        self.directory_tabs.addTab(tab_crit, "Критичність")

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

        def inject_action_buttons(tab_layout):
            dir_btns = QHBoxLayout()
            btn_add = self.create_action_button("➕ Додати запис")
            btn_add.clicked.connect(self.action_add_directory_item)
            dir_btns.addWidget(btn_add)

            btn_edit = self.create_action_button("✏️ Редагувати")
            btn_edit.clicked.connect(self.action_edit_directory_item)
            dir_btns.addWidget(btn_edit)

            btn_del = self.create_action_button("🗑️ Видалити", danger=True)
            btn_del.clicked.connect(self.action_delete_directory_item)
            dir_btns.addWidget(btn_del)

            dir_btns.addStretch()
            tab_layout.addLayout(dir_btns)

        inject_action_buttons(cat_lay)
        inject_action_buttons(iss_lay)
        inject_action_buttons(mat_lay)
        inject_action_buttons(crew_lay)
        inject_action_buttons(crit_lay)
        inject_action_buttons(crew_stat_lay)

        return page

    def build_audit_page(self):
        """Ініціалізує сторінку перегляду логів та журналу аудиту операцій."""
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
        self.table_audit.cellDoubleClicked.connect(self.show_full_audit_value)

        self.lay_filter_audit = QVBoxLayout()
        layout.addLayout(self.lay_filter_audit)
        layout.addWidget(self.table_audit)

        btn_export = self.create_action_button("📋 Експорт журналу", primary=True)
        btn_export.clicked.connect(self.action_export_audit_log)
        layout.addWidget(btn_export, alignment=Qt.AlignmentFlag.AlignRight)
        return page

    def build_settings_page(self):
        """Формує сторінку глобальної конфігурації системи та параметрів автоматичного бекапу."""
        import json
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        group = QGroupBox("Глобальні конфігурації та авто-бекап")
        form = QFormLayout(group)

        self.config_path = os.getenv("SHARED_BACKUP_CONFIG", "backup_settings.json")

        config_data = {
            "company_name": "КП 'Київжитлоспецексплуатація'",
            "mode": "Щодня",
            "custom_minutes": 1
        }

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except:
                pass

        self.le_name = QLineEdit()
        self.le_name.setPlaceholderText("КП 'Київжитлоспецексплуатація'")
        self.le_name.setText(config_data.get("company_name", "КП 'Київжитлоспецексплуатація'"))

        self.le_ip = QLineEdit()
        self.le_ip.setText(os.getenv("DB_HOST", "192.168.1.5"))
        self.le_ip.setEnabled(False)

        self.backup_freq = StyledComboBox()
        self.backup_freq.addItems([
            "Кожну хвилину", "Щогодини", "Кожні 12 годин",
            "Щодня", "Щотижня", "Щомісяця", "Свій інтервал (хв)"
        ])
        idx = self.backup_freq.findText(config_data.get("mode", "Щодня"))
        if idx >= 0:
            self.backup_freq.setCurrentIndex(idx)

        self.le_custom_minutes = QLineEdit()
        self.le_custom_minutes.setPlaceholderText("Введіть хвилини...")
        self.le_custom_minutes.setText(str(config_data.get("custom_minutes", 1)))

        self.backup_freq.currentTextChanged.connect(
            lambda text: self.le_custom_minutes.setEnabled(text == "Свій інтервал (хв)")
        )
        self.le_custom_minutes.setEnabled(self.backup_freq.currentText() == "Свій інтервал (хв)")

        form.addRow("Назва підприємства:", self.le_name)
        form.addRow("IP-адреса сервера (статична):", self.le_ip)
        form.addRow("Частота авто-бекапів:", self.backup_freq)
        form.addRow("Власний інтервал (хвилини):", self.le_custom_minutes)

        layout.addWidget(group)

        btn_save = self.create_action_button("💾 Зберегти настройки", primary=True)
        btn_save.clicked.connect(self.action_save_global_settings)
        self.le_name.returnPressed.connect(self.action_save_global_settings)
        self.le_custom_minutes.returnPressed.connect(self.action_save_global_settings)
        layout.addWidget(btn_save, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addStretch()
        return page

    def action_save_global_settings(self):
        """Записує конфігураційні зміни підприємства та бекапів у загальний JSON-файл."""
        import json
        company_text = self.le_name.text().strip()
        mode = self.backup_freq.currentText()
        minutes_text = self.le_custom_minutes.text().strip()

        if not company_text:
            QMessageBox.warning(self, "Увага", "Назва підприємства не може бути порожньою!")
            return

        custom_mins = 1
        if mode == "Свій інтервал (хв)":
            try:
                custom_mins = int(minutes_text)
                if custom_mins <= 0:
                    raise ValueError()
            except ValueError:
                QMessageBox.warning(self, "Помилка", "Введіть ціле число хвилин більше 0!")
                return

        new_config = {
            "company_name": company_text,
            "mode": mode,
            "custom_minutes": custom_mins
        }

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(new_config, f, ensure_ascii=False, indent=4)
            QMessageBox.information(self, "Успіх", "Глобальні налаштування комплексу успішно оновлено!")
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося записати файл конфігурації: {e}")

    def init_static_table_filters(self):
        """Ініціалізує фільтри пошуку для всіх таблиць на сторінці адміністратора."""
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
        """Виконує комплексне синхронне оновлення всіх даних АРМ."""
        try:
            self.load_users_data()
            self.load_all_directories()
            self.load_audit_data()
            self.refresh_monitoring_data()
        except Exception as e:
            print(f"Помилка наповнення даних: {e}")

    def load_users_data(self):
        """Зчитує перелік користувачів з бази та відображає їх у таблиці."""
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
        """Оновлює вміст усіх таблиць довідників із бази даних."""
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

        try:
            self.table_cat.setRowCount(0)
            for r, i in enumerate(ds.get_categories()):
                self.table_cat.insertRow(r)
                self.table_cat.setItem(r, 0, QTableWidgetItem(str(i["id"])))
                self.table_cat.setItem(r, 1, QTableWidgetItem(i["name"]))
        except Exception as e:
            print(f"Помилка категорій: {e}")

        try:
            self.table_issues.setRowCount(0)
            for r, i in enumerate(ds.get_incident_types()):
                self.table_issues.insertRow(r)
                self.table_issues.setItem(r, 0, QTableWidgetItem(str(i["id"])))
                self.table_issues.setItem(r, 1, QTableWidgetItem(i["category_name"]))
                self.table_issues.setItem(r, 2, QTableWidgetItem(i["incident_name"]))
        except Exception as e:
            print(f"Помилка типів аварій: {e}")

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

        try:
            self.table_crew.setRowCount(0)
            for r, i in enumerate(ds.get_crews()):
                self.table_crew.insertRow(r)
                self.table_crew.setItem(r, 0, QTableWidgetItem(str(i["id"])))
                self.table_crew.setItem(r, 1, QTableWidgetItem(i["crew_number"]))
                self.table_crew.setItem(r, 2, QTableWidgetItem(i["category_name"]))
                self.table_crew.setItem(r, 3, QTableWidgetItem(i["status"]))
        except Exception as e:
            print(f"Помилка brigades: {e}")

        try:
            self.table_roles.setRowCount(0)
            for r, i in enumerate(ds.get_roles()):
                self.table_roles.insertRow(r)
                self.table_roles.setItem(r, 0, QTableWidgetItem(str(i["id"])))
                self.table_roles.setItem(r, 1, QTableWidgetItem(i["name"]))
        except Exception as e:
            print(f"Помилка ролей: {e}")

        try:
            self.table_status.setRowCount(0)
            for r, i in enumerate(ds.get_statuses()):
                self.table_status.insertRow(r)
                self.table_status.setItem(r, 0, QTableWidgetItem(str(i["id"])))
                self.table_status.setItem(r, 1, QTableWidgetItem(i["name"]))
        except Exception as e:
            print(f"Помилка статусів: {e}")

        try:
            self.table_crit.setRowCount(0)
            for r, i in enumerate(ds.get_criticalities()):
                self.table_crit.insertRow(r)
                self.table_crit.setItem(r, 0, QTableWidgetItem(str(i["id"])))
                self.table_crit.setItem(r, 1, QTableWidgetItem(i["name"]))
        except Exception as e:
            print(f"Помилка критичності: {e}")

        try:
            self.table_crew_status.setRowCount(0)
            for r, i in enumerate(ds.get_crew_statuses()):
                self.table_crew_status.insertRow(r)
                self.table_crew_status.setItem(r, 0, QTableWidgetItem(str(i["id"])))
                self.table_crew_status.setItem(r, 1, QTableWidgetItem(i["name"]))
        except Exception as e:
            print(f"Помилка статусів бригад: {e}")

        for table in (self.table_cat, self.table_issues, self.table_mat, self.table_crew,
                      self.table_roles, self.table_status, self.table_crit, self.table_crew_status):
            for row in range(table.rowCount()):
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    if item:
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

    def load_audit_data(self):
        """Зчитує дані з бази та наповнює таблицю Журналу дій користувачів."""
        try:
            self.clear_layout(self.lay_filter_audit)
            self.lay_filter_audit.addWidget(self.create_table_filters(self.table_audit))

            logs_data = audit_service.get_all_audit_logs()
            self.table_audit.setRowCount(0)

            color_map = {
                "delete": QColor("#552222") if self.is_dark_theme else QColor("#FFCCCC"),
                "insert": QColor("#1A3C1A") if self.is_dark_theme else QColor("#E5FFE5"),
                "password": QColor("#553C1A") if self.is_dark_theme else QColor("#FFE5CC"),
                "default": QColor("transparent")
            }

            for row_idx, log in enumerate(logs_data):
                self.table_audit.insertRow(row_idx)

                event_lower = log["event"].lower()
                if "delete" in event_lower or "block" in event_lower: row_color = color_map["delete"]
                elif "insert" in event_lower or "add" in event_lower: row_color = color_map["insert"]
                elif "password" in event_lower: row_color = color_map["password"]
                else: row_color = color_map["default"]

                row_items = [str(log["id"]), log["user_name"], log["time"], log["event"], log["table"], log["old_val"], log["new_val"]]
                for col_idx, cell_data in enumerate(row_items):
                    item = QTableWidgetItem(cell_data)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item.setBackground(row_color)
                    self.table_audit.setItem(row_idx, col_idx, item)

        except Exception as e:
            print(f"Помилка рендеру журналу дій: {e}")

    def action_export_audit_log(self):
        """Експортує відфільтровані записи журналу логування в текстовий звіт."""
        import datetime
        from PyQt6.QtWidgets import QFileDialog, QMessageBox

        if self.table_audit.rowCount() == 0:
            QMessageBox.warning(self, "Увага", "Журнал дій порожній, немає чого експортувати!")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Зберегти звіт аудиту", f"audit_report_{datetime.date.today()}.txt", "Текстові файли (*.txt)"
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("=" * 90 + "\n")
                f.write(f" 📑 ПОВНИЙ ЗВІТ ПРО ДІЇ КОРИСТУВАЧІВ ІНФРАСТРУКТУРИ СКАМ\n")
                f.write(f" Сформовано: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                f.write("=" * 90 + "\n\n")

                exported_count = 0
                for row in range(self.table_audit.rowCount()):
                    if self.table_audit.isRowHidden(row):
                        continue

                    log_id = self.table_audit.item(row, 0).text()
                    user = self.table_audit.item(row, 1).text()
                    log_time = self.table_audit.item(row, 2).text()
                    event = self.table_audit.item(row, 3).text()
                    table_name = self.table_audit.item(row, 4).text()
                    old_val = self.table_audit.item(row, 5).text()
                    new_val = self.table_audit.item(row, 6).text()

                    f.write(f"Запис логу ID: {log_id}\n")
                    f.write(f"------------------------------------------------------------------------\n")
                    f.write(f"• Користувач: {user}\n")
                    f.write(f"• Час події:  {log_time}\n")
                    f.write(f"• Тип дії:    {event}\n")
                    f.write(f"• Об'єкт/Поле: {table_name}\n")
                    f.write(f"• Було (Old):  {old_val}\n")
                    f.write(f"• Стало (New): {new_val}\n")
                    f.write(f"========================================================================\n\n")

                    exported_count += 1

                f.write(f"Всього вивантажено записів: {exported_count}\n")

            QMessageBox.information(self, "Успіх",
                                    f"Журнал дій успішно експортовано! Вивантажено записів: {exported_count}")
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося зберегти звіт: {e}")

    def on_menu_click(self, index, btn):
        """Перехоплює натискання меню для оновлення журналу аудиту в реальному часі."""
        super().on_menu_click(index, btn)
        if index == 3:
            self.load_audit_data()

    def action_delete_user(self):
        """Видаляє (деактивує) вибраного користувача із системи з логуванням дії."""
        selected_rows = self.users_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Увага", "Спочатку оберіть користувача в таблиці!")
            return
        row = selected_rows[0].row()
        user_id = int(self.users_table.item(row, 0).text())
        reply = QMessageBox.question(self, "Підтвердження", "Ви впевнені, що хочете видалити цього користувача?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = us.delete_user(user_id, self.current_admin_id)
            if success:
                self.load_users_data()
            else:
                QMessageBox.critical(self, "Помилка", msg)

    def get_selected_user_id(self):
        """Повертає ID користувача, виділеного у головній таблиці."""
        selected_rows = self.users_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Увага", "Будь ласка, оберіть користувача в таблиці.")
            return None
        return int(self.users_table.item(selected_rows[0].row(), 0).text())

    def action_add_user(self):
        """Ініціалізує процес додавання нового користувача через діалогову форму."""
        dialog = UserDialog(self)
        dialog.setStyleSheet(self.styleSheet())
        if dialog.exec():
            data = dialog.get_data()
            if not data["full_name"] or not data["password"]:
                QMessageBox.warning(self, "Помилка", "ПІБ та Пароль є обов'язковими!")
                return
            success, msg = us.add_user(data["role_id"], data["full_name"], data["email"], data["password"],
                                       self.current_admin_id)
            if success:
                self.load_users_data()
            else:
                QMessageBox.critical(self, "Помилка", msg)

    def action_edit_user(self):
        """Запускає редагування параметрів існуючого користувача."""
        user_id = self.get_selected_user_id()
        if not user_id:
            return
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
            success, msg = us.update_user(user_id, data["role_id"], data["full_name"], data["email"],
                                          self.current_admin_id)
            if success:
                self.load_users_data()
            else:
                QMessageBox.critical(self, "Помилка", msg)

    def action_reset_password(self):
        """Встановлює новий пароль для облікового запису користувача."""
        user_id = self.get_selected_user_id()
        if not user_id:
            return
        new_password, ok = QInputDialog.getText(self, "Скидання пароля", "Введіть новий пароль:",
                                                QLineEdit.EchoMode.Password)
        if ok and new_password.strip():
            success, msg = us.reset_password(user_id, new_password.strip(), self.current_admin_id)
            if success:
                QMessageBox.information(self, "Успіх", msg)
            else:
                QMessageBox.critical(self, "Помилка", msg)

    def refresh_monitoring_data(self):
        """Оновлює показники стану бази даних, зайнятого дискового простору та вільного місця."""
        try:
            if ms.check_db_status():
                self.db_indicator.setText("● Працює")
                self.db_indicator.setStyleSheet("color: #50FA7B; font-weight: bold;")
            else:
                self.db_indicator.setText("● Відключено")
                self.db_indicator.setStyleSheet("color: #FF5555; font-weight: bold;")

            self.pbar.setValue(ms.get_disk_usage_percent())

            free_kb = ms.get_disk_free_kb()
            formatted_kb = f"{free_kb:,}".replace(",", " ")
            self.lbl_free_space.setText(f"Вільне місце на сервері: {formatted_kb} КБ")

        except Exception as e:
            print(f"Помилка таймера моніторингу: {e}")

    def action_run_backup(self):
        """Виконує створення повної резервної копії бази даних у ручному режимі."""
        success, message = ms.create_system_backup()
        if success:
            self.lbl_backup_time.setText(f"Останній бекап: {ms.get_last_backup_time()}")
            QMessageBox.information(self, "Успіх", message)
            self.refresh_monitoring_data()
        else:
            QMessageBox.critical(self, "Помилка", message)

    def get_active_directory_table_and_index(self):
        """Повертає індекс та об'єкт поточної відкритої таблиці довідника."""
        idx = self.directory_tabs.currentIndex()
        tables = {
            0: self.table_cat, 1: self.table_issues, 2: self.table_mat,
            3: self.table_crew, 4: self.table_roles,
            5: self.table_status, 6: self.table_crit, 7: self.table_crew_status
        }
        return idx, tables.get(idx)

    def action_add_directory_item(self):
        """Додає новий запис у поточний активний системний довідник."""
        tab_idx, table = self.get_active_directory_table_and_index()
        dialog = DirectoryDialog(self, tab_index=tab_idx)
        dialog.setStyleSheet(self.styleSheet())
        if dialog.exec():
            success, msg = ds.save_directory_item(tab_idx, dialog.get_data(), admin_id=self.current_admin_id)
            if success:
                self.load_all_directories()
            else:
                QMessageBox.critical(self, "Помилка", msg)

    def action_edit_directory_item(self):
        """Редагує вибраний рядок активного системного довідника."""
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
            current_data["status"] = table.item(row, 3).text()

        dialog = DirectoryDialog(self, tab_index=tab_idx, current_data=current_data)
        dialog.setStyleSheet(self.styleSheet())
        if dialog.exec():
            success, msg = ds.save_directory_item(tab_idx, dialog.get_data(), item_id=item_id,
                                                  admin_id=self.current_admin_id)
            if success:
                self.load_all_directories()
            else:
                QMessageBox.critical(self, "Помилка", msg)

    def action_delete_directory_item(self):
        """Остаточно вилучає запис із активного довідника, якщо немає обмежень цілісності БД."""
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
            success, msg = ds.delete_directory_item(tab_idx, item_id, self.current_admin_id)
            if success:
                self.load_all_directories()
            else:
                QMessageBox.critical(self, "Обмеження видалення", msg)

    def show_full_audit_value(self, row, col):
        """Відкриває детальне модальне вікно для зручного читання логів старого/нового стану полів."""
        if col not in (5, 6):
            return

        item = self.table_audit.item(row, col)
        if not item:
            return

        text_content = item.text().strip()
        if not text_content or text_content == "—":
            return

        col_header = "Старе значення змін" if col == 5 else "Нове значення змін"

        dialog = QDialog(self)
        dialog.setWindowTitle(col_header)
        dialog.resize(550, 380)

        lay = QVBoxLayout(dialog)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(15)

        title = QLabel(f"Повний технічний зліпок події (Рядок ID: {self.table_audit.item(row, 0).text()}):")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #8B5CF6;")

        text_edit = QTextEdit()
        text_edit.setPlainText(text_content)
        text_edit.setReadOnly(True)

        if self.is_dark_theme:
            dialog.setStyleSheet("QDialog { background-color: #282A36; color: #F8F8F2; }")
            text_edit.setStyleSheet(
                "background-color: #1E1E2E; color: #F8F8F2; border: 1px solid #44475A; border-radius: 6px; padding: 10px; font-size: 14px;"
            )
        else:
            dialog.setStyleSheet("QDialog { background-color: #F8F9FA; color: #2C3E50; }")
            text_edit.setStyleSheet(
                "background-color: #FFFFFF; color: #2C3E50; border: 1px solid #DEE2E6; border-radius: 6px; padding: 10px; font-size: 14px;"
            )

        btn_close = self.create_action_button("Закрити", primary=True)
        btn_close.clicked.connect(dialog.accept)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)

        lay.addWidget(title)
        lay.addWidget(text_edit)
        lay.addLayout(btn_layout)

        dialog.exec()