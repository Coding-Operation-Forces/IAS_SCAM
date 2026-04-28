from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QHeaderView, QTextEdit, QCompleter,
                             QFormLayout, QGroupBox, QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView
from base_arm import BaseArmWindow, StyledComboBox


class ArmWorkerWindow(BaseArmWindow):
    def __init__(self):
        super().__init__("АРМ Працівника комунального підприємства")
        self.issue_mapping = {
            "Водопостачання": ["Прорив труби", "Відсутність води", "Низький тиск води", "Прорив каналізації"],
            "Електропостачання": ["Відсутність світла", "Обрив проводу", "Іскріння/Коротке замикання",
                                  "Перепади напруги"],
            "Опалення": ["Холодні батареї", "Прорив теплотраси", "Витік теплоносія"],
            "Благоустрій": ["Повалене дерево", "Відкритий люк", "Неприбране сміття", "Ями на дорогах"]
        }
        self.setup_menu()

    def setup_menu(self):
        self.add_menu_item("Прийом заявок", self.build_requests_page())
        self.add_menu_item("Реєстрація звернень", self.build_registration_page())
        self.add_menu_item("Виконання робіт", self.build_works_page())
        self.add_menu_item("Карта інфраструктури", self.build_map_page())
        self.finalize_menu()

    # ==========================================
    # 1. ПРИЙОМ ЗАЯВОК
    # ==========================================
    def build_requests_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Список поточних звернень")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")

        self.requests_table = QTableWidget()
        self.requests_table.setColumnCount(9)
        self.requests_table.setHorizontalHeaderLabels(
            ["ID", "Час фіксування", "Заявник", "Адреса", "Тип аварії", "Критичність", "Статус", "Бригада", "Канал"]
        )
        self.requests_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.requests_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.requests_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.requests_table.setRowCount(0)

        filters = self.create_table_filters(self.requests_table)
        layout.addWidget(filters)
        layout.addWidget(self.requests_table)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.create_action_button("Оновити список"))
        btn_layout.addWidget(self.create_action_button("Редагувати статус"))
        btn_layout.addStretch()

        layout.addLayout(btn_layout)
        return page

    # ==========================================
    # 2. РЕЄСТРАЦІЯ ЗВЕРНЕНЬ
    # ==========================================
    def build_registration_page(self):
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

        self.input_account = self.create_line_edit("Введіть номер особового рахунку...")

        self.combo_address_type = StyledComboBox()
        self.combo_address_type.addItems(["За особовим рахунком (Автоматично)", "Інша адреса (Ввести вручну)"])
        self.combo_address_type.currentTextChanged.connect(self.on_address_type_changed)

        # ОНОВЛЕНО: Розділені поля адреси
        self.input_address = self.create_line_edit("Вулиця та будинок (Підтягнеться з БД)...")
        self.input_address.setEnabled(False)

        self.input_apartment = self.create_line_edit("Підтягнеться...")
        self.input_apartment.setEnabled(False)

        self.input_floor = self.create_line_edit("Підтягнеться...")
        self.input_floor.setEnabled(False)

        form_app.addRow("Особовий рахунок:", self.input_account)
        form_app.addRow("Тип адреси:", self.combo_address_type)
        form_app.addRow("Вулиця, будинок:", self.input_address)

        # Групуємо Квартиру і Поверх в один рядок для компактності
        apt_floor_layout = QHBoxLayout()
        apt_floor_layout.addWidget(self.input_apartment)
        lbl_floor = QLabel("Поверх:")
        apt_floor_layout.addWidget(lbl_floor)
        apt_floor_layout.addWidget(self.input_floor)

        form_app.addRow("Квартира:", apt_floor_layout)

        form_app.addRow("", QLabel(""))  # Пробіл для візуального розділення
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
        self.combo_cat.addItems(list(self.issue_mapping.keys()))

        self.combo_type = StyledComboBox()
        self.combo_cat.currentTextChanged.connect(self.update_issue_types)
        self.update_issue_types(self.combo_cat.currentText())

        self.combo_criticality = StyledComboBox()
        self.combo_criticality.addItems(["Низький", "Середній", "Високий", "Критичний"])

        self.input_desc = QTextEdit()
        self.input_desc.setFixedHeight(80)

        form_req.addRow("Канал звернення:", self.combo_channel)
        form_req.addRow("Категорія:", self.combo_cat)
        form_req.addRow("Тип аварії:", self.combo_type)
        form_req.addRow("Рівень критичності:", self.combo_criticality)
        form_req.addRow("Опис проблеми:", self.input_desc)

        scroll_layout.addWidget(group_app)
        scroll_layout.addWidget(group_req)

        scroll_layout.addWidget(self.create_action_button("Зберегти заявку", primary=True),
                                alignment=Qt.AlignmentFlag.AlignRight)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        return page

    def on_address_type_changed(self, text):
        """Логіка перемикання полів адреси, квартири та поверху"""
        if "Автоматично" in text:
            self.input_address.setPlaceholderText("Вулиця та будинок (Підтягнеться з БД)...")
            self.input_address.setEnabled(False)
            self.input_address.clear()

            self.input_apartment.setPlaceholderText("Підтягнеться...")
            self.input_apartment.setEnabled(False)
            self.input_apartment.clear()

            self.input_floor.setPlaceholderText("Підтягнеться...")
            self.input_floor.setEnabled(False)
            self.input_floor.clear()
        else:
            self.input_address.setPlaceholderText("Введіть вулицю та номер будинку вручну...")
            self.input_address.setEnabled(True)

            self.input_apartment.setPlaceholderText("№ квартири...")
            self.input_apartment.setEnabled(True)

            self.input_floor.setPlaceholderText("Поверх...")
            self.input_floor.setEnabled(True)

    def update_issue_types(self, cat):
        self.combo_type.clear()
        self.combo_type.addItems(self.issue_mapping.get(cat, []))

    # ==========================================
    # 3. ВИКОНАННЯ РОБІТ
    # ==========================================
    def build_works_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Деталізація виконаних робіт")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")

        group = QGroupBox("Списання матеріалів")
        form = QFormLayout(group)

        self.combo_req = StyledComboBox()
        self.combo_req.setEditable(True)
        self.combo_req.setPlaceholderText("Введіть номер заявки...")

        completer = QCompleter(self.combo_req.model())
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.combo_req.setCompleter(completer)

        self.combo_mat = StyledComboBox()
        self.combo_mat.setPlaceholderText("Оберіть матеріал...")

        self.input_quantity = self.create_line_edit("Введіть кількість...")

        form.addRow("Пошук заявки:", self.combo_req)
        form.addRow("Матеріал:", self.combo_mat)
        form.addRow("Кількість:", self.input_quantity)
        form.addRow("", self.create_action_button("Додати до звіту", primary=True))

        layout.addWidget(group)

        self.works_table = QTableWidget()
        self.works_table.setColumnCount(5)
        self.works_table.setHorizontalHeaderLabels(
            ["ID", "Заявка", "Матеріал", "Кількість", "Сума"])
        self.works_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.works_table.setRowCount(0)

        filters = self.create_table_filters(self.works_table)
        layout.addWidget(filters)
        layout.addWidget(self.works_table)

        return page

    # ==========================================
    # 4. КАРТА ІНФРАСТРУКТУРИ
    # ==========================================
    def build_map_page(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        left_panel = QWidget()
        left_panel.setFixedWidth(350)
        left_lay = QVBoxLayout(left_panel)
        left_lay.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Поточні завдання на карті")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.worker_map_table = QTableWidget()
        self.worker_map_table.setColumnCount(4)
        self.worker_map_table.setHorizontalHeaderLabels(["ID", "Критичність", "Статус", "Адреса"])
        header = self.worker_map_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.worker_map_table.setRowCount(0)

        filters = self.create_table_filters(self.worker_map_table)
        left_lay.addWidget(filters)
        left_lay.addWidget(self.worker_map_table)

        left_lay.addWidget(self.create_action_button("Оновити карту", primary=True))

        self.web_map = QWebEngineView()

        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style> 
                body { margin: 0; padding: 0; }
                #map { height: 100vh; width: 100%; }
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var bounds = L.latLngBounds(L.latLng(50.21, 30.20), L.latLng(50.59, 30.85));
                var map = L.map('map', {
                    maxBounds: bounds,
                    maxBoundsViscosity: 1.0, 
                    minZoom: 11 
                }).setView([50.4501, 30.5234], 12);

                L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { attribution: '&copy; CARTO' }).addTo(map);
            </script>
        </body>
        </html>
        """
        self.web_map.setHtml(html_content)
        layout.addWidget(left_panel)
        layout.addWidget(self.web_map, stretch=1)
        return page