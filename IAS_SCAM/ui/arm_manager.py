import json
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QHeaderView, QFileDialog, QMessageBox,
                             QGroupBox, QFrame, QGridLayout, QLineEdit, QDialog, 
                             QTreeWidget, QTreeWidgetItem, QDateEdit, QSpinBox,
                             QAbstractItemView, QMenu, QTableWidgetItem)
from PyQt6.QtCore import Qt, QUrl, QDate, QPoint
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QColor, QShortcut, QKeySequence
from ui.base_arm import BaseArmWindow, StyledComboBox
from services import manager_service, worker_service
from services.api_service import load_address_cache

MONTHS_LIST = ["Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень", 
               "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"]


class ArmManagerWindow(BaseArmWindow):
    """Робоче місце керівника комунального підприємства з геоаналітикою та фінансовим контролем."""
    
    def __init__(self):
        super().__init__("АРМ Керівника комунального підприємства")
        self.setup_menu()
        self.refresh_map()
        self.refresh_budget()
        
        self.shortcut_refresh = QShortcut(QKeySequence("F5"), self)
        self.shortcut_refresh.activated.connect(self.refresh_all_manager_data)

    def refresh_all_manager_data(self):
        """Повноцінно синхронізує показники ефективності, карту інфраструктури та фінансові ліміти."""
        self.refresh_efficiency()
        self.refresh_map()
        self.refresh_budget()

    def get_help_data(self):
        return {
            "Головне про модуль": """
                <h3>АРМ Керівника</h3>
                <p>Це стратегічний інструмент для аналізу та прийняття управлінських рішень. Модуль агрегує дані з усієї системи та представляє їх у вигляді інтерактивних дашбордів, географічної карти та фінансових звітів.</p>
                <p>Основна мета АРМ — надати керівництву повну картину ефективності роботи підприємства, виявити проблемні зони та контролювати використання бюджету.</p>
            """,
            "Ефективність роботи": """
                <h3>Аналіз ефективності (KPI)</h3>
                <p>Цей дашборд призначений для відстеження ключових показників ефективності (KPI) роботи диспетчерської та ремонтних служб за обраний період.</p>
                <ul>
                    <li><b>Фільтрація:</b> Ви можете гнучко налаштувати період аналізу, вказавши дати "З" та "По", а також обрати конкретну категорію аварій для більш детального аналізу. Натисніть <b>"🔍 Застосувати фільтр"</b> для оновлення всіх даних на екрані.</li>
                    <li><b>Статистичні картки:</b> Відображають зведену кількість заявок у розрізі статусів: нові, в роботі, виконані та скасовані за вказаний період.</li>
                    <li><b>Кругова діаграма:</b> Наочно показує, які категорії аварій (наприклад, "Сантехніка", "Електрика") складають найбільшу частку від загальної кількості звернень.</li>
                    <li><b>Таблиця заявок:</b> Містить перелік останніх заявок, що відповідають фільтру. Натисніть <b>правою кнопкою миші (ПКМ)</b> на будь-якій заявці, щоб викликати контекстне меню для швидких дій:
                        <br> • <b>📍 Подивитись на карті</b> — миттєво переходить на вкладку з картою та фокусується на обраній заявці.
                        <br> • <b>💰 Показати витрати</b> — відкриває вкладку бюджету та автоматично фільтрує таблицю витрат по цій заявці.
                    </li>
                </ul>
            """,
            "Карта інфраструктури": """
                <h3>Інтерактивна карта міста</h3>
                <p>Цей інструмент забезпечує візуалізацію всіх поточних аварійних ситуацій на географічній карті Києва, дозволяючи оцінити їх масштаби та просторовий розподіл.</p>
                <ul>
                    <li><b>Кольорові маркери:</b> Кожна заявка позначається маркером, колір якого відповідає рівню критичності:
                        <br><span style='color:red;'>■</span> - Критична, <span style='color:orange;'>■</span> - Висока, <span style='color:green;'>■</span> - Низька, <span style='color:blue;'>■</span> - Інші.
                        <br>При наведенні на маркер з'являється детальна інформація про заявку.</li>
                    <li><b>Синхронізація зі списком:</b> Зліва від карти знаходиться таблиця з усіма активними заявками. Клік по будь-якому рядку в цій таблиці автоматично центрує та наближає карту до відповідної адреси, відкриваючи інформаційне вікно.</li>
                    <li><b>Геокодування:</b> Система автоматично визначає географічні координати адрес. Щоб прискорити роботу, знайдені координати зберігаються в локальному кеші.</li>
                    <li><b>Детальна статистика:</b> Кнопка <b>"📊 Детальна статистика"</b> відкриває вікно з деревоподібним звітом, де заявки згруповані за категоріями та рівнями критичності.</li>
                </ul>
            """,
            "Контроль бюджету": """
                <h3>Фінанси та звіти</h3>
                <p>Розділ для повного контролю за фінансовими витратами підприємства на закупівлю та списання матеріалів для ремонтних робіт.</p>
                <ul>
                    <li><b>Встановлення ліміту:</b> Ви можете встановити місячний бюджетний ліміт. Для цього оберіть місяць та рік, вкажіть суму у гривнях та натисніть <b>"💾 Зберегти ліміт"</b>.</li>
                    <li><b>Фінансова аналітика:</b> Картки вгорі показують загальний бюджет на обраний період (місяць або рік), суму вже витрачених коштів та залишок. Це дозволяє оперативно контролювати перевитрати.</li>
                    <li><b>Деталізація витрат:</b> У таблиці нижче наведено повний перелік всіх списаних матеріалів із прив'язкою до конкретних заявок.</li>
                    <li><b>Експорт звітів:</b> Система дозволяє генерувати офіційні фінансові звіти за обраний період у форматах <b>📄 Microsoft Word (.docx)</b> та <b>📊 Excel (.xlsx)</b> для подальшої передачі у бухгалтерію або для внутрішнього аналізу.</li>
                </ul>
            """,
            "Оперативність служб": """
                <h3>Оперативність служб (Аналіз SLA)</h3>
                <p>Цей аналітичний розділ призначений для моніторингу швидкості реагування та роботи комунальних служб на кожному етапі обробки заявки (SLA - Service Level Agreement).</p>
                <ul>
                    <li><b>Горизонтальна діаграма:</b> Наочно візуалізує середній час (у годинах), який заявки проводять у кожному зі статусів. Чим довша смуга, тим більше часу йде на відповідний етап, що може свідчити про "вузьке місце" у процесі.</li>
                    <li><b>Детальна таблиця:</b> Поруч із графіком знаходиться таблиця, що відображає точний розрахунок середнього часу та загальну кількість переходів у кожен статус.</li>
                    <li><b>Кольорове сповіщення:</b> Для швидкого виявлення проблем, система автоматично підсвічує критичні затримки в таблиці:
                        <br><span style='color:#FF5555; font-weight:bold;'>■ Червоний колір</span> — середній простій у статусі перевищує 24 години.
                        <br><span style='color:#FFB86C; font-weight:bold;'>■ Помаранчевий колір</span> — середня затримка становить більше 3 годин.
                    </li>
                    <li><b>Оновлення даних:</b> Кнопка <b>"🔄 Оновити аналітику"</b> дозволяє миттєво перерахувати всі показники на основі найсвіжіших даних з бази.</li>
                </ul>
            """,
            "Гарячі клавіші": """
                <h3>Гарячі клавіші</h3>
                <p>Для прискорення роботи ви можете використовувати наступні комбінації клавіш:</p>
                <ul>
                    <li><b>F1</b> — Відкрити цю довідку.</li>
                    <li><b>F5</b> — Примусово оновити дані на активній вкладці.</li>
                    <li><b>Ctrl+T</b> — Змінити тему оформлення (світла/темна).</li>
                    <li><b>Ctrl+Q</b> — Вийти з поточного робочого місця (АРМ).</li>
                </ul>
            """
        }

    def setup_menu(self):
        """Ініціалізує основні аналітичні вкладки інтерфейсу керівника."""
        self.add_menu_item("Ефективність роботи", self.build_efficiency_page())
        self.add_menu_item("Карта інфраструктури", self.build_map_page())
        self.add_menu_item("Контроль бюджету", self.build_budget_page())
        self.add_menu_item("Оперативність служб", self.build_sla_page())
        self.finalize_menu()

    def build_efficiency_page(self):
        """Конструює сторінку інтерактивних графіків КРІ та аналізу категорій аварійності."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Аналіз ефективності роботи підприємства")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        filter_group = QGroupBox("Фільтрація даних")
        filter_lay = QHBoxLayout(filter_group)

        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDisplayFormat("dd.MM.yyyy")
        self.date_start.setDate(QDate.currentDate().addDays(-30))
        self.date_start.setMinimumWidth(160)

        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDisplayFormat("dd.MM.yyyy")
        self.date_end.setDate(QDate.currentDate())
        self.date_end.setMinimumWidth(160)

        self.cb_category = StyledComboBox()
        self.cb_category.addItem("Всі категорії")
        self.cb_category.setMinimumWidth(200)

        btn_filter = self.create_action_button("🔍 Застосувати фільтр")
        btn_filter.clicked.connect(self.refresh_efficiency)

        filter_lay.addWidget(QLabel("З:"))
        filter_lay.addWidget(self.date_start)
        filter_lay.addWidget(QLabel("По:"))
        filter_lay.addWidget(self.date_end)
        filter_lay.addSpacing(20)
        filter_lay.addWidget(QLabel("Категорія:"))
        filter_lay.addWidget(self.cb_category)
        filter_lay.addWidget(btn_filter)
        filter_lay.addStretch()
        layout.addWidget(filter_group)

        stats_lay = QHBoxLayout()
        self.card_new = self.create_stat_card("Нові", "0", "#8BE9FD")
        self.lbl_new = self.card_new.findChild(QLabel, "stat_value")
        self.card_prog = self.create_stat_card("В роботі", "0", "#FFB86C")
        self.lbl_prog = self.card_prog.findChild(QLabel, "stat_value")
        self.card_done = self.create_stat_card("Виконані", "0", "#50FA7B")
        self.lbl_done = self.card_done.findChild(QLabel, "stat_value")
        self.card_canc = self.create_stat_card("Скасовані", "0", "#FF5555")
        self.lbl_canc = self.card_canc.findChild(QLabel, "stat_value")
        
        stats_lay.addWidget(self.card_new)
        stats_lay.addWidget(self.card_prog)
        stats_lay.addWidget(self.card_done)
        stats_lay.addWidget(self.card_canc)
        layout.addLayout(stats_lay)

        data_layout = QHBoxLayout()

        self.chart_view = QWebEngineView()
        self.chart_view.setMinimumWidth(400)
        self.setup_chart_html()
        self.chart_view.loadFinished.connect(lambda ok: self.refresh_efficiency() if ok else None)
        
        data_layout.addWidget(self.chart_view, stretch=1)

        table_container = QWidget()
        table_lay = QVBoxLayout(table_container)
        table_lay.setContentsMargins(0, 0, 0, 0)

        table_label = QLabel("Останні заявки")
        table_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        table_lay.addWidget(table_label)

        self.eff_table = QTableWidget()
        self.eff_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.eff_table.setColumnCount(6)
        self.eff_table.setHorizontalHeaderLabels(["ID", "Час фіксування", "Категорія", "Бригада", "Критичність", "Статус"])
        self.eff_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.eff_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        
        self.eff_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.eff_table.customContextMenuRequested.connect(self.show_eff_table_context_menu)
        
        self.eff_table.setRowCount(0)

        filters = self.create_table_filters(self.eff_table)
        table_lay.addWidget(filters)
        table_lay.addWidget(self.eff_table)

        data_layout.addWidget(table_container, stretch=2)
        layout.addLayout(data_layout)
        return page

    def show_eff_table_context_menu(self, pos: QPoint):
        """Генерує контекстне меню правого кліку для швидкого переходу між розділами системи."""
        row = self.eff_table.currentRow()
        if row < 0: 
            return
        
        id_item = self.eff_table.item(row, 0)
        if not id_item: 
            return
        req_id = id_item.text()

        menu = QMenu(self)
        if self.is_dark_theme:
            menu.setStyleSheet("QMenu { background-color: #282A36; color: #F8F8F2; border: 1px solid #44475A; } QMenu::item:selected { background-color: #8B5CF6; color: white; }")
        else:
            menu.setStyleSheet("QMenu { background-color: #F8F9FA; color: #2C3E50; border: 1px solid #DEE2E6; } QMenu::item:selected { background-color: #8B5CF6; color: white; }")
        
        act_map = menu.addAction("📍 Подивитись на карті")
        act_budget = menu.addAction("💰 Показати витрати")
        
        action = menu.exec(self.eff_table.viewport().mapToGlobal(pos))
        
        if action == act_map:
            self.stacked_widget.setCurrentIndex(1)
            if hasattr(self, 'menu_buttons') and len(self.menu_buttons) > 1:
                self.active_button = self.menu_buttons[1]
                self.apply_theme()
            self.web_map.page().runJavaScript(f"if(typeof setFocusTarget==='function') setFocusTarget('{req_id}');")
            
        elif action == act_budget:
            self.stacked_widget.setCurrentIndex(2)
            if hasattr(self, 'menu_buttons') and len(self.menu_buttons) > 2:
                self.active_button = self.menu_buttons[2]
                self.apply_theme()
            if hasattr(self, 'budget_filter_inputs'):
                for col, widget in self.budget_filter_inputs:
                    if col == 0 and isinstance(widget, QLineEdit):
                        widget.setText(f"Заявка #{req_id}")
                        break

    def refresh_efficiency(self):
        """Оновлює статистичні дані КРІ, кругову діаграму розподілу та таблицю останніх подій."""
        start_date = self.date_start.date().toPyDate()
        end_date = self.date_end.date().toPyDate()
        
        dt_start = datetime.combine(start_date, datetime.min.time())
        dt_end = datetime.combine(end_date, datetime.min.time())
        
        category = self.cb_category.currentText()
        data = manager_service.get_efficiency_data(dt_start, dt_end, category)
        
        if self.cb_category.count() == 1 and data["categories"]:
            self.cb_category.blockSignals(True)
            self.cb_category.addItems(data["categories"])
            self.cb_category.blockSignals(False)

        if hasattr(self, 'lbl_new'):
            self.lbl_new.setText(str(data["counts"]["new"]))
            self.lbl_prog.setText(str(data["counts"]["in_progress"]))
            self.lbl_done.setText(str(data["counts"]["completed"]))
            self.lbl_canc.setText(str(data["counts"]["cancelled"]))
        
        labels_json = json.dumps(data["chart_labels"], ensure_ascii=False)
        data_json = json.dumps(data["chart_data"])
        js_code = f"if(typeof updateChart === 'function') updateChart({labels_json}, {data_json});"
        self.chart_view.page().runJavaScript(js_code)
        
        self.eff_table.setRowCount(0)
        for row_data in data["table_data"]: 
            self.add_table_row(self.eff_table, row_data)

    def setup_chart_html(self):
        """Інжектує JavaScript графік Chart.js всередину компонента QWebEngineView."""
        bg_color = "#1E1E2E" if self.is_dark_theme else "#F8F9FA"
        text_color = "#F8F8F2" if self.is_dark_theme else "#2C3E50"

        chart_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style> 
                body {{ margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: {bg_color}; transition: background-color 0.3s; }} 
            </style>
        </head>
        <body id="chartBody">
            <div style="width: 95%; height: 95%;">
                <canvas id="myChart"></canvas>
            </div>
            <script>
                const ctx = document.getElementById('myChart');
                var myChart = new Chart(ctx, {{
                    type: 'doughnut',
                    data: {{
                        labels: [],
                        datasets: [{{
                            data: [],
                            backgroundColor: ['#8B5CF6', '#FFB86C', '#FF5555', '#50FA7B', '#8BE9FD', '#F1FA8C', '#BD93F9', '#FF79C6'],
                            borderWidth: 0, hoverOffset: 5
                        }}]
                    }},
                    options: {{ 
                        responsive: true, maintainAspectRatio: false, cutout: '65%',
                        plugins: {{ legend: {{ position: 'bottom', labels: {{ color: '{text_color}', font: {{ size: 14 }} }} }} }} 
                    }}
                }});
                
                function updateChart(newLabels, newData) {{
                    myChart.data.labels = newLabels;
                    myChart.data.datasets[0].data = newData;
                    myChart.update();
                }}

                function changeTheme(isDark) {{
                    document.getElementById('chartBody').style.backgroundColor = isDark ? '#1E1E2E' : '#F8F9FA';
                    myChart.options.plugins.legend.labels.color = isDark ? '#F8F8F2' : '#2C3E50';
                    myChart.update();
                }}
            </script>
        </body>
        </html>
        """
        self.chart_view.setHtml(chart_html)

    def build_map_page(self):
        """Будує інтерфейс інтерактивної карти Leaflet для геомоніторингу інфраструктури."""
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        left_panel = QWidget()
        left_panel.setFixedWidth(350)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Список звернень на карті")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        left_layout.addWidget(title)

        self.map_requests_list = QTableWidget()
        self.map_requests_list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.map_requests_list.setColumnCount(4)
        self.map_requests_list.setHorizontalHeaderLabels(["ID", "Час", "Критичність", "Адреса"])
        header = self.map_requests_list.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.map_requests_list.setRowCount(0)
        self.map_requests_list.itemSelectionChanged.connect(self.on_map_row_selected)

        left_layout.addWidget(self.create_table_filters(self.map_requests_list))
        left_layout.addWidget(self.map_requests_list)

        btn_refresh_map = self.create_action_button("🔄 Оновити")
        btn_refresh_map.clicked.connect(self.refresh_map)
        
        btn_stats = self.create_action_button("📊 Детальна статистика")
        btn_stats.clicked.connect(self.show_map_statistics)
        
        left_layout.addWidget(btn_refresh_map)
        left_layout.addWidget(btn_stats)

        self.web_map = QWebEngineView()
        self.web_map.setStyleSheet("border-radius: 10px; border: 1px solid #44475A;")
        self.web_map.titleChanged.connect(self.handle_map_title_cache)

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
                            } else {
                                document.title = "MAP_READY";
                            }
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
        self.web_map.loadFinished.connect(lambda ok: self.refresh_map() if ok else None)

        layout.addWidget(left_panel)
        layout.addWidget(self.web_map, stretch=1)
        return page

    def handle_map_title_cache(self, title):
        """Слухає зміни заголовків карти для динамічного локального збереження знайдених геокоординат."""
        if title.startswith("CACHE|"):
            parts = title.split("|")
            if len(parts) == 4:
                addr = parts[1]
                lat = float(parts[2])
                lon = float(parts[3])
                
                cache = load_address_cache()
                if addr not in cache:
                    cache[addr] = [lat, lon]
                    from services.api_service import save_address_cache
                    save_address_cache(cache)

    def show_map_statistics(self):
        """Відкриває деревоподібне ієрархічне вікно з розподілом поточних аварій містом."""
        stats = manager_service.get_map_statistics()
        dialog = QDialog(self)
        dialog.setWindowTitle("Детальна статистика аварій")
        dialog.resize(600, 400)
        lay = QVBoxLayout(dialog)
        
        info = QLabel("Розподіл поточних активних заявок містом (за категоріями та критичністю):")
        lay.addWidget(info)
        
        tree = QTreeWidget()
        tree.setHeaderLabels(["Категорія / Район", "Критичність", "Кількість заявок"])
        tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        grouped = {}
        for s in stats:
            cat = s["category"]
            if cat not in grouped: 
                grouped[cat] = []
            grouped[cat].append(s)
            
        for cat, items in grouped.items():
            parent = QTreeWidgetItem(tree, [f"📂 Категорія: {cat}", "", ""])
            total_cat = 0
            for it in items:
                QTreeWidgetItem(parent, ["", it["criticality"], str(it["count"])])
                total_cat += it["count"]
            parent.setText(2, str(total_cat))
            
        tree.expandAll()
        lay.addWidget(tree)
        
        if self.is_dark_theme:
            dialog.setStyleSheet("QDialog { background-color: #282A36; color: #F8F8F2; } QTreeWidget { background-color: #1E1E2E; color: #F8F8F2; border: 1px solid #44475A; border-radius: 6px; }")
            info.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px; color: #8B5CF6;")
        else:
            dialog.setStyleSheet("QDialog { background-color: #F8F9FA; color: #2C3E50; } QTreeWidget { background-color: #FFFFFF; color: #2C3E50; border: 1px solid #DEE2E6; border-radius: 6px; }")
            info.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px; color: #8B5CF6;")
            
        dialog.exec()

    def refresh_map(self):
        """Оновлює маркери та списки на інтерактивній карті."""
        self.map_requests_list.setRowCount(0)
        self.web_map.page().runJavaScript("if (typeof clearMarkers === 'function') clearMarkers();")
        
        data = worker_service.get_active_requests(show_all=False)
        address_cache = load_address_cache()
        
        def escape_js(t): 
            return str(t or "").replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", " ")

        for row in data:
            req_time = row["request_date"].strftime("%H:%M %d.%m") if row.get("request_date") else ""
            display_addr = f"{row['street'] or ''}, кв. {row['apartment'] or ''}".strip(", ")
            self.add_table_row(self.map_requests_list, [str(row["id"]), req_time, row["criticality"], display_addr])
            
            search_addr = row["street"].strip()
            search_addr_lower = search_addr.lower()
            
            lat, lon = "null", "null"
            if search_addr_lower in address_cache:
                lat = address_cache[search_addr_lower][0]
                lon = address_cache[search_addr_lower][1]
            
            applicant = f"{row.get('applicant_last', '')} {row.get('applicant_first', '')}".strip() or "Невідомо"
            desc = row.get("description", "Опис відсутній")
            crew = f"Бригада №{row['crew_number']}" if row.get("crew_number") else "Не призначено"

            js = f"if(typeof addMarker==='function') addMarker('{row['id']}','{escape_js(display_addr)}','{escape_js(search_addr)}','{escape_js(row['status'])}','{escape_js(row['criticality'])}','{escape_js(row['issue_type'])}','{escape_js(desc)}','{escape_js(applicant)}','{escape_js(req_time)}','{escape_js(crew)}', {lat}, {lon});"
            self.web_map.page().runJavaScript(js)

    def on_map_row_selected(self):
        """Фокусує і наближає карту до об'єкта при виборі його в таблиці."""
        row = self.map_requests_list.currentRow()
        if row >= 0:
            item = self.map_requests_list.item(row, 0)
            if item: 
                self.web_map.page().runJavaScript(f"if(typeof setFocusTarget==='function') setFocusTarget('{item.text()}');")

    def build_budget_page(self):
        """Будує інтерфейс моніторингу видатків, фінансових лімітів та генерації офіційних звітів."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Контроль бюджету та витрат")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)
        
        view_group = QGroupBox("Перегляд звіту за період")
        view_lay = QHBoxLayout(view_group)
        
        self.cb_view_month = StyledComboBox()
        self.cb_view_month.addItem("Весь час (Всі витрати)")
        self.cb_view_month.addItem("Всі місяці (Весь рік)")
        self.cb_view_month.addItems(MONTHS_LIST)
        self.cb_view_month.setCurrentIndex(datetime.now().month + 1)
        self.cb_view_month.setMinimumWidth(200)
        
        self.spin_view_year = QSpinBox()
        self.spin_view_year.setRange(2020, 2100)
        self.spin_view_year.setValue(datetime.now().year)
        self.spin_view_year.setMinimumWidth(100)
        
        self.cb_view_month.currentIndexChanged.connect(self.refresh_budget)
        self.spin_view_year.valueChanged.connect(self.refresh_budget)
        
        view_lay.addWidget(QLabel("Місяць:"))
        view_lay.addWidget(self.cb_view_month)
        view_lay.addWidget(QLabel("Рік:"))
        view_lay.addWidget(self.spin_view_year)
        view_lay.addStretch()
        layout.addWidget(view_group)

        budget_grid = QGridLayout()
        self.card_total_budget = self.create_stat_card("Загальний бюджет", "0 ₴", "#8B5CF6")
        self.val_total_budget = self.card_total_budget.findChild(QLabel, "stat_value")
        self.card_spent = self.create_stat_card("Вже витрачено", "0 ₴", "#FFB86C")
        self.val_spent = self.card_spent.findChild(QLabel, "stat_value")
        self.card_rem = self.create_stat_card("Залишок фонду", "0 ₴", "#50FA7B")
        self.val_rem = self.card_rem.findChild(QLabel, "stat_value")
        
        budget_grid.addWidget(self.card_total_budget, 0, 0)
        budget_grid.addWidget(self.card_spent, 0, 1)
        budget_grid.addWidget(self.card_rem, 0, 2)
        layout.addLayout(budget_grid)

        set_group = QGroupBox("Встановити ліміт бюджету")
        set_lay = QHBoxLayout(set_group)
        
        self.cb_set_month = StyledComboBox()
        self.cb_set_month.addItems(MONTHS_LIST)
        self.cb_set_month.setCurrentIndex(datetime.now().month - 1)
        self.cb_set_month.setMinimumWidth(150)
        
        self.spin_set_year = QSpinBox()
        self.spin_set_year.setRange(2020, 2100)
        self.spin_set_year.setValue(datetime.now().year)
        self.spin_set_year.setMinimumWidth(100)
        
        self.input_budget = QLineEdit()
        self.input_budget.setPlaceholderText("Сума (₴)")
        self.input_budget.setFixedWidth(120)
        
        btn_set_budget = self.create_action_button("💾 Зберегти ліміт")
        btn_set_budget.clicked.connect(self.save_new_budget)
        self.input_budget.returnPressed.connect(self.save_new_budget)
        
        set_lay.addWidget(QLabel("Встановити на:"))
        set_lay.addWidget(self.cb_set_month)
        set_lay.addWidget(self.spin_set_year)
        set_lay.addWidget(self.input_budget)
        set_lay.addWidget(btn_set_budget)
        set_lay.addStretch()
        layout.addWidget(set_group)

        table_label = QLabel("Деталізація витрат на ремонти")
        table_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(table_label)

        self.budget_table = QTableWidget()
        self.budget_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.budget_table.setColumnCount(5)
        self.budget_table.setHorizontalHeaderLabels(["Заявка", "Матеріал", "Ціна", "Кількість", "Сума"])
        self.budget_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        filters = self.create_table_filters(self.budget_table)
        self.budget_filter_inputs = getattr(self, 'filter_inputs', [])
        layout.addWidget(filters)
        layout.addWidget(self.budget_table)

        rep_lay = QHBoxLayout()
        rep_lay.addStretch()
        
        btn_export_word = self.create_action_button("📄 Експорт (Word)")
        btn_export_word.clicked.connect(self.export_budget_to_word)
        
        btn_export_excel = self.create_action_button("📊 Експорт (Excel)")
        btn_export_excel.clicked.connect(self.export_budget_to_excel)
        
        rep_lay.addWidget(btn_export_word)
        rep_lay.addWidget(btn_export_excel)
        layout.addLayout(rep_lay)

        return page

    def save_new_budget(self):
        """Зберігає оновлену граничну суму бюджету для підприємства у БД."""
        val = self.input_budget.text().strip()
        month_idx = self.cb_set_month.currentIndex() + 1
        year = self.spin_set_year.value()
        try:
            amount = float(val.replace(',', '.'))
            manager_service.set_budget(year, month_idx, amount)
            self.input_budget.clear()
            self.refresh_budget()
            QMessageBox.information(self, "Успіх", f"Бюджет успішно оновлено на {MONTHS_LIST[month_idx-1]} {year}!")
        except ValueError: 
            QMessageBox.critical(self, "Помилка", "Введіть коректне число!")

    def refresh_budget(self):
        """Завантажує деталізовані дані фінансового звіту з БД за обраний період."""
        idx = self.cb_view_month.currentIndex()
        year = self.spin_view_year.value()
        
        if idx == 0: 
            month = -1
        elif idx == 1: 
            month = 0
        else: 
            month = idx - 1
        
        self.current_budget_data = manager_service.get_budget_data(year, month)
        data = self.current_budget_data
        
        if hasattr(self, 'val_total_budget'):
            self.val_total_budget.setText(f"{data['total_budget']:,.0f} ₴".replace(',', ' '))
            self.val_spent.setText(f"{data['spent']:,.0f} ₴".replace(',', ' '))
            self.val_rem.setText(f"{data['remaining']:,.0f} ₴".replace(',', ' '))
            
        self.budget_table.setRowCount(0)
        for row_data in data["table_data"]: 
            self.add_table_row(self.budget_table, row_data)

    def export_budget_to_word(self):
        """Формує офіційний документ звітності у форматі Microsoft Word (.docx)."""
        if not hasattr(self, 'current_budget_data'): 
            return
        suffix = self.current_budget_data.get('file_suffix', 'звіт')
        default_filename = f"Звіт_Витрат_за_{suffix}.docx"
        path, _ = QFileDialog.getSaveFileName(self, "Зберегти звіт у Word", default_filename, "Word Documents (*.docx)")
        if not path: 
            return
        try:
            manager_service.generate_word_report(path, self.current_budget_data)
            QMessageBox.information(self, "Успіх", f"Звіт Word успішно сформовано!\n{path}")
        except Exception as e: 
            QMessageBox.critical(self, "Помилка", f"Помилка: {str(e)}")

    def export_budget_to_excel(self):
        """Експортує фінансові таблиці ТМЦ у зведені таблиці Microsoft Excel (.xlsx)."""
        if not hasattr(self, 'current_budget_data'): 
            return
        suffix = self.current_budget_data.get('file_suffix', 'звіт')
        default_filename = f"Звіт_Витрат_за_{suffix}.xlsx"
        path, _ = QFileDialog.getSaveFileName(self, "Зберегти звіт в Excel", default_filename, "Excel Files (*.xlsx)")
        if not path: 
            return
        try:
            manager_service.generate_excel_report(path, self.current_budget_data)
            QMessageBox.information(self, "Успіх", f"Звіт Excel успішно сформовано!\n{path}")
        except Exception as e: 
            QMessageBox.critical(self, "Помилка", f"Помилка: {str(e)}")



    def apply_theme(self):
        """Коригує графічний стиль та тему відображення вбудованих веб-графіків."""
        super().apply_theme()
        
        if hasattr(self, 'chart_view'):
            border_color = "#44475A" if self.is_dark_theme else "#DEE2E6"
            self.chart_view.setStyleSheet(f"background: transparent; border-radius: 10px; border: 1px solid {border_color};")
            is_dark_str = 'true' if self.is_dark_theme else 'false'
            self.chart_view.page().runJavaScript(f"if(typeof changeTheme === 'function') changeTheme({is_dark_str});")

        if hasattr(self, 'sla_chart_view'):
            border_col = "#44475A" if self.is_dark_theme else "#DEE2E6"
            self.sla_chart_view.setStyleSheet(
                f"background: transparent; border-radius: 10px; border: 1px solid {border_col};")

            is_dark_str = 'true' if self.is_dark_theme else 'false'
            self.sla_chart_view.page().runJavaScript(
                f"if(typeof changeTheme === 'function') changeTheme({is_dark_str});")

    def create_stat_card(self, title_text, value_text, color):
        """Фабричний метод створення інформаційних карток для дашборду."""
        card = QFrame()
        card.setObjectName("stat_card")
        card.setProperty("accent_color", color)
        card_lay = QVBoxLayout(card)
        card_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title = QLabel(title_text)
        lbl_title.setObjectName("stat_title")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_val = QLabel(value_text)
        lbl_val.setObjectName("stat_value")
        lbl_val.setProperty("accent_color", color)
        lbl_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_lay.addWidget(lbl_title)
        card_lay.addWidget(lbl_val)
        return card
    
    def build_sla_page(self):
        """Створює сторінку аналізу швидкості роботи з горизонтальним графіком та таблицею."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Аналіз швидкості виконання заявок")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        border_color = "#44475A" if self.is_dark_theme else "#DEE2E6"

        chart_and_table_layout = QHBoxLayout()

        self.sla_chart_view = QWebEngineView()
        self.sla_chart_view.setMinimumWidth(450)
        self.sla_chart_view.setStyleSheet(
            f"background: transparent; border-radius: 10px; border: 1px solid {border_color};")

        self.setup_sla_chart_html()
        chart_and_table_layout.addWidget(self.sla_chart_view, stretch=4)

        table_container = QWidget()
        table_lay = QVBoxLayout(table_container)
        table_lay.setContentsMargins(0, 0, 0, 0)
        table_lay.setSpacing(5)

        lbl_tbl = QLabel("Середній час перебування заявок у стані:")
        lbl_tbl.setStyleSheet("font-size: 15px; font-weight: bold;")
        lbl_descr = QLabel("Показує середню тривалість обробки на кожному кроці життєвого циклу.")
        lbl_descr.setStyleSheet("color: #A6ADC8; font-size: 13px; margin-bottom: 5px;")

        self.sla_table = QTableWidget()
        self.sla_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.sla_table.setColumnCount(3)
        self.sla_table.setHorizontalHeaderLabels([
            "Назва статусу системи", "Середній час перебування", "Кількість переходів"
        ])
        self.sla_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        table_lay.addWidget(lbl_tbl)
        table_lay.addWidget(lbl_descr)
        table_lay.addWidget(self.sla_table)

        chart_and_table_layout.addWidget(table_container, stretch=5)
        layout.addLayout(chart_and_table_layout)

        btn_refresh_sla = self.create_action_button("🔄 Оновити аналітику", primary=True)
        btn_refresh_sla.clicked.connect(self.refresh_sla_analytics)
        layout.addWidget(btn_refresh_sla, alignment=Qt.AlignmentFlag.AlignLeft)

        self.sla_chart_view.loadFinished.connect(lambda ok: self.refresh_sla_analytics() if ok else None)
        return page

    def web_content_sla_widget(self):
        return QWidget()
    def setup_sla_chart_html(self):
        """Генерує HTML сторінку з горизонтальним стовпчиковим графіком та підтримкою зміни тем."""
        bg_color = "#1E1E2E" if self.is_dark_theme else "#F8F9FA"
        text_color = "#F8F8F2" if self.is_dark_theme else "#2C3E50"

        chart_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style> 
                body {{ margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: {bg_color}; transition: background-color 0.3s; }} 
            </style>
        </head>
        <body id="slaChartBody">
            <div style="width: 95%; height: 90%;">
                <canvas id="slaChart"></canvas>
            </div>
            <script>
                const ctx = document.getElementById('slaChart');
                var slaChart = new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: [],
                        datasets: [{{
                            label: 'Середня тривалість (год)',
                            data: [],
                            backgroundColor: '#8B5CF6',
                            borderRadius: 5,
                            borderWidth: 0
                        }}]
                    }},
                    options: {{
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{ display: false }},
                            tooltip: {{ callbacks: {{ label: function(context) {{ return ' ' + context.raw + ' год.'; }} }} }}
                        }},
                        scales: {{
                            x: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '{text_color}' }} }},
                            y: {{ grid: {{ display: false }}, ticks: {{ color: '{text_color}', font: {{ size: 13, weight: 'bold' }} }} }}
                        }}
                    }}
                }});

                function updateSlaChart(labels, dataValues) {{
                    slaChart.data.labels = labels;
                    slaChart.data.datasets[0].data = dataValues;
                    slaChart.update();
                }}

                function changeTheme(isDark) {{
                    document.getElementById('slaChartBody').style.backgroundColor = isDark ? '#1E1E2E' : '#F8F9FA';

                    const newTextColor = isDark ? '#F8F8F2' : '#2C3E50';
                    const newGridColor = isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)';

                    slaChart.options.scales.x.ticks.color = newTextColor;
                    slaChart.options.scales.y.ticks.color = newTextColor;
                    slaChart.options.scales.x.grid.color = newGridColor;

                    slaChart.update();
                }}
            </script>
        </body>
        </html>
        """
        self.sla_chart_view.setHtml(chart_html)

    def refresh_sla_analytics(self):
        """Зчитує дані, заповнює таблицю та передає масиви на графік."""
        if not hasattr(self, 'sla_table') or not hasattr(self, 'sla_chart_view'):
            return

        self.sla_table.setRowCount(0)
        sla_data = manager_service.get_status_duration_statistics()

        chart_labels = []
        chart_values = []

        for row_idx, row in enumerate(sla_data):
            self.sla_table.insertRow(row_idx)

            hours_float = round(row["avg_seconds"] / 3600, 2)
            chart_labels.append(row["status_name"])
            chart_values.append(hours_float)

            item_status = QTableWidgetItem(row["status_name"])
            item_time = QTableWidgetItem(row["time_display"])
            item_count = QTableWidgetItem(f"{row['transitions_count']} разів")

            if row["avg_seconds"] > 86400:
                item_time.setForeground(QColor("#FF5555"))
            elif row["avg_seconds"] > 10800:
                item_time.setForeground(QColor("#FFB86C"))

            self.sla_table.setItem(row_idx, 0, item_status)
            self.sla_table.setItem(row_idx, 1, item_time)
            self.sla_table.setItem(row_idx, 2, item_count)

        labels_json = json.dumps(chart_labels, ensure_ascii=False)
        values_json = json.dumps(chart_values)
        js_code = f"if(typeof updateSlaChart === 'function') updateSlaChart({labels_json}, {values_json});"
        self.sla_chart_view.page().runJavaScript(js_code)

        self.apply_theme()

    def on_menu_click(self, index, btn):
        """Перехоплює клік по боковому меню АРМ Керівника."""
        super().on_menu_click(index, btn)

        if index == 3:
            self.refresh_sla_analytics()