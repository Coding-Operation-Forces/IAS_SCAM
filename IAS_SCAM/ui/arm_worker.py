from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QHeaderView, QTextEdit, QCompleter, QMenu,
                             QFormLayout, QGroupBox, QScrollArea, QMessageBox, QTableWidgetItem, QLineEdit, QDialog)
from PyQt6.QtCore import Qt, QTimer, QStringListModel, QPoint, QUrl
from PyQt6.QtGui import QColor, QShortcut, QKeySequence, QIcon
from PyQt6.QtWebEngineWidgets import QWebEngineView

from ui.base_arm import BaseArmWindow, StyledComboBox
from services import worker_service, dictionary_service
from services.api_service import AddressSearchThread, load_address_cache


class ArmWorkerWindow(BaseArmWindow):
    """Робоче місце оператора/диспетчера для швидкої реєстрації та обробки аварійних заявок."""
    
    def __init__(self, user_id=None):
        super().__init__("АРМ Працівника комунального підприємства")
        self.user_id = user_id
        self.issue_mapping = {}
        self.show_all_mode = False
        self.current_applicant_id = None
        self.map_window = None 
        
        self.address_thread = AddressSearchThread()
        self.address_thread.results_ready.connect(self.update_address_completer)
        
        self.address_timer = QTimer()
        self.address_timer.setSingleShot(True)
        self.address_timer.timeout.connect(self.trigger_address_search)

        self.setup_menu()
        
        self.issue_mapping = worker_service.get_issue_mapping()
        if hasattr(self, 'combo_cat') and self.issue_mapping:
            self.combo_cat.blockSignals(True)
            self.combo_cat.clear()
            self.combo_cat.addItems(list(self.issue_mapping.keys()))
            self.combo_cat.blockSignals(False)
            if self.combo_cat.count() > 0:
                self.update_issue_types(self.combo_cat.currentText())

        self.refresh_requests_table()
        self.refresh_works_table()

        self.data_refresh_timer = QTimer(self)
        self.data_refresh_timer.timeout.connect(self.silent_refresh)
        self.data_refresh_timer.start(30000)

        self.shortcut_refresh = QShortcut(QKeySequence("F5"), self)
        self.shortcut_refresh.activated.connect(self.silent_refresh)
        
        self.shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save.activated.connect(self.save_table_changes)

    def get_help_data(self):
        return {
            "Головне про модуль": """
                <h3>АРМ Працівника / Диспетчера</h3>
                <p>Це основне робоче місце для оперативного прийому та обробки звернень від населення, призначення ремонтних бригад на об'єкти та фіксації витрачених матеріалів для подальшої фінансової звітності.</p>
                <p>Модуль розроблено для максимальної автоматизації та прискорення рутинних операцій диспетчера.</p>
            """,
            "Перегляд та обробка звернень": {
                "Загальний опис": """
                    <h3>Диспетчеризація та моніторинг</h3>
                    <p>Це головний екран модуля, де у вигляді таблиці представлені всі аварійні заявки. Він слугує для моніторингу поточного стану робіт та оперативного керування бригадами.</p>
                    <ul>
                        <li><b>Автоматичне оновлення:</b> Дані в таблиці оновлюються самостійно кожні 30 секунд, щоб ви завжди бачили актуальну картину. Також можна оновити дані примусово, натиснувши кнопку <b>"🔄 Оновити список"</b> або клавішу <b>F5</b>.</li>
                        <li><b>Режими перегляду:</b> За замовчуванням таблиця показує лише активні заявки (нові та в роботі). Щоб переглянути архів, включно з виконаними та скасованими, натисніть кнопку <b>"👁️ Показати всі заявки"</b>.</li>
                    </ul>
                """,
                "Редагування та взаємодія": """
                    <h3>Редагування та взаємодія</h3>
                    <ul>
                        <li><b>Швидке редагування:</b> Ви можете змінювати <b>Статус</b> заявки та призначати на неї <b>Бригаду</b> прямо в таблиці, обираючи потрібні значення з випадаючих списків. Після внесення змін обов'язково натисніть кнопку <b>"💾 Зберегти зміни"</b> (або <b>Ctrl+S</b>), щоб записати їх у базу даних.</li>
                        <li><b>Кольорова індикація:</b> Рядки в таблиці підсвічуються різними кольорами залежно від рівня критичності для швидкого візуального розпізнавання пріоритетних завдань:
                            <br><span style='color:red;'>■</span> - Критична, <span style='color:orange;'>■</span> - Висока, <span style='color:green;'>■</span> - Низька.</li>
                        <li><b>Детальний опис:</b> Якщо текст у колонці "Опис проблеми" занадто довгий, зробіть по ній <b>подвійний клік</b>, щоб відкрити зручне вікно для читання повного тексту звернення.</li>
                        <li><b>Фільтрація та пошук:</b> Для швидкого пошуку потрібної заявки вводьте текст у поля під заголовками колонок. Можна фільтрувати за будь-якою колонкою, наприклад, за адресою, прізвищем заявника або статусом.</li>
                    </ul>
                """,
                "Додаткові дії (ПКМ)": """
                    <h3>Контекстне меню</h3>
                    <p>Натисніть <b>правою кнопкою миші</b> на будь-якій заявці в таблиці, щоб викликати меню швидких дій:</p>
                    <ul>
                        <li><b>🗺️ Показати на карті:</b> Відкриває інтерактивну карту міста, де кольоровим маркером буде позначено місце аварії. Це дозволяє візуально оцінити розташування проблеми.</li>
                        <li><b>🛠️ Списати матеріали:</b> Автоматично перемикає вас на вкладку "Виконання робіт" та вставляє ID обраної заявки у відповідне поле, що прискорює процес списання матеріалів.</li>
                    </ul>
                """
            },
            "Реєстрація звернень": """
                <h3>Створення нової заявки</h3>
                <p>Ця вкладка призначена для реєстрації нових звернень від громадян. Процес поділено на дві логічні частини: дані заявника та деталі самої аварії.</p>
                <ul>
                    <li><b>Автозаповнення за рахунком:</b> Введіть номер особового рахунку абонента в перше поле та натисніть <b>"🔍 Знайти"</b>. Якщо такий абонент вже є в базі даних, система автоматично заповнить усі його контактні дані та адресу.</li>
                    <li><b>Ручне введення адреси:</b> Якщо абонент новий або звертається з іншої адреси, змініть "Тип адреси" на "Інша адреса (Ввести вручну)". Поля адреси стануть активними. Почніть вводити назву вулиці, і система запропонує варіанти <b>автодоповнення</b> з офіційного реєстру вулиць Києва.</li>
                    <li><b>Деталі аварії:</b> Обов'язково вкажіть категорію та тип аварії (наприклад, "Сантехніка" -> "Прорив труби"), оберіть рівень її критичності та детально опишіть проблему зі слів мешканця.</li>
                    <li>Після заповнення всіх полів натисніть <b>"✅ Зберегти заявку"</b>.</li>
                </ul>
            """,
            "Виконання робіт": """
                <h3>Списання матеріалів</h3>
                <p>Після того, як ремонтна бригада виконала роботи, диспетчер або майстер повинен зафіксувати витрачені товарно-матеріальні цінності (ТМЦ) для коректного фінансового обліку.</p>
                <ul>
                    <li><b>ID заявки:</b> Вкажіть номер заявки, на яку списуються матеріали. Ви можете дізнатись його на першій вкладці або скористатись контекстним меню для автозаповнення.</li>
                    <li><b>Матеріал:</b> Оберіть потрібний матеріал із випадаючого списку. Поруч у дужках вказана його вартість та одиниця виміру.</li>
                    <li><b>Кількість:</b> Вкажіть витрачену кількість. Можна використовувати дробові числа (наприклад, <b>1.5</b> для півтора метра труби).</li>
                    <li>Натисніть <b>"➕ Додати до звіту"</b>. Запис про списання з'явиться в таблиці нижче, а загальна сума автоматично потрапить у фінансовий звіт для керівництва.</li>
                </ul>
            """,
            "Гарячі клавіші": """
                <h3>Гарячі клавіші</h3>
                <p>Для прискорення роботи ви можете використовувати наступні комбінації клавіш:</p>
                <ul>
                    <li><b>F1</b> — Відкрити довідку.</li>
                    <li><b>F5</b> — Примусово оновити дані в таблицях.</li>
                    <li><b>Ctrl+S</b> — Зберегти зміни, зроблені в таблиці заявок (зміна статусів, призначення бригад).</li>
                    <li><b>Ctrl+T</b> — Перемкнути тему оформлення (світла/темна).</li>
                    <li><b>Ctrl+Q</b> — Вийти з поточного робочого місця (АРМ).</li>
                </ul>
            """
        }

    def silent_refresh(self):
        """Періодично оновлює дані в таблицях, якщо диспетчер зараз не редагує комбобокси."""
        has_changes = False
        if hasattr(self, 'requests_table'):
            for row in range(self.requests_table.rowCount()):
                cb_s = self.requests_table.cellWidget(row, 7)
                cb_c = self.requests_table.cellWidget(row, 8)
                if cb_s and cb_c:
                    if cb_s.currentData() != cb_s.property("original_id") or cb_c.currentData() != cb_c.property("original_id"):
                        has_changes = True
                        break
        
        if not has_changes:
            self.refresh_requests_table()
            self.refresh_works_table()

    def setup_menu(self):
        """Ініціалізує сторінки диспетчерського пульта керування."""
        self.add_menu_item("Перегляд та обробка", self.build_requests_page())
        self.add_menu_item("Реєстрація звернень", self.build_registration_page())
        self.add_menu_item("Виконання робіт", self.build_works_page())
        self.finalize_menu()

    def on_menu_click(self, index, btn):
        super().on_menu_click(index, btn)
        if index == 0:
            self.refresh_requests_table()
        elif index == 2:
            self.refresh_works_table()

    def get_criticality_color(self, crit_name):
        """Повертає колір підсвічування рядка залежно від ступеня критичності аварії."""
        c = str(crit_name).lower()
        if "критич" in c: 
            return QColor("#552222") if self.is_dark_theme else QColor("#FFCCCC")
        elif "висок" in c: 
            return QColor("#553C1A") if self.is_dark_theme else QColor("#FFE5CC")
        elif "низьк" in c: 
            return QColor("#1A3C1A") if self.is_dark_theme else QColor("#E5FFE5")
        return QColor("#1F2D44") if self.is_dark_theme else QColor("#E5F2FF")

    def apply_theme(self):
        """Забезпечує коректну колірну палітру для всіх таблиць та вбудованих комбобоксів."""
        super().apply_theme()
        text_color = "#F8F8F2" if self.is_dark_theme else "#2C3E50"
        bg_color = "#313244" if self.is_dark_theme else "#FFFFFF"
        border_color = "#44475A" if self.is_dark_theme else "#DEE2E6"
        accent_color = "#8B5CF6"
        hover_bg = "#44475A" if self.is_dark_theme else "#E9ECEF"
        
        table_cb_style = f"""
            QComboBox {{ background-color: transparent; color: {text_color}; border: 1px solid transparent; padding: 2px 5px; }}
            QComboBox:hover {{ border: 1px solid {border_color}; border-radius: 4px; }}
            QComboBox QAbstractItemView {{ background-color: {bg_color}; color: {text_color}; selection-background-color: {accent_color}; border: 1px solid {border_color}; }}
            QComboBox QAbstractItemView::item {{ color: {text_color}; min-height: 28px; }}
            QComboBox QAbstractItemView::item:hover {{ background-color: {hover_bg}; }}
        """

        if hasattr(self, 'requests_table'):
            for row in range(self.requests_table.rowCount()):
                crit_item = self.requests_table.item(row, 6)
                if crit_item:
                    row_bg_color = self.get_criticality_color(crit_item.text())
                    for col in range(self.requests_table.columnCount()):
                        item = self.requests_table.item(row, col)
                        if item:
                            item.setBackground(row_bg_color)
                            
                    cb_s = self.requests_table.cellWidget(row, 7)
                    if cb_s: 
                        cb_s.setStyleSheet(table_cb_style)
                    
                    cb_c = self.requests_table.cellWidget(row, 8)
                    if cb_c: 
                        cb_c.setStyleSheet(table_cb_style)

                    

    def create_table_filters(self, table, filter_options=None):
        """Ініціалізує поля фільтрації та динамічно вирівнює їх за шириною колонок таблиці."""
        filter_options = filter_options or {}
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 2)
        filter_layout.setSpacing(0)

        self.filter_inputs = [] 
        self.corner_spacer = QWidget()
        filter_layout.addWidget(self.corner_spacer)
        
        for col in range(table.columnCount()):
            header_item = table.horizontalHeaderItem(col)
            header_text = header_item.text().replace('\n', ' ') if header_item else f"Колонка {col + 1}"

            if col in filter_options:
                cb = StyledComboBox()
                cb.setFixedHeight(26)
                cb.addItem("Всі")
                cb.addItems(filter_options[col])
                cb.setProperty("is_filter", "true")
                filter_layout.addWidget(cb) 
                self.filter_inputs.append((col, cb))
                cb.currentTextChanged.connect(lambda text, t=table, ins=self.filter_inputs: self.filter_table(t, ins))
            else:
                le = QLineEdit()
                le.setFixedHeight(26)
                le.setPlaceholderText(f"{header_text}")
                le.setProperty("is_filter", "true")
                filter_layout.addWidget(le)
                self.filter_inputs.append((col, le))
                le.textChanged.connect(lambda text, t=table, ins=self.filter_inputs: self.filter_table(t, ins))

        table.filter_inputs = self.filter_inputs

        def sync_widths():
            v_header_width = table.verticalHeader().width()
            self.corner_spacer.setFixedWidth(v_header_width)
            for c, widget in self.filter_inputs:
                widget.setFixedWidth(table.columnWidth(c))

        table.horizontalHeader().sectionResized.connect(sync_widths)
        QTimer.singleShot(100, sync_widths)
        return filter_widget

    def build_requests_page(self):
        """Створює сторінку журналювання та інтерактивної обробки заявок бригадами."""
        page = QWidget()
        main_layout = QVBoxLayout(page)
        main_layout.setContentsMargins(20, 20, 20, 20)

        top_bar = QHBoxLayout()
        title = QLabel("Диспетчеризація та моніторинг звернень")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        top_bar.addWidget(title)
        top_bar.addStretch()
        
        btn_refresh = self.create_action_button("🔄 Оновити список")
        btn_refresh.clicked.connect(self.refresh_requests_table)
        
        self.btn_toggle_view = self.create_action_button("👁️ Показати всі заявки")
        self.btn_toggle_view.clicked.connect(self.toggle_requests_view_mode)
        
        btn_save = self.create_action_button("💾 Зберегти зміни")
        btn_save.clicked.connect(self.save_table_changes)
        
        top_bar.addWidget(btn_refresh)
        top_bar.addWidget(self.btn_toggle_view)
        top_bar.addWidget(btn_save)
        main_layout.addLayout(top_bar)

        self.requests_table = QTableWidget()
        self.requests_table.setColumnCount(11)
        self.requests_table.setHorizontalHeaderLabels(
            ["ID", "Час фіксування", "Час виконання", "Заявник", "Адреса", "Тип аварії", "Критичність", "Статус", "Бригада", "Опис проблеми", "Канал"]
        )
        
        header = self.requests_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setMinimumSectionSize(80)
        
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Stretch)

        self.requests_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.requests_table.customContextMenuRequested.connect(self.show_table_context_menu)
        self.requests_table.cellDoubleClicked.connect(self.show_full_description)

        crit_list = [c["name"] for c in dictionary_service.get_criticalities()]
        status_list = [s["name"] for s in dictionary_service.get_statuses()]
        
        filters = self.create_table_filters(self.requests_table, filter_options={
            6: crit_list,
            7: status_list
        })
        main_layout.addWidget(filters)
        main_layout.addWidget(self.requests_table)

        btn_show_map = self.create_action_button("🗺️ Відкрити карту міста")
        btn_show_map.clicked.connect(self.open_map_window)
        main_layout.addWidget(btn_show_map)

        return page

    def show_full_description(self, row, col):
        """Відкриває модальну форму для повного детального читання опису поточної проблеми."""
        if col == 9: 
            item = self.requests_table.item(row, col)
            if not item: 
                return
            
            desc_text = item.text().strip()
            if not desc_text: 
                return

            dialog = QDialog(self)
            dialog.setWindowTitle("Деталі звернення")
            dialog.resize(500, 350)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)
            
            title = QLabel("Повний опис проблеми:")
            title.setStyleSheet("font-size: 16px; font-weight: bold;")
            
            text_edit = QTextEdit()
            text_edit.setPlainText(desc_text)
            text_edit.setReadOnly(True)
            
            if self.is_dark_theme:
                dialog.setStyleSheet("QDialog { background-color: #282A36; color: #F8F8F2; }")
                text_edit.setStyleSheet("background-color: #1E1E2E; color: #F8F8F2; border: 1px solid #44475A; border-radius: 6px; padding: 10px; font-size: 14px;")
                title.setStyleSheet("font-size: 16px; font-weight: bold; color: #8B5CF6;")
            else:
                dialog.setStyleSheet("QDialog { background-color: #F8F9FA; color: #2C3E50; }")
                text_edit.setStyleSheet("background-color: #FFFFFF; color: #2C3E50; border: 1px solid #DEE2E6; border-radius: 6px; padding: 10px; font-size: 14px;")
                title.setStyleSheet("font-size: 16px; font-weight: bold; color: #8B5CF6;")
                
            btn_close = self.create_action_button("Закрити")
            btn_close.clicked.connect(dialog.accept)
            
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            btn_layout.addWidget(btn_close)
            
            layout.addWidget(title)
            layout.addWidget(text_edit)
            layout.addLayout(btn_layout)
            
            dialog.exec()

    def toggle_requests_view_mode(self):
        """Перемикає відображення між усіма заявками та лише відкритими."""
        self.show_all_mode = not self.show_all_mode
        if self.show_all_mode:
            self.btn_toggle_view.setText("👁️ Приховати закриті")
        else:
            self.btn_toggle_view.setText("👁️ Показати всі заявки")
        self.refresh_requests_table()

    def refresh_requests_table(self):
        """Підвантажує свіжі заявки та заповнює таблицю з урахуванням критичності та призначень."""
        if not hasattr(self, 'requests_table'): 
            return
        self.requests_table.setRowCount(0)
        data = worker_service.get_active_requests(self.show_all_mode)
        
        self.all_statuses = dictionary_service.get_statuses()
        self.all_crews = dictionary_service.get_crews()

        for row_idx, row_data in enumerate(data):
            self.requests_table.insertRow(row_idx)
            bg_color = self.get_criticality_color(row_data["criticality"])
            
            request_time = row_data["request_date"].strftime("%d.%m.%Y %H:%M") if row_data.get("request_date") else ""
            comp_time = row_data["completion_date"].strftime("%d.%m.%Y %H:%M") if row_data.get("completion_date") else ""
            applicant = f"{row_data['applicant_last']} {row_data['applicant_first']}".strip() or "Невідомо"
            address = f"{row_data['street'] or ''}, кв. {row_data['apartment'] or ''}".strip(", ") if row_data['street'] else "Не вказано"
            crew_num = f"Бригада №{row_data['crew_number']}" if row_data['crew_number'] else "Не призначено"

            formatted_row = [
                str(row_data["id"]), request_time, comp_time, applicant, address,
                row_data["issue_type"], row_data["criticality"], row_data["status"],
                crew_num, row_data["description"], row_data["channel"]
            ]

            for col_idx in range(11):
                if col_idx != 7 and col_idx != 8:
                    item = QTableWidgetItem(formatted_row[col_idx])
                    item.setBackground(bg_color)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.requests_table.setItem(row_idx, col_idx, item)
            
            cb_status = StyledComboBox()
            for s in self.all_statuses: 
                cb_status.addItem(s["name"], userData=s["id"])
            cb_status.setCurrentText(row_data["status"])
            cb_status.setProperty("original_id", cb_status.currentData())
            cb_status.setProperty("request_id", row_data["id"])
            
            dummy_s = QTableWidgetItem("")
            dummy_s.setBackground(bg_color)
            self.requests_table.setItem(row_idx, 7, dummy_s)
            self.requests_table.setCellWidget(row_idx, 7, cb_status)

            cb_crew = StyledComboBox()
            cb_crew.addItem("Не призначено", userData=0)
            for cr in self.all_crews: 
                cb_crew.addItem(f"Б №{cr['crew_number']} ({cr['category_name']})", userData=cr["id"])
            
            saved_crew_id = row_data["crew_id"]
            if saved_crew_id:
                idx = cb_crew.findData(saved_crew_id)
                if idx != -1: 
                    cb_crew.setCurrentIndex(idx)
            else: 
                cb_crew.setCurrentIndex(0)

            cb_crew.setProperty("original_id", cb_crew.currentData())
            cb_crew.setProperty("request_id", row_data["id"])

            dummy_c = QTableWidgetItem("")
            dummy_c.setBackground(bg_color)
            self.requests_table.setItem(row_idx, 8, dummy_c)
            self.requests_table.setCellWidget(row_idx, 8, cb_crew)

        if hasattr(self, 'filter_inputs'):
            self.filter_table(self.requests_table, self.filter_inputs)
            
        self.apply_theme()
        self.refresh_map_markers()

    def handle_map_title_cache(self, title):
        """Зберігає географічні координати знайденої адреси у спільний кеш-файл json."""
        if title.startswith("CACHE|"):
            parts = title.split("|")
            if len(parts) == 4:
                addr = parts[1]
                lat = float(parts[2])
                lon = float(parts[3])
                from services.api_service import load_address_cache, save_address_cache
                cache = load_address_cache()
                if addr not in cache:
                    cache[addr] = [lat, lon]
                    save_address_cache(cache)

    def open_map_window(self):
        """Ініціалізує та відкриває автономне вікно карти для моніторингу викликів."""
        req_id = None
        full_addr = "Всі поточні аварії міста Києва"
        
        row = self.requests_table.currentRow()
        if row >= 0:
            id_item = self.requests_table.item(row, 0)
            if id_item:
                req_id = id_item.text()
                full_addr = self.requests_table.item(row, 4).text()

        if getattr(self, 'map_window', None) is None or not self.map_window.isVisible():
            self.map_window = QWidget()
            self.map_window.setWindowTitle(f"Карта інфраструктури: {full_addr}")
            self.map_window.setWindowIcon(QIcon("ui/icon.png"))
            self.map_window.resize(1000, 700)
            map_layout = QVBoxLayout(self.map_window)
            map_layout.setContentsMargins(0, 0, 0, 0)
            
            self.web_map = QWebEngineView()
            self.web_map.titleChanged.connect(self.handle_map_title_cache)
            map_layout.addWidget(self.web_map)
            
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
                <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
                <style> 
                    body { margin: 0; padding: 0; } #map { height: 100vh; width: 100%; } 
                    .popup-custom { font-family: 'Segoe UI', sans-serif; min-width: 220px; line-height: 1.5; }
                    .popup-custom h4 { margin: 0 0 8px 0; color: #8B5CF6; border-bottom: 1px solid #ddd; padding-bottom: 4px;}
                    .desc-box { background-color: #f8f9fa; padding: 6px; border-radius: 4px; border: 1px solid #e9ecef; margin-top: 5px; font-size: 13px; color: #555;}
                </style>
            </head>
            <body>
                <div id="map"></div>
                <script>
                    var kyivBounds = L.latLngBounds(L.latLng(50.33, 30.23), L.latLng(50.55, 30.83));
                    var map = L.map('map', { 
                        maxBounds: kyivBounds,
                        maxBoundsViscosity: 1.0,
                        minZoom: 11,
                        maxZoom: 18
                    }).setView([50.4501, 30.5234], 12);
                    
                    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png').addTo(map);
                    
                    var markers = {}; 
                    var focusTargetId = null;
                    
                    function clearMarkers() { for (var k in markers) { map.removeLayer(markers[k]); } markers = {}; }
                    
                    function setFocusTarget(id) {
                        focusTargetId = String(id);
                        if (markers[focusTargetId]) {
                            map.flyTo(markers[focusTargetId].getLatLng(), 16, { animate: true, duration: 1.5 });
                            markers[focusTargetId].openPopup();
                        }
                    }

                    var geocodeQueue = [];
                    var isGeocoding = false;

                    function processQueue() {
                        if (geocodeQueue.length === 0) { isGeocoding = false; return; }
                        isGeocoding = true;
                        var task = geocodeQueue.shift();

                        fetch('https://nominatim.openstreetmap.org/search?format=json&limit=1&q=' + encodeURIComponent(task.search_addr + ", Київ, Україна"))
                            .then(res => res.json())
                            .then(data => {
                                if(data.length > 0) {
                                    task.callback(data[0].lat, data[0].lon);
                                    document.title = "CACHE|" + task.search_addr.toLowerCase() + "|" + data[0].lat + "|" + data[0].lon;
                                } else { document.title = "MAP_READY"; }
                                setTimeout(processQueue, 1500); 
                            })
                            .catch(err => { setTimeout(processQueue, 3000); });
                    }
                    
                    function addMarker(id, display_addr, search_addr, status, criticality, issue_type, desc, applicant, time, crew, lat, lon) {
                        var color = "blue"; var crit = String(criticality).toLowerCase();
                        if (crit.includes("критич")) color = "red";
                        else if (crit.includes("висок")) color = "orange";
                        else if (crit.includes("низьк")) color = "green";
                        
                        var customIcon = L.icon({
                            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-' + color + '.png',
                            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                            iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34]
                        });

                        var popupContent = `<div class="popup-custom"><h4>Заявка #${id}</h4><b>📅 Час:</b> ${time}<br><b>📍 Адреса:</b> ${display_addr}<br><b>👤 Заявник:</b> ${applicant}<br><b>⚠️ Тип:</b> ${issue_type}<br><div class="desc-box"><b>📝 Опис:</b> ${desc}</div><hr style='margin:8px 0;border:0;border-top:1px solid #ddd;'><b>🛠 Статус:</b> ${status}<br><b>👷 Виконавець:</b> ${crew}</div>`;
                        
                        function drawPin(markerLat, markerLon) {
                            var m = L.marker([markerLat, markerLon], {icon: customIcon}).addTo(map).bindPopup(popupContent);
                            markers[String(id)] = m;
                            
                            if (String(id) === focusTargetId) {
                                map.flyTo([markerLat, markerLon], 16, { animate: true, duration: 1.5 });
                                m.openPopup();
                            }
                        }

                        if (lat !== null && lon !== null) {
                            drawPin(lat, lon);
                        } else {
                            geocodeQueue.push({ search_addr: search_addr, callback: drawPin });
                            if (!isGeocoding) processQueue();
                        }
                    }
                </script>
            </body>
            </html>
            """
            self.web_map.setHtml(html_content, QUrl("http://localhost"))
            self.map_window.pending_focus_id = req_id
            self.web_map.loadFinished.connect(self._on_external_map_loaded)
            self.map_window.show()
        else:
            self.map_window.setWindowTitle(f"Карта інфраструктури: {full_addr}")
            self.map_window.raise_()
            self.map_window.activateWindow()
            if req_id:
                self.web_map.page().runJavaScript(f"if(typeof setFocusTarget==='function') setFocusTarget('{req_id}');")

    def _on_external_map_loaded(self, ok):
        if ok:
            self.refresh_map_markers()
            if hasattr(self, 'map_window') and getattr(self.map_window, 'pending_focus_id', None):
                self.web_map.page().runJavaScript(f"if(typeof setFocusTarget==='function') setFocusTarget('{self.map_window.pending_focus_id}');")

    def refresh_map_markers(self):
        """Рендерить поточні активні аварії як кольорові маркери на географічній карті."""
        if not getattr(self, 'map_window', None) or not hasattr(self, 'web_map'): 
            return
        self.web_map.page().runJavaScript("if (typeof clearMarkers === 'function') clearMarkers();")
        
        data = worker_service.get_active_requests(self.show_all_mode)
        address_cache = load_address_cache()
        
        def escape_js(text):
            return str(text or "").replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", " ").replace("\r", "")

        for row in data:
            if row["status"] != "Виконано" and row["status"] != "Скасовано":
                display_addr = f"{row['street'] or ''}, кв. {row['apartment'] or ''}".strip(", ")
                search_addr = row["street"].strip()
                search_addr_lower = search_addr.lower()
                
                lat, lon = "null", "null"
                if search_addr_lower in address_cache:
                    lat = address_cache[search_addr_lower][0]
                    lon = address_cache[search_addr_lower][1]
                
                request_time = row["request_date"].strftime("%d.%m.%Y %H:%M") if row.get("request_date") else ""
                applicant = f"{row['applicant_last']} {row['applicant_first']}".strip() or "Невідомо"
                crew_num = f"Бригада №{row['crew_number']}" if row['crew_number'] else "Не призначено"

                js = f"if(typeof addMarker==='function') addMarker('{row['id']}','{escape_js(display_addr)}','{escape_js(search_addr)}','{escape_js(row['status'])}','{escape_js(row['criticality'])}','{escape_js(row['issue_type'])}','{escape_js(row['description'])}','{escape_js(applicant)}','{escape_js(request_time)}','{escape_js(crew_num)}', {lat}, {lon});"
                self.web_map.page().runJavaScript(js)

    def show_table_context_menu(self, pos: QPoint):
        """Контекстне меню правого кліку для швидкої маршрутизації до інших вкладок."""
        row = self.requests_table.currentRow()
        if row < 0: 
            return
        
        id_item = self.requests_table.item(row, 0)
        if not id_item: 
            return
        req_id = id_item.text()

        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #282A36; color: #F8F8F2; border: 1px solid #44475A; } QMenu::item:selected { background-color: #8B5CF6; }")
        
        act_map = menu.addAction("🗺️ Показати на карті")
        act_works = menu.addAction("🛠️ Списати матеріали")
        
        action = menu.exec(self.requests_table.viewport().mapToGlobal(pos))
        
        if action == act_map:
            self.open_map_window()
        elif action == act_works:
            self.stacked_widget.setCurrentIndex(2)
            if hasattr(self, 'active_button'):
                self.active_button = self.menu_buttons[2]
                self.apply_theme()
            if hasattr(self, 'input_req_id'):
                self.input_req_id.setText(str(req_id))

    def save_table_changes(self):
        """Збирає змінені вручну статуси та призначення бригад і пакетно оновлює їх у БД."""
        updates = []
        for row in range(self.requests_table.rowCount()):
            cb_s = self.requests_table.cellWidget(row, 7)
            cb_c = self.requests_table.cellWidget(row, 8)
            if cb_s and cb_c:
                req_id = cb_s.property("request_id")
                if cb_s.currentData() != cb_s.property("original_id") or cb_c.currentData() != cb_c.property("original_id"):
                    updates.append({'req_id': req_id, 'status_id': cb_s.currentData(), 'crew_id': cb_c.currentData()})
                    cb_s.setProperty("original_id", cb_s.currentData())
                    cb_c.setProperty("original_id", cb_c.currentData())

        if not updates:
            QMessageBox.information(self, "Інформація", "Немає змін для збереження.")
            return

        worker_id = getattr(self, "user_id", None)
        success, msg = worker_service.update_requests_data(updates, worker_id)
        
        if success:
            QMessageBox.information(self, "Успіх", msg)
            self.refresh_requests_table()
        else:
            QMessageBox.critical(self, "Помилка", msg)

    def build_registration_page(self):
        """Конструює сторінку реєстрації нових звернень з інтелектуальним автозаповненням адрес."""
        page = QWidget()
        main_layout = QVBoxLayout(page)
        main_layout.setContentsMargins(20, 20, 20, 20)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)

        title = QLabel("Реєстрація нового звернення")
        scroll_layout.addWidget(title)

        group_app = QGroupBox("Дані заявника")
        form_app = QFormLayout(group_app)

        self.input_lname = self.create_line_edit("Введіть прізвище")
        self.input_fname = self.create_line_edit("Введіть ім'я")
        self.input_mname = self.create_line_edit("Введіть по батькові")
        self.input_phone = self.create_line_edit("+380...")
        self.input_email = self.create_line_edit("приклад@пошта.com")

        account_layout = QHBoxLayout()
        self.input_account = self.create_line_edit("Введіть номер особового рахунку...")
        btn_search_acc = self.create_action_button("🔍 Знайти")
        btn_search_acc.clicked.connect(self.search_applicant)
        self.input_account.returnPressed.connect(self.search_applicant)
        account_layout.addWidget(self.input_account)
        account_layout.addWidget(btn_search_acc)

        self.input_address = self.create_line_edit("Введіть вулицю та номер будинку...")

        self.completer_model = QStringListModel()
        self.address_completer = QCompleter(self.completer_model, self)
        self.address_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.address_completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self.input_address.setCompleter(self.address_completer)
        self.input_address.textEdited.connect(self.on_address_text_edited)

        self.input_apartment = self.create_line_edit("№ квартири...")
        self.input_entrance = self.create_line_edit("№ під'їзду...")
        self.input_floor = self.create_line_edit("Поверх...")

        form_app.addRow("Особовий рахунок:", account_layout)
        form_app.addRow("Вулиця, будинок:", self.input_address)

        apt_floor_layout = QHBoxLayout()
        apt_floor_layout.addWidget(self.input_apartment)
        apt_floor_layout.addWidget(QLabel("Під'їзд:"))
        apt_floor_layout.addWidget(self.input_entrance)
        apt_floor_layout.addWidget(QLabel("Поверх:"))
        apt_floor_layout.addWidget(self.input_floor)
        form_app.addRow("Квартира:", apt_floor_layout)

        form_app.addRow("", QLabel(""))  
        form_app.addRow("Прізвище:", self.input_lname)
        form_app.addRow("Ім'я:", self.input_fname)
        form_app.addRow("По батькові:", self.input_mname)
        form_app.addRow("Телефон:", self.input_phone)
        form_app.addRow("Електронна пошта:", self.input_email)

        group_req = QGroupBox("Деталі заявки")
        form_req = QFormLayout(group_req)

        self.combo_channel = StyledComboBox()
        self.combo_channel.addItems(["Телефон", "Веб-портал", "Особистий візит"])

        self.combo_cat = StyledComboBox()
        self.combo_type = StyledComboBox()
        self.combo_cat.currentTextChanged.connect(self.update_issue_types)

        self.combo_criticality = StyledComboBox()
        crits = dictionary_service.get_criticalities()
        for c in crits: 
            self.combo_criticality.addItem(c["name"], userData=c["id"])

        self.input_desc = QTextEdit()
        self.input_desc.setFixedHeight(80)

        form_req.addRow("Канал звернення:", self.combo_channel)
        form_req.addRow("Категорія:", self.combo_cat)
        form_req.addRow("Тип аварії:", self.combo_type)
        form_req.addRow("Рівень критичності:", self.combo_criticality)
        form_req.addRow("Опис проблеми:", self.input_desc)

        scroll_layout.addWidget(group_app)
        scroll_layout.addWidget(group_req)

        btn_layout = QHBoxLayout()
        
        btn_clear = self.create_action_button("🧹 Очистити")
        btn_clear.clicked.connect(self.clear_registration_fields)
        
        btn_save_req = self.create_action_button("✅ Зберегти заявку")
        btn_save_req.clicked.connect(self.submit_request)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_clear)
        btn_layout.addWidget(btn_save_req)
        
        scroll_layout.addLayout(btn_layout)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        return page
    
    def search_applicant(self):
        """Знаходить та підтягує дані абонента за номером його особового рахунку."""
        account = self.input_account.text().strip()
        if not account: 
            return
        result = worker_service.get_applicant_by_account(account)
        if result["found"]:
            self.current_applicant_id = result["applicant_id"]
            self.input_lname.setText(result["lname"])
            self.input_fname.setText(result["fname"])
            self.input_mname.setText(result["mname"])
            self.input_phone.setText(result["phone"])
            self.input_email.setText(result["email"])
            self.input_address.setText(result["street"])
            self.input_apartment.setText(result["apartment"])
            self.input_floor.setText(result["floor"])
            self.input_entrance.setText(result.get("entrance", ""))
        else:
            self.current_applicant_id = None
            QMessageBox.information(self, "Результат", "Абонента не знайдено.")

    def on_address_text_edited(self, text):
        """Запускає затримку таймера автодоповнення для оптимізації кількості API-запитів."""
        if len(text) >= 3:
            self.address_timer.start(600)
    
    def clear_registration_fields(self):
        """Очищає всі поля форми реєстрації нового звернення."""
        self.input_account.clear()
        self.input_address.clear()
        self.input_apartment.clear()
        self.input_entrance.clear()
        self.input_floor.clear()
        self.input_lname.clear()
        self.input_fname.clear()
        self.input_mname.clear()
        self.input_phone.clear()
        self.input_email.clear()
        self.input_desc.clear()
        
        self.combo_channel.setCurrentIndex(0)
        if self.combo_cat.count() > 0:
            self.combo_cat.setCurrentIndex(0)
        if self.combo_criticality.count() > 0:
            self.combo_criticality.setCurrentIndex(0)
            
        self.current_applicant_id = None

    def trigger_address_search(self):
        """Ініціює фоновий потік пошуку адрес через OpenStreetMap API."""
        self.address_thread.search(self.input_address.text().strip())

    def update_address_completer(self, results):
        """Оновлює випадаючий список результатів інтелектуального пошуку адрес."""
        self.completer_model.setStringList(results)
        if results:
            self.address_completer.complete()

    def update_issue_types(self, cat):
        """Фільтрує підлеглий список типів аварій відповідно до обраної категорії."""
        self.combo_type.clear()
        for type_id, type_name in self.issue_mapping.get(cat, []):
            self.combo_type.addItem(type_name, userData=type_id)

    def submit_request(self):
        """Збирає валідовані дані форми та фіксує нове звернення у базі даних."""
        app_data = {
            "account": self.input_account.text().strip(), "lname": self.input_lname.text().strip(),
            "fname": self.input_fname.text().strip(), "mname": self.input_mname.text().strip(),
            "phone": self.input_phone.text().strip(), "email": self.input_email.text().strip(),
            "street": self.input_address.text().strip(), "apartment": self.input_apartment.text().strip(),
            "floor": self.input_floor.text().strip(), 
            "entrance": self.input_entrance.text().strip(),
            "applicant_id": self.current_applicant_id
        }
        if not app_data["lname"] or not app_data["street"] or self.combo_type.currentData() is None or self.combo_criticality.currentData() is None:
            QMessageBox.warning(self, "Помилка", "Заповніть обов'язкові поля!")
            return

        req_data = {
            "channel": self.combo_channel.currentText(), "issue_type_id": self.combo_type.currentData(),
            "criticality_id": self.combo_criticality.currentData(), "description": self.input_desc.toPlainText().strip(),
            "user_id": getattr(self, "user_id", None)
        }
        success, msg = worker_service.register_new_request(app_data, req_data)
        if success:
            QMessageBox.information(self, "Успіх", msg)
            self.refresh_requests_table()
            self.input_desc.clear()
        else: 
            QMessageBox.critical(self, "Помилка", msg)

    def build_works_page(self):
        """Створює сторінку для списання товарно-матеріальних цінностей на ремонти."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Деталізація виконаних робіт")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")

        group = QGroupBox("Списання матеріалів")
        form = QFormLayout(group)

        self.input_req_id = self.create_line_edit("Введіть ID заявки...")
        self.combo_mat = StyledComboBox()
        for m in dictionary_service.get_materials():
            self.combo_mat.addItem(f"{m['name']} ({m['price']} грн/{m['unit']})", userData=m['id'])

        self.input_quantity = self.create_line_edit("Введіть кількість...")
        btn_add_mat = self.create_action_button("➕ Додати до звіту")
        btn_add_mat.clicked.connect(self.submit_material)
        self.input_req_id.returnPressed.connect(self.submit_material)
        self.input_quantity.returnPressed.connect(self.submit_material)

        form.addRow("ID заявки:", self.input_req_id)
        form.addRow("Матеріал:", self.combo_mat)
        form.addRow("Кількість:", self.input_quantity)
        form.addRow("", btn_add_mat)
        layout.addWidget(group)

        self.works_table = QTableWidget()
        self.works_table.setColumnCount(5)
        self.works_table.setHorizontalHeaderLabels(["ID Списання", "Заявка", "Матеріал", "Кількість", "Сума"])
        self.works_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.create_table_filters(self.works_table))
        layout.addWidget(self.works_table)
        return page

    def submit_material(self):
        """Проводить списання вказаної кількості матеріалу на обрану аварійну заявку."""
        req_id = self.input_req_id.text().strip()
        qty = self.input_quantity.text().strip()
        if not req_id or not qty or not req_id.isdigit(): 
            return
        success, msg = worker_service.write_off_material(int(req_id), self.combo_mat.currentData(), qty)
        if success:
            self.input_quantity.clear()
            self.refresh_works_table()
        else: 
            QMessageBox.critical(self, "Помилка", msg)

    def refresh_works_table(self):
        """Оновлює зведену таблицю списань ТМЦ з бази даних."""
        if not hasattr(self, 'works_table'): 
            return
        self.works_table.setRowCount(0)
        data = worker_service.get_used_materials_report()
        for row in data: 
            formatted_row = [
                str(row["id"]), 
                f"Заявка #{row['request_id']}", 
                row["material_name"], 
                f"{row['quantity']} {row['unit']}", 
                f"{row['total_cost']:.2f} грн"
            ]
            self.add_table_row(self.works_table, formatted_row)