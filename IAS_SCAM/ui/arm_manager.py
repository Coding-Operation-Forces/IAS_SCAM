import csv
import json
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QHeaderView, QFileDialog, QMessageBox,
                             QGroupBox, QFrame, QGridLayout, QLineEdit, QDialog, 
                             QTreeWidget, QTreeWidgetItem, QDateEdit, QSpinBox, QAbstractItemView, QMenu)
from PyQt6.QtCore import Qt, QUrl, QDate, QPoint
from PyQt6.QtWebEngineWidgets import QWebEngineView

from ui.base_arm import BaseArmWindow, StyledComboBox
from services import manager_service, worker_service
from services.api_service import load_address_cache, save_address_cache # Використовуємо новий кеш!

MONTHS_LIST = ["Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень", 
               "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"]

class ArmManagerWindow(BaseArmWindow):
    def __init__(self):
        super().__init__("АРМ Керівника комунального підприємства")
        self.setup_menu()
        
        self.refresh_map()
        self.refresh_budget()

    def get_help_data(self):
        return {
            "Головне про модуль": """
                <h3>АРМ Керівника</h3>
                <p>Модуль розроблений для прийняття управлінських рішень. Він надає зведену аналітику, візуалізацію даних на географічній карті та дозволяє контролювати фінансові витрати підприємства.</p>
            """,
            "Ефективність роботи": """
                <h3>Аналіз ефективності</h3>
                <p>Дашборд для відстеження KPI (ключових показників ефективності) підприємства за вибраний період.</p>
                <ul>
                    <li><b>Фільтрація:</b> Вкажіть період дат та категорію аварій. Натисніть "Застосувати", щоб оновити графіки та таблицю.</li>
                    <li><b>Статистика:</b> Картки показують кількість нових, поточних, виконаних та скасованих заявок.</li>
                    <li><b>Діаграма:</b> Відображає частку кожної категорії проблем у загальному обсязі (Doughnut Chart).</li>
                    <li><b>Контекстне меню:</b> Натисніть <b>правою кнопкою миші (ПКМ)</b> на заявці в таблиці внизу, щоб швидко перейти до її розташування на карті або подивитись витрати по ній.</li>
                </ul>
            """,
            "Карта інфраструктури": """
                <h3>Інтерактивна карта міста</h3>
                <p>Візуалізація всіх поточних звернень громадян.</p>
                <ul>
                    <li><b>Пошук адрес:</b> Система автоматично шукає координати (геокодування) введених вулиць та кешує їх для швидкого завантаження у майбутньому.</li>
                    <li><b>Кольори маркерів:</b> 
                        <span style='color:red;'>Червоний</span> — критичні аварії; 
                        <span style='color:orange;'>Помаранчевий</span> — високий пріоритет; 
                        <span style='color:green;'>Зелений</span> — низький пріоритет; 
                        <span style='color:blue;'>Синій</span> — стандартний.</li>
                    <li><b>Навігація:</b> Клік по рядку в лівій таблиці автоматично наблизить карту до відповідного будинку і відкриє детальний опис проблеми.</li>
                    <li><b>Статистика:</b> Кнопка "Детальна статистика" показує деревоподібний розподіл заявок по місту.</li>
                </ul>
            """,
            "Контроль бюджету": """
                <h3>Фінанси та звіти</h3>
                <p>Розділ для контролю витрат на матеріали при виконанні ремонтних робіт.</p>
                <ul>
                    <li><b>Встановлення ліміту:</b> Виберіть місяць та рік, впишіть суму фонду і натисніть "Зберегти".</li>
                    <li><b>Аналітика:</b> Картки автоматично вираховують загальний бюджет, вже списані кошти та залишок.</li>
                    <li><b>Деталізація:</b> У таблиці наведено список всіх списаних матеріалів із прив'язкою до заявок.</li>
                    <li><b>Експорт:</b> Доступна генерація офіційних звітів у форматах <b>Microsoft Word (.docx)</b> та <b>Excel (.xlsx)</b> за вибраний звітний період.</li>
                </ul>
            """
        }

    def setup_menu(self):
        self.add_menu_item("Ефективність роботи", self.build_efficiency_page())
        self.add_menu_item("Карта інфраструктури", self.build_map_page())
        self.add_menu_item("Контроль бюджету", self.build_budget_page())
        self.finalize_menu()

    # ==========================================
    # 1. АНАЛІЗ ЕФЕКТИВНОСТІ
    # ==========================================
    def build_efficiency_page(self):
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

        btn_filter = self.create_action_button("Застосувати фільтр")
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

        table_label = QLabel("Останні заявки (ПКМ для додаткових дій)")
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
        row = self.eff_table.currentRow()
        if row < 0: return
        
        id_item = self.eff_table.item(row, 0)
        if not id_item: return
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
        for row_data in data["table_data"]: self.add_table_row(self.eff_table, row_data)

    def setup_chart_html(self):
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

    # ==========================================
    # 2. КАРТА ІНФРАСТРУКТУРИ ТА СТАТИСТИКА
    # ==========================================
    def build_map_page(self):
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

        btn_refresh_map = self.create_action_button("Оновити карту")
        btn_refresh_map.clicked.connect(self.refresh_map)
        
        btn_stats = self.create_action_button("📊 Подивитись детальну статистику")
        btn_stats.clicked.connect(self.show_map_statistics)
        
        left_layout.addWidget(btn_refresh_map)
        left_layout.addWidget(btn_stats)

        self.web_map = QWebEngineView()
        self.web_map.setStyleSheet("border-radius: 10px; border: 1px solid #44475A;")

        # --- СИСТЕМА ПЕРЕХОПЛЕННЯ ЗБЕРЕЖЕННЯ В КЕШ ---
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
                                // ПЕРЕДАЄМО ЗНАЙДЕНІ ДАНІ НАЗАД У PYTHON (ДЛЯ ADDRESS_CACHE.JSON)
                                document.title = "CACHE|" + task.search_addr.toLowerCase() + "|" + data[0].lat + "|" + data[0].lon;
                            } else {
                                document.title = "MAP_READY"; // пустий сигнал
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
        # localhost ПОВЕРНУТО! CORS-помилки більше не буде!
        self.web_map.setHtml(html_content, QUrl("http://localhost"))
        self.web_map.loadFinished.connect(lambda ok: self.refresh_map() if ok else None)

        layout.addWidget(left_panel)
        layout.addWidget(self.web_map, stretch=1)
        return page

    def handle_map_title_cache(self, title):
        # Якщо JS знайшов нову адресу в інтернеті, він повідомить Python через заголовок сторінки!
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
            if cat not in grouped: grouped[cat] = []
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
        self.map_requests_list.setRowCount(0)
        self.web_map.page().runJavaScript("if (typeof clearMarkers === 'function') clearMarkers();")
        
        data = worker_service.get_active_requests(show_all=False)
        address_cache = load_address_cache() # ТЕПЕР КАРТА ЧИТАЄ НОВИЙ КЕШ ДЛЯ БУДИНКІВ
        
        def escape_js(t): return str(t or "").replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", " ")

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
        row = self.map_requests_list.currentRow()
        if row >= 0:
            item = self.map_requests_list.item(row, 0)
            if item: self.web_map.page().runJavaScript(f"if(typeof setFocusTarget==='function') setFocusTarget('{item.text()}');")

    # ==========================================
    # 3. КОНТРОЛЬ БЮДЖЕТУ ТА ЗВІТИ
    # ==========================================
    def build_budget_page(self):
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
        
        btn_set_budget = self.create_action_button("Зберегти ліміт")
        btn_set_budget.clicked.connect(self.save_new_budget)
        
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
        val = self.input_budget.text().strip()
        month_idx = self.cb_set_month.currentIndex() + 1
        year = self.spin_set_year.value()
        try:
            amount = float(val.replace(',', '.'))
            manager_service.set_budget(year, month_idx, amount)
            self.input_budget.clear()
            self.refresh_budget()
            QMessageBox.information(self, "Успіх", f"Бюджет успішно оновлено на {MONTHS_LIST[month_idx-1]} {year}!")
        except ValueError: QMessageBox.critical(self, "Помилка", "Введіть коректне число!")

    def refresh_budget(self):
        idx = self.cb_view_month.currentIndex()
        year = self.spin_view_year.value()
        
        if idx == 0: month = -1
        elif idx == 1: month = 0
        else: month = idx - 1
        
        self.current_budget_data = manager_service.get_budget_data(year, month)
        data = self.current_budget_data
        
        if hasattr(self, 'val_total_budget'):
            self.val_total_budget.setText(f"{data['total_budget']:,.0f} ₴".replace(',', ' '))
            self.val_spent.setText(f"{data['spent']:,.0f} ₴".replace(',', ' '))
            self.val_rem.setText(f"{data['remaining']:,.0f} ₴".replace(',', ' '))
            
        self.budget_table.setRowCount(0)
        for row_data in data["table_data"]: self.add_table_row(self.budget_table, row_data)

    def export_budget_to_word(self):
        if not hasattr(self, 'current_budget_data'): return
        suffix = self.current_budget_data.get('file_suffix', 'звіт')
        default_filename = f"Звіт_Витрат_за_{suffix}.docx"
        path, _ = QFileDialog.getSaveFileName(self, "Зберегти звіт у Word", default_filename, "Word Documents (*.docx)")
        if not path: return
        try:
            manager_service.generate_word_report(path, self.current_budget_data)
            QMessageBox.information(self, "Успіх", f"Звіт Word успішно сформовано!\n{path}")
        except Exception as e: QMessageBox.critical(self, "Помилка", f"Помилка: {str(e)}")

    def export_budget_to_excel(self):
        if not hasattr(self, 'current_budget_data'): return
        suffix = self.current_budget_data.get('file_suffix', 'звіт')
        default_filename = f"Звіт_Витрат_за_{suffix}.xlsx"
        path, _ = QFileDialog.getSaveFileName(self, "Зберегти звіт в Excel", default_filename, "Excel Files (*.xlsx)")
        if not path: return
        try:
            manager_service.generate_excel_report(path, self.current_budget_data)
            QMessageBox.information(self, "Успіх", f"Звіт Excel успішно сформовано!\n{path}")
        except Exception as e: QMessageBox.critical(self, "Помилка", f"Помилка: {str(e)}")

    def apply_theme(self):
        super().apply_theme()
        
        if hasattr(self, 'chart_view'):
            border_color = "#44475A" if self.is_dark_theme else "#DEE2E6"
            self.chart_view.setStyleSheet(f"background: transparent; border-radius: 10px; border: 1px solid {border_color};")
            is_dark_str = 'true' if self.is_dark_theme else 'false'
            self.chart_view.page().runJavaScript(f"if(typeof changeTheme === 'function') changeTheme({is_dark_str});")

    def create_stat_card(self, title_text, value_text, color):
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