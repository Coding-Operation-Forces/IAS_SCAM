from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QHeaderView, QTextEdit, QCompleter,
                             QFormLayout, QGroupBox, QScrollArea, QMessageBox, QTableWidgetItem)
from PyQt6.QtCore import Qt, QTimer, QStringListModel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from ui.base_arm import BaseArmWindow, StyledComboBox

# Імпортуємо наші сервіси
from services import worker_service
from services import dictionary_service
from services.api_service import AddressSearchThread

class ArmWorkerWindow(BaseArmWindow):
    def on_menu_click(self, index, btn):
        """Перевизначаємо базовий клік меню, щоб вкладки оновлювалися на льоту"""
        super().on_menu_click(index, btn)
        if index == 0:
            self.refresh_requests_table()
        elif index == 2:
            self.refresh_works_table()
        elif index == 3:
            # Щоразу при переході на вкладку карти — примусово її оновлюємо
            self.refresh_map_table()
    
    def on_address_text_edited(self, text):
        """Запускає таймер при вводі адреси (якщо це ручний ввід)"""
        if len(text) >= 3 and self.combo_address_type.currentText() != "За особовим рахунком (Автоматично)":
            self.address_timer.start(600)  # Затримка 600мс після останнього натискання

    def trigger_address_search(self):
        query = self.input_address.text().strip()
        self.address_thread.search(query)

    def update_address_completer(self, results):
        if results:
            self.completer_model.setStringList(results)
            self.address_completer.complete()

    def __init__(self):
        super().__init__("АРМ Працівника комунального підприємства")
        self.issue_mapping = worker_service.get_issue_mapping()
        self.current_applicant_id = None
        
        # --- ІНІЦІАЛІЗАЦІЯ API АДРЕС ---
        self.address_thread = AddressSearchThread()
        self.address_thread.results_ready.connect(self.update_address_completer)
        
        # Таймер для Debounce (щоб не відправляти запит на кожну літеру)
        self.address_timer = QTimer()
        self.address_timer.setSingleShot(True)
        self.address_timer.timeout.connect(self.trigger_address_search)

        self.setup_menu()

    def setup_menu(self):
        self.add_menu_item("Прийом заявок", self.build_requests_page())
        self.add_menu_item("Реєстрація звернень", self.build_registration_page())
        self.add_menu_item("Виконання робіт", self.build_works_page())
        self.add_menu_item("Карта інфраструктури", self.build_map_page())
        self.finalize_menu()
        
        # Початкове завантаження даних у таблиці
        self.refresh_requests_table()
        self.refresh_works_table()

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
        self.requests_table.setColumnCount(10)
        self.requests_table.setHorizontalHeaderLabels(
            ["ID", "Час фіксування", "Заявник", "Адреса", "Тип аварії", "Критичність", "Статус", "Бригада", "Опис проблеми", "Канал"]
        )
        self.requests_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.requests_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.requests_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.requests_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)

        filters = self.create_table_filters(self.requests_table)
        layout.addWidget(filters)
        layout.addWidget(self.requests_table)

        btn_layout = QHBoxLayout()
        btn_refresh = self.create_action_button("Оновити список")
        btn_refresh.clicked.connect(self.refresh_requests_table)
        
        btn_save_changes = self.create_action_button("💾 Зберегти зміни (Статуси та Бригади)", primary=True)
        btn_save_changes.clicked.connect(self.save_table_changes)
        
        btn_layout.addWidget(btn_refresh)
        btn_layout.addWidget(btn_save_changes)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)
        return page

    def refresh_requests_table(self):
        """Оновлює таблицю звернень з БД, створюючи інтерактивні випадаючі списки."""
        self.requests_table.setRowCount(0)
        data = worker_service.get_active_requests()
        
        self.all_statuses = dictionary_service.get_statuses()
        self.all_crews = dictionary_service.get_crews()

        for row_idx, row_data in enumerate(data):
            self.requests_table.insertRow(row_idx)
            
            for col_idx in range(10):
                if col_idx != 6 and col_idx != 7:
                    self.requests_table.setItem(row_idx, col_idx, QTableWidgetItem(str(row_data[col_idx])))
            
            # Колонка 6: СТАТУС
            cb_status = StyledComboBox()
            for s in self.all_statuses:
                cb_status.addItem(s["name"], userData=s["id"])
            cb_status.setCurrentText(str(row_data[6]))
            cb_status.setProperty("original_id", cb_status.currentData())
            cb_status.setProperty("request_id", row_data[0])
            
            dummy_status = QTableWidgetItem(str(row_data[6]))
            self.requests_table.setItem(row_idx, 6, dummy_status)
            cb_status.currentTextChanged.connect(lambda text, r=row_idx, c=6: self.requests_table.item(r, c).setText(text))
            self.requests_table.setCellWidget(row_idx, 6, cb_status)

            # Колонка 7: БРИГАДА
            cb_crew = StyledComboBox()
            cb_crew.addItem("Не призначено", userData=0)
            for cr in self.all_crews:
                cb_crew.addItem(f"Бригада №{cr['crew_number']} ({cr['category_name']})", userData=cr["id"])
            
            saved_crew_id = row_data[10]
            if saved_crew_id:
                idx = cb_crew.findData(saved_crew_id)
                if idx != -1: cb_crew.setCurrentIndex(idx)
            else:
                cb_crew.setCurrentIndex(0)

            cb_crew.setProperty("original_id", cb_crew.currentData())
            cb_crew.setProperty("request_id", row_data[0])
            
            dummy_crew = QTableWidgetItem(cb_crew.currentText())
            self.requests_table.setItem(row_idx, 7, dummy_crew)
            cb_crew.currentTextChanged.connect(lambda text, r=row_idx, c=7: self.requests_table.item(r, c).setText(text))
            self.requests_table.setCellWidget(row_idx, 7, cb_crew)

    def save_table_changes(self):
        """Зберігає змінені статуси чи бригади в БД."""
        updates = []
        for row in range(self.requests_table.rowCount()):
            cb_status = self.requests_table.cellWidget(row, 6)
            cb_crew = self.requests_table.cellWidget(row, 7)
            
            if cb_status and cb_crew:
                req_id = cb_status.property("request_id")
                curr_status_id = cb_status.currentData()
                orig_status_id = cb_status.property("original_id")
                curr_crew_id = cb_crew.currentData()
                orig_crew_id = cb_crew.property("original_id")
                
                if curr_status_id != orig_status_id or curr_crew_id != orig_crew_id:
                    updates.append({
                        'req_id': req_id,
                        'status_id': curr_status_id,
                        'crew_id': curr_crew_id
                    })
                    cb_status.setProperty("original_id", curr_status_id)
                    cb_crew.setProperty("original_id", curr_crew_id)

        if not updates:
            QMessageBox.information(self, "Інформація", "Не виявлено жодних змін для збереження.")
            return

        success, msg = worker_service.update_requests_data(updates)
        if success:
            QMessageBox.information(self, "Успіх", msg)
            if hasattr(self, 'refresh_map_table'):
                self.refresh_map_table()
        else:
            QMessageBox.critical(self, "Помилка", msg)

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

        # Пошук за рахунком
        account_layout = QHBoxLayout()
        self.input_account = self.create_line_edit("Введіть номер особового рахунку...")
        btn_search_acc = self.create_action_button("🔍 Знайти")
        btn_search_acc.clicked.connect(self.search_applicant)
        account_layout.addWidget(self.input_account)
        account_layout.addWidget(btn_search_acc)

        self.combo_address_type = StyledComboBox()
        self.combo_address_type.addItems(["За особовим рахунком (Автоматично)", "Інша адреса (Ввести вручну)"])
        self.combo_address_type.currentTextChanged.connect(self.on_address_type_changed)

        self.input_address = self.create_line_edit("Вулиця та будинок (Підтягнеться з БД)...")
        self.input_address.setEnabled(False)
        self.completer_model = QStringListModel()
        self.address_completer = QCompleter(self.completer_model, self)
        self.address_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.input_address.setCompleter(self.address_completer)
        
        # Підключаємо сигнал вводу тексту
        self.input_address.textEdited.connect(self.on_address_text_edited)

        self.input_apartment = self.create_line_edit("Підтягнеться...")
        self.input_apartment.setEnabled(False)

        self.input_floor = self.create_line_edit("Підтягнеться...")
        self.input_floor.setEnabled(False)

        form_app.addRow("Особовий рахунок:", account_layout)
        form_app.addRow("Тип адреси:", self.combo_address_type)
        form_app.addRow("Вулиця, будинок:", self.input_address)

        apt_floor_layout = QHBoxLayout()
        apt_floor_layout.addWidget(self.input_apartment)
        lbl_floor = QLabel("Поверх:")
        apt_floor_layout.addWidget(lbl_floor)
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
        self.combo_cat.addItems(list(self.issue_mapping.keys()))

        self.combo_type = StyledComboBox()
        self.combo_cat.currentTextChanged.connect(self.update_issue_types)
        if self.issue_mapping:
            self.update_issue_types(self.combo_cat.currentText())

        self.combo_criticality = StyledComboBox()
        # Завантажуємо реальні рівні критичності з БД
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

        btn_save_request = self.create_action_button("Зберегти заявку", primary=True)
        btn_save_request.clicked.connect(self.submit_request)
        scroll_layout.addWidget(btn_save_request, alignment=Qt.AlignmentFlag.AlignRight)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        return page

    def search_applicant(self):
        """Шукає абонента в БД та заповнює поля."""
        account = self.input_account.text().strip()
        if not account:
            QMessageBox.warning(self, "Помилка", "Введіть номер рахунку!")
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
            
            QMessageBox.information(self, "Успіх", "Дані абонента знайдено та завантажено.")
        else:
            self.current_applicant_id = None
            QMessageBox.information(self, "Результат", "Абонента не знайдено. Введіть дані вручну.")

    def on_address_type_changed(self, text):
        if "Автоматично" in text:
            self.input_address.setPlaceholderText("Вулиця та будинок (Підтягнеться з БД)...")
            self.input_address.setEnabled(False)
            self.input_apartment.setPlaceholderText("Підтягнеться...")
            self.input_apartment.setEnabled(False)
            self.input_floor.setPlaceholderText("Підтягнеться...")
            self.input_floor.setEnabled(False)
        else:
            self.current_address_id = None # Скидаємо прив'язку
            self.input_address.setPlaceholderText("Введіть вулицю та номер будинку вручну...")
            self.input_address.setEnabled(True)
            self.input_apartment.setPlaceholderText("№ квартири...")
            self.input_apartment.setEnabled(True)
            self.input_floor.setPlaceholderText("Поверх...")
            self.input_floor.setEnabled(True)

    def update_issue_types(self, cat):
        self.combo_type.clear()
        types = self.issue_mapping.get(cat, [])
        for type_id, type_name in types:
            self.combo_type.addItem(type_name, userData=type_id)

    def submit_request(self):
        """Збирає дані з форми та відправляє у сервіс."""
        app_data = {
            "account": self.input_account.text().strip(),
            "lname": self.input_lname.text().strip(),
            "fname": self.input_fname.text().strip(),
            "mname": self.input_mname.text().strip(),
            "phone": self.input_phone.text().strip(),
            "email": self.input_email.text().strip(),
            "street": self.input_address.text().strip(),
            "apartment": self.input_apartment.text().strip(),
            "floor": self.input_floor.text().strip(),
            "applicant_id": self.current_applicant_id,
            "address_id": self.current_address_id
        }

        # Валідація мінімальних даних
        if not app_data["lname"] or not app_data["street"]:
            QMessageBox.warning(self, "Помилка", "Заповніть обов'язкові поля: Прізвище та Вулиця!")
            return

        # Запобігаємо помилці, якщо немає типів у БД
        if self.combo_type.currentData() is None:
            QMessageBox.warning(self, "Помилка", "Не обрано тип аварії. Перевірте довідники БД!")
            return

        req_data = {
            "channel": self.combo_channel.currentText(),
            "issue_type_id": self.combo_type.currentData(),
            "criticality_id": self.combo_criticality.currentData(),
            "description": self.input_desc.toPlainText().strip()
        }

        success, msg = worker_service.register_new_request(app_data, req_data)
        if success:
            QMessageBox.information(self, "Успіх", msg)
            self.refresh_requests_table()
            # Очищення полів після збереження
            for field in [self.input_account, self.input_lname, self.input_fname, self.input_mname, 
                          self.input_phone, self.input_email, self.input_address, self.input_apartment, 
                          self.input_floor]:
                field.clear()
            self.input_desc.clear()
            self.current_applicant_id = None
            self.current_address_id = None
        else:
            QMessageBox.critical(self, "Помилка", msg)

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

        # Оскільки ID заявок краще не завантажувати всі одразу, 
        # дозволяємо просто вписати ID
        self.input_req_id = self.create_line_edit("Введіть ID заявки...")

        self.combo_mat = StyledComboBox()
        # Завантажуємо матеріали з БД
        materials = dictionary_service.get_materials()
        for m in materials:
            self.combo_mat.addItem(f"{m['name']} ({m['price']} грн/{m['unit']})", userData=m['id'])

        self.input_quantity = self.create_line_edit("Введіть кількість...")

        btn_add_mat = self.create_action_button("Додати до звіту", primary=True)
        btn_add_mat.clicked.connect(self.submit_material)

        form.addRow("ID заявки:", self.input_req_id)
        form.addRow("Матеріал:", self.combo_mat)
        form.addRow("Кількість:", self.input_quantity)
        form.addRow("", btn_add_mat)

        layout.addWidget(group)

        self.works_table = QTableWidget()
        self.works_table.setColumnCount(5)
        self.works_table.setHorizontalHeaderLabels(["ID Списання", "Заявка", "Матеріал", "Кількість", "Сума"])
        self.works_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.works_table.setRowCount(0)

        filters = self.create_table_filters(self.works_table)
        layout.addWidget(filters)
        layout.addWidget(self.works_table)

        return page

    def submit_material(self):
        req_id = self.input_req_id.text().strip()
        qty = self.input_quantity.text().strip()
        mat_id = self.combo_mat.currentData()

        if not req_id or not qty or not req_id.isdigit():
            QMessageBox.warning(self, "Помилка", "Введіть коректний ID заявки та кількість!")
            return

        success, msg = worker_service.write_off_material(int(req_id), mat_id, qty)
        if success:
            QMessageBox.information(self, "Успіх", msg)
            self.input_quantity.clear()
            self.refresh_works_table()
        else:
            QMessageBox.critical(self, "Помилка", msg)

    def refresh_works_table(self):
        self.works_table.setRowCount(0)
        data = worker_service.get_used_materials_report()
        for row_data in data:
            self.add_table_row(self.works_table, row_data)

