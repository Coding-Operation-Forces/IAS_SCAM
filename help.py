from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QSplitter,
                             QTreeWidget, QTreeWidgetItem, QTextBrowser)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon


class HelpWindow(QWidget):
    def __init__(self, help_data, title="Довідка", is_dark_theme=True):
        super().__init__()
        self.help_data = help_data
        self.is_dark_theme = is_dark_theme

        self.text_color = "#F8F8F2" if is_dark_theme else "#2C3E50"

        self.setWindowTitle(title)
        self.setWindowIcon(QIcon("icon.png"))
        self.resize(850, 600)

        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowFlag(Qt.WindowType.Window)

        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.populate_tree(self.help_data, self.tree)
        self.tree.expandAll()
        self.tree.itemClicked.connect(self.on_item_clicked)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)

        splitter.addWidget(self.tree)
        splitter.addWidget(self.browser)

        splitter.setSizes([250, 600])

        layout.addWidget(splitter)

        if self.tree.topLevelItemCount() > 0:
            first_item = self.tree.topLevelItem(0)
            self.tree.setCurrentItem(first_item)
            self.on_item_clicked(first_item, 0)

    def populate_tree(self, data, parent):
        if not isinstance(data, dict):
            item = QTreeWidgetItem(["Загальна інформація"])
            item.setData(0, Qt.ItemDataRole.UserRole, str(data))
            if isinstance(parent, QTreeWidget):
                parent.addTopLevelItem(item)
            else:
                parent.addChild(item)
            return

        for key, value in data.items():
            item = QTreeWidgetItem([str(key)])
            if isinstance(value, dict):
                self.populate_tree(value, item)
                item.setData(0, Qt.ItemDataRole.UserRole, "")
            else:
                item.setData(0, Qt.ItemDataRole.UserRole, str(value))

            if isinstance(parent, QTreeWidget):
                parent.addTopLevelItem(item)
            else:
                parent.addChild(item)

    def on_item_clicked(self, item, column):
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
                <h2 style="color: #8B5CF6;">{item.text(0)}</h2>
                <p>👈 Розгорніть цей розділ та оберіть підпункт у меню ліворуч для перегляду інформації.</p>
            </div>
            """
            self.browser.setHtml(empty_html)

    def apply_theme(self):
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

            /* СУЧАСНІ СКРОЛБАРИ ТУТ ТАКОЖ */
            QScrollBar:vertical {{
                border: none;
                background: {scroll_bg};
                width: 10px;
                border-radius: 5px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {scroll_handle};
                min-height: 30px;
                border-radius: 5px;
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
                border: none;
                background: {scroll_bg};
                height: 10px;
                border-radius: 5px;
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: {scroll_handle};
                min-width: 30px;
                border-radius: 5px;
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