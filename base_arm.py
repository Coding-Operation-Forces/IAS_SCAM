from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QStackedWidget, QLabel, QFrame, QApplication,
                             QTableWidget, QLineEdit, QComboBox, QTextEdit, QGroupBox,
                             QTabWidget, QTableWidgetItem)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QPoint
from PyQt6.QtGui import QIcon, QPainter, QPen, QColor
import os


class StyledComboBox(QComboBox):
    """QComboBox з власною сучасною chevron-стрілкою (малюється через paintEvent)."""

    arrow_color = QColor("#CDD6F4")
    accent_color = QColor("#8B5CF6")

    def paintEvent(self, event):
        # 1. Стандартний рендер (фон, рамка, текст) — через QSS
        super().paintEvent(event)

        # 2. Поверх малюємо свій chevron
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Колір: фіолетовий при hover/відкритті, інакше звичайний
        if self.underMouse() or self.view().isVisible():
            color = self.accent_color
        else:
            color = self.arrow_color

        pen = QPen(color, 1.8, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Зона стрілки — праві 32px
        rx = self.width() - 32
        cx = rx + 16
        cy = self.height() // 2
        w, h = 6, 4

        painter.drawLine(QPoint(cx - w, cy - h // 2), QPoint(cx, cy + h // 2))
        painter.drawLine(QPoint(cx, cy + h // 2), QPoint(cx + w, cy - h // 2))
        painter.end()



class BaseArmWindow(QWidget):
    """
    Базовий клас АРМ-вікна.
    ВАЖЛИВО: Замість QComboBox використовуйте StyledComboBox —
    тільки він малює сучасну chevron-стрілку.
    Приклад: cb = StyledComboBox(parent)
    """
    def __init__(self, title):
        super().__init__()
        self.title_text = title
        self.is_dark_theme = True
        self.menu_buttons = []
        self.active_button = None
        self.help_window = None
        self.init_base_ui()

    def init_base_ui(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, "icon.png")
        self.setWindowTitle(self.title_text)
        self.setWindowIcon(QIcon(icon_path))
        self.resize(1100, 700)
        self.setStyleSheet("font-family: 'Segoe UI', sans-serif;")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setMaximumWidth(230)
        self.sidebar.setMinimumWidth(230)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(10, 20, 10, 20)
        self.sidebar_layout.setSpacing(5)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.top_bar = QFrame()
        self.top_bar.setFixedHeight(60)
        top_bar_layout = QHBoxLayout(self.top_bar)
        top_bar_layout.setContentsMargins(15, 0, 20, 0)

        self.hamburger_btn = QPushButton("☰")
        self.hamburger_btn.setFixedSize(45, 45)
        self.hamburger_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hamburger_btn.clicked.connect(self.toggle_sidebar)

        self.title_label = QLabel(self.title_text)

        top_bar_layout.addWidget(self.hamburger_btn)
        top_bar_layout.addSpacing(10)
        top_bar_layout.addWidget(self.title_label)
        top_bar_layout.addStretch()

        self.stacked_widget = QStackedWidget()

        content_layout.addWidget(self.top_bar)
        content_layout.addWidget(self.stacked_widget)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(content_widget)

    def add_menu_item(self, text, page_widget):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_buttons.append(btn)

        index = self.stacked_widget.count()
        self.stacked_widget.addWidget(page_widget)

        btn.clicked.connect(lambda checked=False, idx=index, b=btn: self.on_menu_click(idx, b))
        self.sidebar_layout.addWidget(btn)

        if index == 0:
            self.active_button = btn

    def on_menu_click(self, index, btn):
        self.stacked_widget.setCurrentIndex(index)
        self.active_button = btn
        self.apply_theme()

    def finalize_menu(self):
        self.sidebar_layout.addStretch()

        for btn in self.menu_buttons:
            if "Довідка" in btn.text():
                btn.hide()

        self.btn_help = QPushButton("❓ Довідка")
        self.btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_help.clicked.connect(self.show_help_window)
        self.sidebar_layout.addWidget(self.btn_help)

        self.theme_btn = QPushButton("🌞 Світла тема")
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.clicked.connect(self.animate_theme_toggle)
        self.sidebar_layout.addWidget(self.theme_btn)

        self.btn_logout = QPushButton("Вихід")
        self.btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_logout.clicked.connect(self.perform_logout)
        self.sidebar_layout.addWidget(self.btn_logout)

        self.apply_theme()

    # ==========================================
    # ВІДКРИТТЯ ВІКНА ДОВІДКИ (ГАРАНТОВАНИЙ ЗАХИСТ ВІД 0xC0000409)
    # ==========================================
    def show_help_window(self):
        from help import HelpWindow

        try:
            if self.help_window is not None:
                self.help_window.windowTitle()
        except RuntimeError:
            self.help_window = None

        if self.help_window is None:
            self.help_window = HelpWindow(self.get_help_data(), f"Довідка: {self.title_text}", self.is_dark_theme)

        self.help_window.is_dark_theme = self.is_dark_theme
        self.help_window.apply_theme()
        self.help_window.show()
        self.help_window.raise_()
        self.help_window.activateWindow()

    def get_help_data(self):
        if "Адміністратора" in self.title_text:
            return {
                "Вступ": "<h1 style='color: #8B5CF6;'>АРМ Адміністратора</h1><p>Цей модуль призначений для технічного обслуговування системи.</p>",
                "Технічне управління": {
                    "🖥️ Моніторинг": "<h2 style='color: #8B5CF6;'>Моніторинг стану</h2><p>Дозволяє перевіряти активність БД та робити бекап.</p>",
                    "⚙️ Настройки": "<h2 style='color: #8B5CF6;'>Настройки системи</h2><p>Глобальні параметри програми.</p>"
                },
                "Управління даними": {
                    "👥 Користувачі": "<h2 style='color: #8B5CF6;'>Управління користувачами</h2><p>Реєстрація нових працівників підприємства.</p>",
                    "📚 Довідники": "<h2 style='color: #8B5CF6;'>Ведення довідників</h2><p>Оновлюйте ціни на матеріали та типи робіт.</p>"
                }
            }
        elif "Керівника" in self.title_text:
            return {
                "Вступ": "<h1 style='color: #8B5CF6;'>АРМ Керівника</h1><p>Модуль для аналітики та прийняття управлінських рішень.</p>",
                "Аналітика": {
                    "📈 Ефективність": "<h2 style='color: #8B5CF6;'>Ефективність роботи</h2><p>Графік та таблиці оновлюються автоматично.</p>",
                    "🗺️ Карта": "<h2 style='color: #8B5CF6;'>Візуалізація ділянок</h2><p>Карта Києва, що відображає найбільш критичні зони.</p>"
                },
                "Фінанси": {
                    "💰 Бюджет": "<h2 style='color: #8B5CF6;'>Контроль бюджету</h2><p>Підбивається загальна сума витрат матеріалів.</p>"
                }
            }
        elif "Працівника" in self.title_text:
            return {
                "Вступ": "<h1 style='color: #8B5CF6;'>АРМ Працівника</h1><p>Модуль для управління зверненнями та обліку матеріалів.</p>",
                "Робота з заявками": {
                    "📌 Прийом заявок": "<h2 style='color: #8B5CF6;'>Прийом заявок</h2><p>Відображає список активних звернень.</p>",
                    "📝 Реєстрація": "<h2 style='color: #8B5CF6;'>Реєстрація звернень</h2><p>Адреса підтягується автоматично за номером рахунку.</p>"
                },
                "Виконання": {
                    "🔧 Роботи": "<h2 style='color: #8B5CF6;'>Виконання робіт</h2><p>Списання матеріалів та підрахунок вартості.</p>",
                    "🗺️ Карта": "<h2 style='color: #8B5CF6;'>Карта</h2><p>Візуально оцінюйте місцезнаходження аварії.</p>"
                }
            }
        else:
            return {"Довідка": "<p>Універсальна довідка</p>"}

    # ==========================================
    # СИСТЕМА ФІЛЬТРАЦІЇ ДЛЯ ТАБЛИЦЬ
    # ==========================================
    def create_table_filters(self, table):
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 5)
        filter_layout.setSpacing(8)

        inputs = []
        for col in range(table.columnCount()):
            header_item = table.horizontalHeaderItem(col)
            header_text = header_item.text() if header_item else f"Колонка {col + 1}"
            header_text = header_text.replace('\n', ' ')

            le = QLineEdit()
            le.setPlaceholderText(f"🔍 {header_text}")
            le.setProperty("is_filter", "true")
            filter_layout.addWidget(le)
            inputs.append((col, le))
            le.textChanged.connect(lambda text, t=table, ins=inputs: self.filter_table(t, ins))

        return filter_widget

    def filter_table(self, table, inputs):
        for row in range(table.rowCount()):
            match = True
            for col, le in inputs:
                filter_text = le.text().lower().strip()
                if filter_text:
                    item = table.item(row, col)
                    item_text = item.text().lower() if item else ""
                    if filter_text not in item_text:
                        match = False
                        break
            table.setRowHidden(row, not match)

    def add_table_row(self, table, row_data):
        row_idx = table.rowCount()
        table.insertRow(row_idx)
        for col_idx, data in enumerate(row_data):
            table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))

    def create_action_button(self, text, primary=False, danger=False):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if primary:
            btn.setProperty("btn_type", "primary")
        elif danger:
            btn.setProperty("btn_type", "danger")
        else:
            btn.setProperty("btn_type", "standard")
        return btn

    def create_line_edit(self, placeholder=""):
        le = QLineEdit()
        le.setPlaceholderText(placeholder)
        return le

    def perform_logout(self):
        from login_window import LoginWindow
        self.login_window = LoginWindow()
        self.login_window.show()

        try:
            if self.help_window is not None:
                self.help_window.close()
        except RuntimeError:
            pass

        self.close()

    def toggle_sidebar(self):
        width = self.sidebar.width()
        new_width = 0 if width == 230 else 230

        self.anim_group = QParallelAnimationGroup()
        self.anim_max = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self.anim_max.setDuration(500)
        self.anim_max.setStartValue(width)
        self.anim_max.setEndValue(new_width)
        self.anim_max.setEasingCurve(QEasingCurve.Type.InOutQuart)

        self.anim_min = QPropertyAnimation(self.sidebar, b"minimumWidth")
        self.anim_min.setDuration(500)
        self.anim_min.setStartValue(width)
        self.anim_min.setEndValue(new_width)
        self.anim_min.setEasingCurve(QEasingCurve.Type.InOutQuart)

        self.anim_group.addAnimation(self.anim_max)
        self.anim_group.addAnimation(self.anim_min)
        self.anim_group.start()

    def animate_theme_toggle(self):
        self.fade_out_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_anim.setDuration(200)
        self.fade_out_anim.setStartValue(1.0)
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.finished.connect(self.toggle_theme)
        self.fade_out_anim.start()

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        if self.is_dark_theme:
            self.theme_btn.setText("🌞 Світла тема")
        else:
            self.theme_btn.setText("🌙 Темна тема")

        self.apply_theme()

        try:
            if self.help_window is not None:
                self.help_window.is_dark_theme = self.is_dark_theme
                self.help_window.apply_theme()
        except RuntimeError:
            self.help_window = None

        self.fade_in_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_anim.setDuration(250)
        self.fade_in_anim.setStartValue(0.0)
        self.fade_in_anim.setEndValue(1.0)
        self.fade_in_anim.start()

    def apply_theme(self):
        if self.is_dark_theme:
            sidebar_bg = "#1E1E2E"
            top_bar_bg = "#282A36"
            content_bg = "#181825"
            text_color = "#F8F8F2"
            btn_color = "#CDD6F4"
            hover_bg = "#44475A"
            border_color = "#44475A"
            accent_color = "#8B5CF6"
            input_bg = "#313244"
            table_bg = "#1E1E2E"
            header_bg = "#282A36"
            header_text = "#8B5CF6"
            placeholder_color = "rgba(205, 214, 244, 100)"
            scroll_bg = "transparent"
            scroll_handle = "#44475A"
            scroll_hover = "#6272A4"
            arrow_color = "#CDD6F4"
        else:
            sidebar_bg = "#E9ECEF"
            top_bar_bg = "#FFFFFF"
            content_bg = "#F8F9FA"
            text_color = "#2C3E50"
            btn_color = "#495057"
            hover_bg = "#CED4DA"
            border_color = "#DEE2E6"
            accent_color = "#8B5CF6"
            input_bg = "#FFFFFF"
            table_bg = "#FFFFFF"
            header_bg = "#F8F9FA"
            header_text = "#2C3E50"
            placeholder_color = "rgba(44, 62, 80, 100)"
            scroll_bg = "transparent"
            scroll_handle = "#CED4DA"
            scroll_hover = "#ADB5BD"
            arrow_color = "#495057"

        self.sidebar.setStyleSheet(f"background-color: {sidebar_bg}; color: {text_color};")
        self.top_bar.setStyleSheet(f"background-color: {top_bar_bg}; border-bottom: 1px solid {border_color};")
        self.stacked_widget.setStyleSheet(f"background-color: {content_bg};")
        self.title_label.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {text_color}; border: none;")

        self.hamburger_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {accent_color}; font-size: 24px; border: none; border-radius: 8px; }} 
            QPushButton:hover {{ background-color: {hover_bg}; }}
        """)

        for btn in self.menu_buttons:
            if btn == self.active_button:
                btn.setStyleSheet(f"""
                    QPushButton {{ background-color: {hover_bg}; color: {accent_color}; text-align: left; padding: 12px 15px; border: none; border-left: 4px solid {accent_color}; font-size: 14px; font-weight: bold; border-top-right-radius: 6px; border-bottom-right-radius: 6px; }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{ background-color: transparent; color: {btn_color}; text-align: left; padding: 12px 15px; border: none; font-size: 14px; font-weight: 500; border-radius: 6px; }} 
                    QPushButton:hover {{ background-color: {hover_bg}; color: {text_color}; }}
                """)

        btn_bottom_style = f"QPushButton {{ background-color: transparent; color: {btn_color}; text-align: left; padding: 12px 15px; border: none; font-size: 14px; font-weight: 500; border-radius: 6px; }} QPushButton:hover {{ background-color: {hover_bg}; color: {text_color}; }}"

        if hasattr(self, 'btn_help'):
            self.btn_help.setStyleSheet(btn_bottom_style)
        if hasattr(self, 'theme_btn'):
            self.theme_btn.setStyleSheet(btn_bottom_style)
        if hasattr(self, 'btn_logout'):
            self.btn_logout.setStyleSheet(
                "QPushButton { background-color: transparent; color: #FF5555; text-align: left; padding: 12px 15px; border: none; font-size: 14px; font-weight: bold; border-radius: 6px; } QPushButton:hover { background-color: rgba(255, 85, 85, 0.15); }")

        for btn in self.findChildren(QPushButton):
            btn_type = btn.property("btn_type")
            if btn_type == "primary":
                btn.setStyleSheet(
                    f"background-color: {accent_color}; color: #FFFFFF; font-weight: bold; padding: 8px 15px; border-radius: 5px; border: none;")
            elif btn_type == "danger":
                btn.setStyleSheet(
                    f"background-color: #FF5555; color: #FFFFFF; font-weight: bold; padding: 8px 15px; border-radius: 5px; border: none;")
            elif btn_type == "standard":
                btn.setStyleSheet(
                    f"background-color: {hover_bg}; color: {text_color}; font-weight: bold; padding: 8px 15px; border-radius: 5px; border: none;")

        table_style = f"""
            QTableWidget {{ background-color: {table_bg}; color: {text_color}; gridline-color: {border_color}; border: 1px solid {border_color}; border-radius: 6px; }}
            QHeaderView::section {{ background-color: {header_bg}; color: {header_text}; padding: 5px; font-weight: bold; border: 1px solid {border_color}; }}
        """
        for tbl in self.findChildren(QTableWidget):
            tbl.setStyleSheet(table_style)

        tab_style = f"""
            QTabWidget::pane {{ border: 1px solid {border_color}; background-color: {content_bg}; border-radius: 4px; }}
            QTabBar::tab {{ background: {sidebar_bg}; color: {text_color}; padding: 8px 16px; border: 1px solid {border_color}; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }}
            QTabBar::tab:selected {{ background: {content_bg}; color: {accent_color}; font-weight: bold; border-bottom: 3px solid {accent_color}; }}
            QTabBar::tab:hover {{ background: {hover_bg}; }}
        """
        for tab in self.findChildren(QTabWidget):
            tab.setStyleSheet(tab_style)

        # СТИЛІ ДЛЯ ПОЛІВ ВВОДУ, COMBOBOX (з сучасною SVG-стрілочкою) І TEXTEDIT
        input_style = f"""
            QLineEdit, QTextEdit {{ 
                background-color: {input_bg}; 
                color: {text_color}; 
                border: 1px solid {border_color}; 
                border-radius: 6px; 
                padding: 6px 10px; 
                font-size: 14px; 
            }}
            QLineEdit:focus, QTextEdit:focus {{ 
                border: 1px solid {accent_color}; 
            }}
            QLineEdit::placeholder {{ 
                color: {placeholder_color}; 
            }}

            QLineEdit[is_filter="true"] {{
                background-color: {input_bg};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                color: {text_color};
            }}
            QLineEdit[is_filter="true"]:focus {{
                border: 1px solid {accent_color};
            }}

            /* ── СУЧАСНИЙ COMBOBOX ── */
            QComboBox {{
                background-color: {input_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 6px 36px 6px 10px;
                font-size: 14px;
            }}
            QComboBox:focus {{
                border: 1px solid {accent_color};
            }}
            QComboBox:hover {{
                border: 1px solid {accent_color};
            }}
            /* Зона стрілки — прозора, стрілку малює QProxyStyle */
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 32px;
                border: none;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                background: transparent;
            }}
            /* Прибираємо стандартну стрілку Qt повністю */
            QComboBox::down-arrow {{
                width: 0px;
                height: 0px;
                image: none;
            }}

            /* Список елементів */
            QComboBox QAbstractItemView {{ 
                background-color: {input_bg}; 
                color: {text_color}; 
                selection-background-color: {accent_color}; 
                selection-color: #FFFFFF;
                border-radius: 6px;
                border: 1px solid {border_color};
                outline: none;
                padding: 4px;
            }}
            QComboBox QAbstractItemView::item {{
                min-height: 28px;
                border-radius: 4px;
                color: {text_color};
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: {hover_bg};
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {accent_color};
                color: #FFFFFF;
            }}
        """
        for w in self.findChildren(QLineEdit) + self.findChildren(QTextEdit):
            w.setStyleSheet(input_style)

        # Застосовуємо CSS + оновлюємо кольори стрілки для StyledComboBox
        StyledComboBox.arrow_color = QColor(arrow_color)
        combo_style_str = input_style
        for cb in self.findChildren(QComboBox):
            cb.setStyleSheet(combo_style_str)
            cb.update()  # перемалювати chevron одразу

        for gb in self.findChildren(QGroupBox):
            gb.setStyleSheet(
                f"QGroupBox {{ color: {text_color}; font-weight: bold; border: 1px solid {border_color}; border-radius: 8px; margin-top: 15px; padding-top: 20px; }} QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; left: 10px; }}")

        for frame in self.findChildren(QFrame):
            if frame.objectName() == "stat_card":
                color = frame.property("accent_color")
                bg = "#282A36" if self.is_dark_theme else "#FFFFFF"
                border = "none" if self.is_dark_theme else f"1px solid {border_color}"
                frame.setStyleSheet(
                    f"background-color: {bg}; border-radius: 10px; border-top: 4px solid {color}; border-left: {border}; border-right: {border}; border-bottom: {border};")

        for lbl in self.findChildren(QLabel):
            if lbl.objectName() == "stat_title":
                lbl.setStyleSheet(
                    f"color: {'#A6ADC8' if self.is_dark_theme else '#6C757D'}; font-weight: bold; font-size: 14px; border: none;")
            elif lbl.objectName() == "stat_value":
                color = lbl.property("accent_color")
                lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 32px; border: none;")

        self.setStyleSheet(f"""
            QLabel {{ color: {text_color}; }} 
            QScrollArea {{ background: transparent; border: none; }}

            /* СУЧАСНІ СКРОЛБАРИ */
            QScrollBar:vertical {{
                border: none; background: {scroll_bg}; width: 10px; border-radius: 5px; margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {scroll_handle}; min-height: 30px; border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {scroll_hover}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none; background: none; height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

            QScrollBar:horizontal {{
                border: none; background: {scroll_bg}; height: 10px; border-radius: 5px; margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: {scroll_handle}; min-width: 30px; border-radius: 5px;
            }}
            QScrollBar::handle:horizontal:hover {{ background: {scroll_hover}; }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                border: none; background: none; width: 0px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: none; }}
            QAbstractScrollArea::corner {{ background: transparent; }}
        """)