# ==========================================
    # 4. КАРТА ІНФРАСТРУКТУРИ (РОЗШИРЕНА ІНФОРМАЦІЯ НА МАРКЕРАХ)
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

        btn_refresh_map = self.create_action_button("Оновити карту", primary=True)
        btn_refresh_map.clicked.connect(lambda: self.refresh_map_table())
        left_lay.addWidget(btn_refresh_map)

        self.web_map = QWebEngineView()

        # ОНОВЛЕНИЙ HTML ТА JAVASCRIPT З ГАРНИМ ПОПАПОМ
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style> 
                body { margin: 0; padding: 0; } 
                #map { height: 100vh; width: 100%; } 
                .popup-custom { font-family: 'Segoe UI', sans-serif; min-width: 220px; line-height: 1.5; }
                .popup-custom h4 { margin: 0 0 8px 0; color: #8B5CF6; border-bottom: 1px solid #ddd; padding-bottom: 4px;}
                .popup-custom b { color: #333; }
                .desc-box { background-color: #f8f9fa; padding: 6px; border-radius: 4px; border: 1px solid #e9ecef; margin-top: 5px; font-size: 13px; color: #555;}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var bounds = L.latLngBounds(L.latLng(50.21, 30.20), L.latLng(50.59, 30.85));
                var map = L.map('map', { maxBounds: bounds, maxBoundsViscosity: 1.0, minZoom: 11 }).setView([50.4501, 30.5234], 12);
                L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { attribution: '&copy; CARTO' }).addTo(map);
                
                var markers = []; 
                function clearMarkers() { markers.forEach(m => map.removeLayer(m)); markers = []; }
                
                // ОНОВЛЕНО: приймаємо ВСІ дані для попапу
                function addMarker(id, display_addr, search_addr, status, criticality, issue_type, desc, applicant, time, crew) {
                    var query = encodeURIComponent(search_addr + ", Київ, Україна");
                    fetch('https://nominatim.openstreetmap.org/search?format=json&limit=1&q=' + query)
                        .then(res => res.json())
                        .then(data => {
                            if(data.length > 0) {
                                var lat = data[0].lat;
                                var lon = data[0].lon;
                                
                                var color = "blue"; 
                                var crit = criticality.toLowerCase();
                                if (crit.includes("критич")) color = "red";
                                else if (crit.includes("висок")) color = "orange";
                                else if (crit.includes("низьк")) color = "green";
                                
                                var customIcon = L.icon({
                                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-' + color + '.png',
                                    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                                    iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34]
                                });

                                // ВЕРСТКА ІНФОРМАЦІЙНОГО ВІКНА
                                var popupContent = `
                                    <div class="popup-custom">
                                        <h4>Заявка #${id}</h4>
                                        <b>📅 Час:</b> ${time}<br>
                                        <b>📍 Адреса:</b> ${display_addr}<br>
                                        <b>👤 Заявник:</b> ${applicant}<br>
                                        <b>⚠️ Тип аварії:</b> ${issue_type} <i>(${criticality})</i><br>
                                        <div class="desc-box"><b>📝 Опис:</b> ${desc}</div>
                                        <hr style='margin: 8px 0; border: 0; border-top: 1px solid #ddd;'>
                                        <b>🛠 Статус:</b> ${status}<br>
                                        <b>👷 Виконавець:</b> ${crew}
                                    </div>
                                `;

                                var m = L.marker([lat, lon], {icon: customIcon}).addTo(map).bindPopup(popupContent);
                                markers.push(m);
                            }
                        }).catch(e => console.log(e));
                }
            </script>
        </body>
        </html>
        """
        self.web_map.setHtml(html_content)
        layout.addWidget(left_panel)
        layout.addWidget(self.web_map, stretch=1)
        
        self.web_map.loadFinished.connect(self.on_map_load_finished)
        return page

    def on_map_load_finished(self, ok):
        if ok:
            self.refresh_map_table()

    def refresh_map_table(self):
        self.worker_map_table.setRowCount(0)
        data = worker_service.get_active_requests()
        
        self.web_map.page().runJavaScript("if (typeof clearMarkers === 'function') clearMarkers();")

        # Функція для екранування тексту, щоб він не зламав JavaScript
        def escape_for_js(text):
            if text is None: return ""
            return str(text).replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", " ").replace("\r", "")

        for row in data:
            status = row[6]
            if status != "Виконано" and status != "Скасовано":
                req_id = row[0]
                time = row[1]
                applicant = row[2]
                full_addr = row[3]
                issue_type = row[4]
                crit = row[5]
                crew = row[7]
                desc = row[8]
                
                search_addr = full_addr.split(", кв.")[0].strip()
                self.add_table_row(self.worker_map_table, [req_id, crit, status, full_addr])
                
                # Екрануємо всі параметри перед передачею в браузер
                s_id = escape_for_js(req_id)
                s_full_addr = escape_for_js(full_addr)
                s_search_addr = escape_for_js(search_addr)
                s_status = escape_for_js(status)
                s_crit = escape_for_js(crit)
                s_issue = escape_for_js(issue_type)
                s_desc = escape_for_js(desc)
                s_app = escape_for_js(applicant)
                s_time = escape_for_js(time)
                s_crew = escape_for_js(crew)
                
                # Викликаємо JS функцію з 10 параметрами!
                js_command = f"if (typeof addMarker === 'function') addMarker('{s_id}', '{s_full_addr}', '{s_search_addr}', '{s_status}', '{s_crit}', '{s_issue}', '{s_desc}', '{s_app}', '{s_time}', '{s_crew}');"
                self.web_map.page().runJavaScript(js_command)