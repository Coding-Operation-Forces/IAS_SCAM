import os
from PyQt6.QtWidgets import (QHBoxLayout, QWidget, QVBoxLayout,
                             QTreeWidget, QTreeWidgetItem, QTextBrowser, QPushButton)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon


class HelpWindow(QWidget):
    """Спеціалізоване вікно відображення документації та інструкцій користувача."""
    
    def __init__(self, help_data, title="Довідка", is_dark_theme=True):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, "icon.png")
        super().__init__()
        self.help_data = help_data
        self.is_dark_theme = is_dark_theme
        self.text_color = "#F8F8F2" if is_dark_theme else "#2C3E50"

        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(icon_path))
        self.resize(850, 600)

        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowFlag(Qt.WindowType.Window)

        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        """Ініціалізує фіксований контейнер для меню та браузера тексту."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        h_layout = QHBoxLayout()
        h_layout.setSpacing(15)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setFixedWidth(270)
        
        self.tree.setRootIsDecorated(True)
        self.tree.setItemsExpandable(True) 
        self.tree.setIndentation(15) 
        
        self.populate_tree(self.help_data, self.tree)
        self.tree.expandAll()
        self.tree.itemClicked.connect(self.on_item_clicked)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)

        h_layout.addWidget(self.tree)
        h_layout.addWidget(self.browser)
        layout.addLayout(h_layout)

        self.btn_open_pdf = QPushButton("📖 Детальна інструкція (PDF)")
        self.btn_open_pdf.setFixedHeight(40)
        self.btn_open_pdf.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_pdf.clicked.connect(self.open_detailed_help_pdf)
        layout.addWidget(self.btn_open_pdf)

        if self.tree.topLevelItemCount() > 0:
            first_item = self.tree.topLevelItem(0)
            self.tree.setCurrentItem(first_item)
            self.on_item_clicked(first_item, 0)

    def populate_tree(self, data, parent):
        """Рекурсивно наповнює QTreeWidget ієрархічною структурою словника довідки."""
        if not isinstance(data, dict):
            item = QTreeWidgetItem(["Загальна інформація"])
            item.setData(0, Qt.ItemDataRole.UserRole, str(data))
            if isinstance(parent, QTreeWidget):
                parent.addTopLevelItem(item)
            else:
                parent.addChild(item)
            return

        for key, value in data.items():
            is_node = isinstance(value, dict)
            icon_str = "📂 " if is_node else "📄 "
            
            item = QTreeWidgetItem([f"{icon_str}{key}"])
            if is_node:
                item.setData(0, Qt.ItemDataRole.UserRole, "")
                self.populate_tree(value, item)
            else:
                item.setData(0, Qt.ItemDataRole.UserRole, str(value))

            if isinstance(parent, QTreeWidget):
                parent.addTopLevelItem(item)
            else:
                parent.addChild(item)

    def on_item_clicked(self, item, column):
        """Рендерить html-контент вибраного інструкційного розділу в браузер."""
        content = item.data(0, Qt.ItemDataRole.UserRole)

        if content:
            formatted_html = f"""
            <div style="font-family: 'Segoe UI', sans-serif; font-size: 15px; line-height: 1.6; color: {self.text_color};">
                {content}
            </div>
            """
            self.browser.setHtml(formatted_html)
        else:
            empty_html = f"""
            <div style="font-family: 'Segoe UI', sans-serif; font-size: 15px; line-height: 1.6; color: {self.text_color};">
                <h2 style="color: #8B5CF6;">{item.text(0).strip()[2:]}</h2>
                <p>👈 Розгорніть цей розділ та оберіть підпункт у меню ліворуч для перегляду інформації.</p>
            </div>
            """
            self.browser.setHtml(empty_html)

    def open_detailed_help_pdf(self):
        """Знаходить та відкриває PDF-інструкцію користувача у програмі за замовчуванням."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        pdf_path = os.path.abspath(os.path.join(base_dir, "Інструкція для користувачів.pdf"))

        if not os.path.exists(pdf_path):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Помилка", f"Файл інструкції не знайдено за шляхом:\n{pdf_path}")
            return
            
        try:
            os.startfile(pdf_path)
        except Exception as ex:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Помилка", f"Не вдалося відкрити файл інструкції: {ex}")

    def apply_theme(self):
        """Стилізує віджети вікна довідки відповідно до обраної глобальної теми."""
        if self.is_dark_theme:
            bg_color = "#1E1E2E"
            tree_bg = "#282A36"
            content_bg = "#181825"
            self.text_color = "#F8F8F2"
            border_color = "#44475A"
            accent_color = "#8B5CF6"
            hover_bg = "#44475A"
            scroll_bg = "transparent"
            scroll_handle = "#44475A"
            scroll_hover = "#6272A4"
            btn_hover_color = "#7C3AED"
        else:
            bg_color = "#F8F9FA"
            tree_bg = "#FFFFFF"
            content_bg = "#FFFFFF"
            self.text_color = "#2C3E50"
            border_color = "#DEE2E6"
            accent_color = "#8B5CF6"
            hover_bg = "#E9ECEF"
            scroll_bg = "transparent"
            scroll_handle = "#CED4DA"
            scroll_hover = "#ADB5BD"
            btn_hover_color = "#7C3AED"

        self.setStyleSheet(f"""
            QWidget {{ background-color: {bg_color}; color: {self.text_color}; }}

            QTreeWidget {{
                background-color: {tree_bg};
                color: {self.text_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                font-size: 14px;
                padding: 5px;
            }}
            QTreeWidget::item {{
                padding: 5px;
                border-radius: 4px;
            }}
            QTreeWidget::item:hover {{
                background-color: {hover_bg};
            }}
            QTreeWidget::item:selected {{
                background-color: {accent_color};
                color: #FFFFFF;
                font-weight: bold;
            }}

            QTextBrowser {{
                background-color: {content_bg};
                color: {self.text_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 15px;
            }}

            QPushButton {{
                background-color: {accent_color};
                color: #FFFFFF;
                font-weight: bold;
                font-size: 14px;
                border-radius: 6px;
                border: none;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {btn_hover_color};
            }}

            QScrollBar:vertical {{
                border: none; background: {scroll_bg}; width: 10px; border-radius: 5px; margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {scroll_handle}; min-height: 30px; border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {scroll_hover};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none; background: none; height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}

            QScrollBar:horizontal {{
                border: none; background: {scroll_bg}; height: 10px; border-radius: 5px; margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: {scroll_handle}; min-width: 30px; border-radius: 5px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {scroll_hover};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                border: none; background: none; width: 0px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
            QAbstractScrollArea::corner {{
                background: transparent;
            }}
        """)

        current_item = self.tree.currentItem()
        if current_item:
            self.on_item_clicked(current_item, 0)