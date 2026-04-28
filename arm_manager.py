from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QHeaderView,
                             QGroupBox, QFrame, QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView
from base_arm import BaseArmWindow, StyledComboBox


class ArmManagerWindow(BaseArmWindow):
    def __init__(self):
        super().__init__("АРМ Керівника комунального підприємства")
        self.setup_menu()

    def setup_menu(self):
        self.add_menu_item("Ефективність роботи", self.build_efficiency_page())
        self.add_menu_item("Карта інфраструктури", self.build_map_page())
        self.add_menu_item("Контроль бюджету", self.build_budget_page())
        self.finalize_menu()

    # ==========================================
    # 1. АНАЛІЗ ЕФЕКТИВНОСТІ РОБОТИ СЛУЖБ
    # ==========================================
    def build_efficiency_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Аналіз ефективності роботи служб")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        filter_group = QGroupBox("Фільтрація даних")
        filter_lay = QHBoxLayout(filter_group)

        self.cb_period = StyledComboBox()
        self.cb_period.addItems(["За поточний тиждень", "За поточний місяць", "За рік"])

        self.cb_category = StyledComboBox()
        self.cb_category.addItems(["Всі служби", "Водопостачання", "Електропостачання", "Опалення", "Благоустрій"])

        btn_filter = self.create_action_button("Застосувати фільтр", primary=True)

        filter_lay.addWidget(QLabel("Період:"))
        filter_lay.addWidget(self.cb_period)
        filter_lay.addWidget(QLabel("Служба:"))
        filter_lay.addWidget(self.cb_category)
        filter_lay.addWidget(btn_filter)
        filter_lay.addStretch()

        layout.addWidget(filter_group)

        stats_lay = QHBoxLayout()
        stats_lay.addWidget(self.create_stat_card("Всього виконано", "0", "#50FA7B"))
        stats_lay.addWidget(self.create_stat_card("В процесі роботи", "0", "#8BE9FD"))
        stats_lay.addWidget(self.create_stat_card("Порушення термінів", "0", "#FF5555"))
        layout.addLayout(stats_lay)

        data_layout = QHBoxLayout()

        self.chart_view = QWebEngineView()
        self.chart_view.setMinimumWidth(400)

        self.refresh_chart_html()
        data_layout.addWidget(self.chart_view, stretch=1)

        table_container = QWidget()
        table_lay = QVBoxLayout(table_container)
        table_lay.setContentsMargins(0, 0, 0, 0)

        table_label = QLabel("Останні закриті заявки")
        table_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        table_lay.addWidget(table_label)

        self.eff_table = QTableWidget()
        self.eff_table.setColumnCount(6)
        self.eff_table.setHorizontalHeaderLabels(["ID", "Час фіксування", "Служба", "Бригада", "Критичність", "Статус"])
        self.eff_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.eff_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.eff_table.setRowCount(0)

        filters = self.create_table_filters(self.eff_table)
        table_lay.addWidget(filters)
        table_lay.addWidget(self.eff_table)

        data_layout.addWidget(table_container, stretch=2)
        layout.addLayout(data_layout)
        return page

    def refresh_chart_html(self):
        if not hasattr(self, 'chart_view'):
            return

        text_color = "#F8F8F2" if self.is_dark_theme else "#2C3E50"
        bg_color = "#181825" if self.is_dark_theme else "#F8F9FA"

        chart_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style> 
                body {{ margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: {bg_color}; }} 
            </style>
        </head>
        <body>
            <div style="width: 90%; height: 90%;">
                <canvas id="myChart"></canvas>
            </div>
            <script>
                const ctx = document.getElementById('myChart');
                new Chart(ctx, {{
                    type: 'doughnut',
                    data: {{
                        labels: ['Водопостачання', 'Електропостачання', 'Опалення', 'Благоустрій'],
                        datasets: [{{
                            data: [0, 0, 0, 0],
                            backgroundColor: ['#8B5CF6', '#FFB86C', '#FF5555', '#50FA7B'],
                            borderWidth: 0
                        }}]
                    }},
                    options: {{ 
                        responsive: true, 
                        maintainAspectRatio: false, 
                        plugins: {{ legend: {{ position: 'bottom', labels: {{ color: '{text_color}' }} }} }} 
                    }}
                }});
            </script>
        </body>
        </html>
        """
        self.chart_view.setHtml(chart_html)

    # ==========================================
    # 2. ВІЗУАЛІЗАЦІЯ ПРОБЛЕМНИХ ДІЛЯНОК
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
        self.map_requests_list.setColumnCount(4)
        self.map_requests_list.setHorizontalHeaderLabels(["ID", "Час", "Критичність", "Адреса"])

        header = self.map_requests_list.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.map_requests_list.setRowCount(0)
        self.map_requests_list.itemSelectionChanged.connect(self.on_map_row_selected)

        filters = self.create_table_filters(self.map_requests_list)
        left_layout.addWidget(filters)
        left_layout.addWidget(self.map_requests_list)

        btn_refresh_map = self.create_action_button("Оновити карту", primary=True)
        btn_refresh_map.clicked.connect(self.refresh_map)
        left_layout.addWidget(btn_refresh_map)

        self.web_map = QWebEngineView()
        self.web_map.setStyleSheet("border-radius: 10px; border: 1px solid #44475A;")

        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style> body { margin: 0; padding: 0; } #map { height: 100vh; width: 100%; } </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var bounds = L.latLngBounds(L.latLng(50.21, 30.20), L.latLng(50.59, 30.85));
                var map = L.map('map', { maxBounds: bounds, maxBoundsViscosity: 1.0, minZoom: 11 }).setView([50.4501, 30.5234], 12);
                L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { attribution: '&copy; CARTO' }).addTo(map);

                var markers = []; 
                function addMarker(lat, lng, popupText) {
                    var marker = L.marker([lat, lng]).addTo(map);
                    marker.bindPopup("<b>" + popupText + "</b>");
                    markers.push(marker);
                    map.flyTo([lat, lng], 15);
                }
                function clearMarkers() {
                    for(var i = 0; i < markers.length; i++) map.removeLayer(markers[i]);
                    markers = [];
                }
            </script>
        </body>
        </html>
        """
        self.web_map.setHtml(html_content)

        layout.addWidget(left_panel)
        layout.addWidget(self.web_map, stretch=1)

        return page

    def on_map_row_selected(self):
        pass

    def refresh_map(self):
        self.web_map.page().runJavaScript("clearMarkers();")

    # ==========================================
    # 3. КОНТРОЛЬ РОЗПОДІЛУ БЮДЖЕТУ
    # ==========================================
    def build_budget_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Контроль бюджету та витрат")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        budget_grid = QGridLayout()
        budget_grid.addWidget(self.create_stat_card("Загальний бюджет (Місяць)", "0 ₴", "#8B5CF6"), 0, 0)
        budget_grid.addWidget(self.create_stat_card("Вже витрачено", "0 ₴", "#FFB86C"), 0, 1)
        budget_grid.addWidget(self.create_stat_card("Залишок фонду", "0 ₴", "#50FA7B"), 0, 2)
        layout.addLayout(budget_grid)

        table_label = QLabel("Деталізація витрат на ремонти")
        table_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(table_label)

        self.budget_table = QTableWidget()
        self.budget_table.setColumnCount(5)
        self.budget_table.setHorizontalHeaderLabels(
            ["Заявка", "Матеріал", "Ціна", "Кількість", "Сума"])
        self.budget_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.budget_table.setRowCount(0)

        filters = self.create_table_filters(self.budget_table)
        layout.addWidget(filters)
        layout.addWidget(self.budget_table)

        rep_lay = QHBoxLayout()
        rep_lay.addStretch()
        rep_lay.addWidget(self.create_action_button("Сформувати звіт", primary=True))
        rep_lay.addWidget(self.create_action_button("Експорт в Excel"))
        layout.addLayout(rep_lay)

        return page

    def apply_theme(self):
        super().apply_theme()
        border_color = "#44475A" if self.is_dark_theme else "#DEE2E6"
        if hasattr(self, 'chart_view'):
            self.chart_view.setStyleSheet(f"border-radius: 10px; border: 1px solid {border_color};")
        self.refresh_chart_html()

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