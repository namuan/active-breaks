import sys

from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPainter, QColor, QBrush
from PyQt6.QtWidgets import QWidget, QApplication


class DrinkingGlassWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('2D Drinking Glass with Water Levels')
        self.setGeometry(0, 0, 200, 200)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Define the glass body dimensions
        glass_top_width = 140
        glass_bottom_width = 100
        glass_height = 150
        glass_top_y = 10

        # Define the points for the glass (trapezoidal shape)
        top_left = QPointF((self.width() - glass_top_width) / 2, glass_top_y)
        top_right = QPointF((self.width() + glass_top_width) / 2, glass_top_y)
        bottom_left = QPointF((self.width() - glass_bottom_width) / 2, glass_top_y + glass_height)
        bottom_right = QPointF((self.width() + glass_bottom_width) / 2, glass_top_y + glass_height)

        # Set the pen and brush for the glass outline
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Draw the glass body (trapezoid)
        painter.drawPolygon([top_left, top_right, bottom_right, bottom_left])

        # Draw water levels (5 levels)
        num_levels = 5
        level_height = glass_height / num_levels  # Height per water level
        water_color = QColor(0, 128, 255, 200)  # Solid blue for water

        for i in range(num_levels):
            # Calculate the top and bottom Y positions of each water level
            top_level_y = glass_top_y + i * level_height
            bottom_level_y = top_level_y + level_height - 5  # Add small space between levels

            # Calculate the width of the water level at the top and bottom
            current_top_width = glass_top_width - (i * (glass_top_width - glass_bottom_width) / num_levels)
            current_bottom_width = glass_top_width - ((i + 1) * (glass_top_width - glass_bottom_width) / num_levels)

            # Define the 4 points of the trapezoidal water level
            top_left_level = QPointF((self.width() - current_top_width) / 2, top_level_y)
            top_right_level = QPointF((self.width() + current_top_width) / 2, top_level_y)
            bottom_left_level = QPointF((self.width() - current_bottom_width) / 2, bottom_level_y)
            bottom_right_level = QPointF((self.width() + current_bottom_width) / 2, bottom_level_y)

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
