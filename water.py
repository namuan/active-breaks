import sys

from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPainter, QColor, QBrush
from PyQt6.QtWidgets import QWidget, QApplication, QPushButton, QVBoxLayout, QHBoxLayout

class GlassWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_level = 0
        self.max_levels = 5
        self.setFixedSize(200, 200)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        glass_top_width = 140
        glass_bottom_width = 100
        glass_height = 150
        glass_bottom_y = 10 + glass_height

        top_left = QPointF((self.width() - glass_top_width) / 2, glass_bottom_y - glass_height)
        top_right = QPointF((self.width() + glass_top_width) / 2, glass_bottom_y - glass_height)
        bottom_left = QPointF((self.width() - glass_bottom_width) / 2, glass_bottom_y)
        bottom_right = QPointF((self.width() + glass_bottom_width) / 2, glass_bottom_y)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        painter.drawPolygon([top_left, top_right, bottom_right, bottom_left])

        level_height = glass_height / self.max_levels
        water_color = QColor(0, 128, 255, 200)

        for i in range(self.current_level):
            bottom_level_y = glass_bottom_y - i * level_height
            top_level_y = bottom_level_y - level_height + 5

            current_bottom_width = glass_bottom_width + (i * (glass_top_width - glass_bottom_width) / self.max_levels)
            current_top_width = glass_bottom_width + ((i + 1) * (glass_top_width - glass_bottom_width) / self.max_levels)

            bottom_left_level = QPointF((self.width() - current_bottom_width) / 2, bottom_level_y)
            bottom_right_level = QPointF((self.width() + current_bottom_width) / 2, bottom_level_y)
            top_left_level = QPointF((self.width() - current_top_width) / 2, top_level_y)
            top_right_level = QPointF((self.width() + current_top_width) / 2, top_level_y)

            painter.setBrush(QBrush(water_color))
            painter.setPen(Qt.PenStyle.NoPen)

            painter.drawPolygon([top_left_level, top_right_level, bottom_right_level, bottom_left_level])

class DrinkingGlassWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('2D Drinking Glass with Water Levels')
        self.setGeometry(0, 0, 200, 240)
        self.setContentsMargins(0, 0, 0, 0)

        layout = QVBoxLayout()

        self.glass_widget = GlassWidget()

        button_layout = QHBoxLayout()

        common_button_style = """
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #c0c0c0;
                border-radius: 5px;
                padding: 5px;
                color: black;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """

        self.plus_button = QPushButton("+")
        self.plus_button.setFixedSize(40, 40)
        self.plus_button.clicked.connect(self.increase_level)
        self.plus_button.setStyleSheet(common_button_style + """
            QPushButton {
                font-size: 14px;
            }
        """)

        self.reset_button = QPushButton("Reset")
        self.reset_button.setFixedSize(60, 40)
        self.reset_button.clicked.connect(self.reset_level)
        self.reset_button.setStyleSheet(common_button_style + """
            QPushButton {
                font-size: 10px;
            }
        """)

        button_layout.addWidget(self.plus_button)
        button_layout.addWidget(self.reset_button)

        layout.addWidget(self.glass_widget)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def increase_level(self):
        if self.glass_widget.current_level < self.glass_widget.max_levels:
            self.glass_widget.current_level += 1
            self.glass_widget.update()

    def reset_level(self):
        self.glass_widget.current_level = 0
        self.glass_widget.update()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DrinkingGlassWidget()
    window.show()
    sys.exit(app.exec())