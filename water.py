import sys

from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPainter, QColor, QBrush
from PyQt6.QtWidgets import QWidget, QApplication, QPushButton, QVBoxLayout

class DrinkingGlassWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('2D Drinking Glass with Water Levels')
        self.setGeometry(0, 0, 200, 240)  # Increased height to accommodate the button

        # Initialize the current water level (0 initially)
        self.current_level = 0
        self.max_levels = 5  # Maximum number of water levels

        # Create the main layout
        layout = QVBoxLayout()

        # Create a container widget for the glass drawing
        self.glass_widget = QWidget()
        self.glass_widget.setFixedSize(200, 200)
        self.glass_widget.paintEvent = self.paintEvent

        # Create the + button
        self.plus_button = QPushButton("+")
        self.plus_button.setFixedSize(40, 40)  # Set a fixed size for the button
        self.plus_button.clicked.connect(self.increase_level)  # Connect button click to the increase_level method

        # Add widgets to the layout
        layout.addWidget(self.glass_widget)
        layout.addWidget(self.plus_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Set the layout for the main widget
        self.setLayout(layout)

    def increase_level(self):
        # Increase the current water level, but do not exceed the maximum number of levels
        if self.current_level < self.max_levels:
            self.current_level += 1
            self.glass_widget.update()  # Trigger a repaint of the glass widget

    def paintEvent(self, event):
        painter = QPainter(self.glass_widget)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Define the glass body dimensions
        glass_top_width = 140
        glass_bottom_width = 100
        glass_height = 150
        glass_bottom_y = 10 + glass_height  # Bottom of the glass

        # Define the points for the glass (trapezoidal shape)
        top_left = QPointF((self.glass_widget.width() - glass_top_width) / 2, glass_bottom_y - glass_height)
        top_right = QPointF((self.glass_widget.width() + glass_top_width) / 2, glass_bottom_y - glass_height)
        bottom_left = QPointF((self.glass_widget.width() - glass_bottom_width) / 2, glass_bottom_y)
        bottom_right = QPointF((self.glass_widget.width() + glass_bottom_width) / 2, glass_bottom_y)

        # Set the pen and brush for the glass outline
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Draw the glass body (trapezoid)
        painter.drawPolygon([top_left, top_right, bottom_right, bottom_left])

        # Draw water levels from the bottom up based on the current counter
        level_height = glass_height / self.max_levels  # Height per water level
        water_color = QColor(0, 128, 255, 200)  # Solid blue for water

        # Draw water for the current number of levels from the bottom upwards
        for i in range(self.current_level):
            # Calculate the bottom and top Y positions of each water level (starting from the bottom)
            bottom_level_y = glass_bottom_y - i * level_height
            top_level_y = bottom_level_y - level_height + 5  # Add small space between levels

            # Calculate the width of the water level at the top and bottom
            current_bottom_width = glass_bottom_width + (i * (glass_top_width - glass_bottom_width) / self.max_levels)
            current_top_width = glass_bottom_width + ((i + 1) * (glass_top_width - glass_bottom_width) / self.max_levels)

            # Define the 4 points of the trapezoidal water level
            bottom_left_level = QPointF((self.glass_widget.width() - current_bottom_width) / 2, bottom_level_y)
            bottom_right_level = QPointF((self.glass_widget.width() + current_bottom_width) / 2, bottom_level_y)
            top_left_level = QPointF((self.glass_widget.width() - current_top_width) / 2, top_level_y)
            top_right_level = QPointF((self.glass_widget.width() + current_top_width) / 2, top_level_y)

            # Set solid blue color for water
            painter.setBrush(QBrush(water_color))
            painter.setPen(Qt.PenStyle.NoPen)  # No outline for water levels

            # Draw the water level as a trapezoid
            painter.drawPolygon([top_left_level, top_right_level, bottom_right_level, bottom_left_level])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DrinkingGlassWidget()
    window.show()
    sys.exit(app.exec())