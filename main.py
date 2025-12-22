import logging
import os
import random
import sys
from enum import Enum
from pathlib import Path

from PyQt6.QtCore import pyqtProperty
from PyQt6.QtCore import QEasingCurve
from PyQt6.QtCore import QPointF
from PyQt6.QtCore import QPropertyAnimation
from PyQt6.QtCore import QRectF
from PyQt6.QtCore import QSettings
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QBrush
from PyQt6.QtGui import QColor
from PyQt6.QtGui import QIcon
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtGui import QPainter
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QDialog
from PyQt6.QtWidgets import QHBoxLayout
from PyQt6.QtWidgets import QLabel
from PyQt6.QtWidgets import QMenu
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtWidgets import QSizePolicy
from PyQt6.QtWidgets import QSpinBox
from PyQt6.QtWidgets import QSystemTrayIcon
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtWidgets import QWidget


def get_resource_path(relative_path):
    """Get the path to a resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# Set up logging
log_dir = Path.home() / ".logs" / "active_breaks"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "active_breaks.log"

logging.basicConfig(
    filename=str(log_file),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class SettingsDialog(QDialog):
    """Dialog to configure work and break durations."""

    def __init__(
        self,
        work_duration: int,
        break_duration: int,
        hold_duration: int,
        breath_duration: int,
        parent=None,
    ):
        super().__init__(parent)
        logging.debug("Initializing SettingsDialog")
        self.setWindowTitle("Active Breaks")
        self.setModal(True)

        layout = QVBoxLayout()

        # Work duration settings
        work_layout = QHBoxLayout()
        work_label = QLabel("Work duration (minutes):")
        self.work_spinbox = QSpinBox()
        self.work_spinbox.setRange(1, 120)
        self.work_spinbox.setValue(work_duration // 60)
        work_layout.addWidget(work_label)
        work_layout.addWidget(self.work_spinbox)
        layout.addLayout(work_layout)

        # Break duration settings
        break_layout = QHBoxLayout()
        break_label = QLabel("Break duration (minutes):")
        self.break_spinbox = QSpinBox()
        self.break_spinbox.setRange(1, 60)
        self.break_spinbox.setValue(break_duration // 60)
        break_layout.addWidget(break_label)
        break_layout.addWidget(self.break_spinbox)
        layout.addLayout(break_layout)

        # Hold duration settings
        hold_layout = QHBoxLayout()
        hold_label = QLabel("Hold duration (seconds):")
        self.hold_spinbox = QSpinBox()
        self.hold_spinbox.setRange(1, 60)
        self.hold_spinbox.setValue(hold_duration // 1000)
        hold_layout.addWidget(hold_label)
        hold_layout.addWidget(self.hold_spinbox)
        layout.addLayout(hold_layout)

        # Breath duration settings
        breath_layout = QHBoxLayout()
        breath_label = QLabel("Breath duration (seconds):")
        self.breath_spinbox = QSpinBox()
        self.breath_spinbox.setRange(1, 60)
        self.breath_spinbox.setValue(breath_duration // 1000)
        breath_layout.addWidget(breath_label)
        breath_layout.addWidget(self.breath_spinbox)
        layout.addLayout(breath_layout)

        # Save and Cancel buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        logging.debug("SettingsDialog initialized")

    def get_settings(self) -> tuple[int, int, int, int]:
        """Retrieve the work, break, hold, and breath durations from the dialog."""
        work_duration = self.work_spinbox.value() * 60
        break_duration = self.break_spinbox.value() * 60
        hold_duration = self.hold_spinbox.value() * 1000
        breath_duration = self.breath_spinbox.value() * 1000
        logging.debug(
            f"Settings retrieved: Work duration: {work_duration}, Break duration: {break_duration}, Hold duration: {hold_duration}, Breath duration: {breath_duration}"
        )
        return work_duration, break_duration, hold_duration, breath_duration


class ImageSlideshow(QWidget):
    def __init__(self, image_paths, delay_ms=2000):
        super().__init__()

        self.image_paths = image_paths
        self.delay_ms = delay_ms
        self.current_index = 0

        self.layout = QVBoxLayout()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.image_label)
        self.setLayout(self.layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.show_next_image)
        self.timer.start(self.delay_ms)

        self.show_next_image()

    def show_next_image(self):
        if self.current_index >= len(self.image_paths):
            self.current_index = 0

        image_path = self.image_paths[self.current_index]
        pixmap = QPixmap(image_path)
        self.image_label.setPixmap(pixmap)
        self.current_index += 1

    def resizeEvent(self, event):
        super().resizeEvent(event)


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

        top_left = QPointF(
            (self.width() - glass_top_width) / 2, glass_bottom_y - glass_height
        )
        top_right = QPointF(
            (self.width() + glass_top_width) / 2, glass_bottom_y - glass_height
        )
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

            current_bottom_width = glass_bottom_width + (
                i * (glass_top_width - glass_bottom_width) / self.max_levels
            )
            current_top_width = glass_bottom_width + (
                (i + 1) * (glass_top_width - glass_bottom_width) / self.max_levels
            )

            bottom_left_level = QPointF(
                (self.width() - current_bottom_width) / 2, bottom_level_y
            )
            bottom_right_level = QPointF(
                (self.width() + current_bottom_width) / 2, bottom_level_y
            )
            top_left_level = QPointF(
                (self.width() - current_top_width) / 2, top_level_y
            )
            top_right_level = QPointF(
                (self.width() + current_top_width) / 2, top_level_y
            )

            painter.setBrush(QBrush(water_color))
            painter.setPen(Qt.PenStyle.NoPen)

            painter.drawPolygon(
                [top_left_level, top_right_level, bottom_right_level, bottom_left_level]
            )


class DrinkingGlassWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 10)
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
        self.plus_button.setStyleSheet(
            common_button_style
            + """
            QPushButton {
                font-size: 14px;
            }
        """
        )

        self.reset_button = QPushButton("Reset")
        self.reset_button.setFixedSize(60, 40)
        self.reset_button.clicked.connect(self.reset_level)
        self.reset_button.setStyleSheet(
            common_button_style
            + """
            QPushButton {
                font-size: 10px;
            }
        """
        )

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


class BreathState(Enum):
    INHALE = "Inhale"
    EXHALE = "Exhale"
    HOLD = "Hold"


class BreathingWidget(QWidget):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent)
        self._breathe_progress = 0

        # Default values
        self.min_size = kwargs.get("min_size", 10)
        self.max_size = kwargs.get("max_size", 200)
        self.hold_time = kwargs.get("hold_time", 5000)
        self.breath_time = kwargs.get("breath_time", 7000)
        self.circle_color = kwargs.get("circle_color", QColor(200, 200, 255))
        self.text_color = kwargs.get("text_color", QColor(0, 0, 0))

        self._dot_size = self.min_size
        self.state = BreathState.INHALE

        self.setMinimumSize(self.max_size, self.max_size)

        self.label = QLabel(self.state.value, alignment=Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(f"color: {self.text_color.name()}")

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.animation = QPropertyAnimation(self, b"dot_size")
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.setDuration(self.breath_time)
        self.animation.valueChanged.connect(self.update)
        self.animation.finished.connect(self.on_animation_finished)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background:transparent;")

        self.start_inhale()

    def start_inhale(self):
        self.state = BreathState.INHALE
        self.label.setText(self.state.value)
        self.animation.setStartValue(self.min_size)
        self.animation.setEndValue(self.max_size)
        self.animation.start()

    def start_exhale(self):
        self.state = BreathState.EXHALE
        self.label.setText(self.state.value)
        self.animation.setStartValue(self.max_size)
        self.animation.setEndValue(self.min_size)
        self.animation.start()

    def start(self):
        """Start the breathing animation."""
        self.animation.start()

    def stop(self):
        """Stop the breathing animation."""
        self.animation.stop()
        self.breathe_progress = 0
        self.update()

    def on_animation_finished(self):
        self.state = BreathState.HOLD
        self.label.setText(self.state.value)
        if self.state == BreathState.HOLD:
            if self._dot_size == self.max_size:
                QTimer.singleShot(self.hold_time, self.start_exhale)
            else:
                QTimer.singleShot(self.hold_time, self.start_inhale)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.circle_color)

        center = self.rect().center()
        center.setY(center.y())  # Move circle up to make room for text
        painter.drawEllipse(center, self._dot_size // 2, self._dot_size // 2)

    def get_dot_size(self):
        return self._dot_size

    def set_dot_size(self, size):
        if self._dot_size != size:
            self._dot_size = size
            self.update()

    @pyqtProperty(float)
    def breathe_progress(self):
        return self._breathe_progress

    @breathe_progress.setter
    def breathe_progress(self, value):
        self._breathe_progress = value
        self.update()  # Trigger a repaint when the progress changes

    dot_size = pyqtProperty(int, get_dot_size, set_dot_size)


class FullScreenBlocker(QWidget):
    """Full screen translucent blocker window that prevents interaction during breaks."""

    def __init__(self, parent=None):
        super().__init__(
            parent,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        logging.debug("Initializing FullScreenBlocker")
        
        # Make the window translucent
        self.setWindowOpacity(0.7)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 180);")
        
        # Set the window to cover the entire screen
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        # Block all keyboard and mouse events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        logging.debug("FullScreenBlocker initialized")

    def keyPressEvent(self, event: QKeyEvent):
        """Block all key presses."""
        event.ignore()
        logging.debug("FullScreenBlocker: Key press blocked")

    def mousePressEvent(self, event):
        """Block all mouse clicks."""
        event.ignore()
        logging.debug("FullScreenBlocker: Mouse press blocked")


class BreakActivityWindow(QWidget):
    def __init__(self, hold_duration: int, breath_duration: int, parent=None):
        super().__init__(
            parent,
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint,
        )
        logging.debug("Initializing BreakActivityWindow")
        self.setFixedWidth(200)
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #ff5555;
                color: white;
                border: none;
                padding: 2px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff0000;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Top bar with close button
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top_bar.addWidget(spacer)

        close_button = QPushButton("×")
        close_button.setFixedSize(20, 20)
        close_button.clicked.connect(self.hide)
        top_bar.addWidget(close_button)

        main_layout.addLayout(top_bar)

        # Activity label
        self.activity_label = QLabel()
        self.activity_label.setWordWrap(True)
        self.activity_label.setStyleSheet("font-size: 16px; padding: 10px")
        main_layout.addWidget(self.activity_label)

        # Add BreathingWidget
        self.breathing_widget = BreathingWidget(
            self, hold_time=hold_duration, breath_time=breath_duration
        )
        main_layout.addWidget(self.breathing_widget)
        self.breathing_widget.hide()

        # Add DrinkingGlassWidget
        self.glass_widget = DrinkingGlassWidget()
        main_layout.addWidget(self.glass_widget)
        self.glass_widget.hide()

        # Add ImageSlideshow
        self.image_slideshow = ImageSlideshow(
            [
                get_resource_path(f)
                for f in [
                    "exercises/exercise-1.png",
                    "exercises/exercise-2.png",
                    "exercises/exercise-3.png",
                    "exercises/exercise-4.png",
                    "exercises/exercise-5.png",
                    "exercises/exercise-6.png",
                    "exercises/exercise-7.png",
                    "exercises/exercise-8.png",
                    "exercises/exercise-9.png",
                    "exercises/exercise-10.png",
                    "exercises/exercise-11.png",
                    "exercises/exercise-12.png",
                ]
            ],
            delay_ms=10000,
        )
        main_layout.addWidget(self.image_slideshow)
        self.image_slideshow.hide()

        self.setLayout(main_layout)
        logging.debug("BreakActivityWindow initialized")

    def start_breathing_exercise(self):
        self.breathing_widget.show()
        self.breathing_widget.start()

    def stop_breathing_exercise(self):
        self.breathing_widget.hide()
        self.breathing_widget.stop()

    def set_activity(self, activity):
        """Set the activity text and adjust the window size."""
        logging.debug(f"Setting break activity: {activity}")
        if activity == "Do some deep breathing exercises":
            self.start_breathing_exercise()
        elif activity == "Get a glass of water":
            self.glass_widget.show()
        elif activity == "Perform desk exercises":
            self.image_slideshow.show()
        self.activity_label.setText(activity)
        self.adjustSize()

    def mousePressEvent(self, event):
        """Enable dragging the window."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()
            logging.debug("BreakActivityWindow: Mouse press event (start drag)")

    def mouseMoveEvent(self, event):
        """Handle window dragging."""
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
            logging.debug("BreakActivityWindow: Mouse move event (dragging)")

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Escape:
            logging.debug("BreakActivityWindow: Escape key pressed, hiding window")
            self.hide()
        else:
            super().keyPressEvent(event)

    def hide_custom_widgets(self):
        self.stop_breathing_exercise()
        self.glass_widget.hide()
        self.image_slideshow.hide()


class ActiveBreaksApp(QSystemTrayIcon):
    """System Tray Application for managing active breaks."""

    def __init__(self):
        super().__init__()
        logging.debug("Initializing ActiveBreaksApp")

        self.setIcon(QIcon("assets/icon.ico"))

        # Initialize settings
        self.settings = QSettings("deskriders", "activebreaks")
        self.work_duration = self.settings.value(
            "work_duration", 1500, type=int
        )  # 25 minutes
        self.break_duration = self.settings.value(
            "break_duration", 300, type=int
        )  # 5 minutes
        self.hold_duration = self.settings.value(
            "hold_duration", 5000, type=int
        )  # 5 seconds
        self.breath_duration = self.settings.value(
            "breath_duration", 7000, type=int
        )  # 7 seconds
        logging.debug(
            f"Initial settings: Work duration: {self.work_duration}, Break duration: {self.break_duration}, Hold duration: {self.hold_duration}, Breath duration: {self.breath_duration}"
        )

        # Initialize timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.time_left = 0
        self.is_working = False
        self.is_active = False

        # Initialize delay timer
        self.delay_timer = QTimer()
        self.delay_timer.setSingleShot(True)
        self.delay_timer.timeout.connect(self.start_break)

        # Initialize blink timer
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.blink_icon)
        self.is_icon_visible = True
        self.blink_color = "amber"  # Can be "amber" or "blue"

        # Create custom icon
        self.icon_pixmap = QPixmap(32, 32)
        self.setIcon(QIcon(self.icon_pixmap))
        self.setVisible(True)

        # Create the context menu
        self.menu = QMenu()
        self.work_action = self.menu.addAction("Start Work")
        self.break_action = self.menu.addAction("Start Break")
        self.menu.addSeparator()
        self.settings_action = self.menu.addAction("Settings")
        self.quit_action = self.menu.addAction("Quit")

        # Connect menu actions
        self.work_action.triggered.connect(self.toggle_work)
        self.break_action.triggered.connect(self.toggle_break)
        self.settings_action.triggered.connect(self.show_settings)
        self.quit_action.triggered.connect(self.quit_app)

        # Set the context menu to the tray icon
        self.setContextMenu(self.menu)

        # Initialize the icon
        self.update_icon()

        # Initialize break activities
        self.break_activities = [
            "Take a short walk",  # show timer
            "Do some deep breathing exercises",  # breathing
            "Perform desk exercises",  # show sketches of exercises
            "Get a glass of water",  # show a water glass and keep track of glasses
            "Look at something 20 feet away for 20 seconds",  # show timer
        ]
        self.remaining_activities = self.break_activities.copy()

        # Initialize break activity window
        self.break_window = BreakActivityWindow(
            hold_duration=self.hold_duration, breath_duration=self.breath_duration
        )

        # Initialize full screen blocker
        self.screen_blocker = FullScreenBlocker()

        # Start amber blinking immediately as neither work nor break is active
        self.start_blinking("amber")

        logging.info("ActiveBreaksApp initialized")

    def toggle_work(self):
        """Toggle the work timer."""
        logging.debug("Toggle work timer called")
        if self.is_active and self.is_working:
            self.stop_timer()
        else:
            self.start_work()

    def toggle_break(self):
        """Toggle the break timer and show break activity window."""
        logging.debug("Toggle break timer called")
        if self.is_active and not self.is_working:
            self.stop_timer()
            self.break_window.hide()
        else:
            self.start_break()

    def start_work(self):
        """Start the work timer."""
        self.stop_timer()  # stop break activities if it wasn't stopped manually

        logging.info("Starting work timer")
        self.is_working = True
        self.is_active = True
        self.time_left = self.work_duration
        self.timer.start(1000)  # Update every second
        self.update_timer()
        self.update_menu_text()
        self.stop_blinking()  # Stop blinking when work starts
        self.screen_blocker.hide()  # Hide screen blocker when work starts
        logging.debug(f"Work timer started. Duration: {self.work_duration} seconds")

    def start_break(self):
        """Start the break timer."""
        logging.info("Starting break timer")
        self.is_working = False
        self.is_active = True
        self.time_left = self.break_duration
        self.timer.start(1000)  # Update every second
        self.update_timer()
        self.update_menu_text()
        self.show_break_activity()
        self.stop_blinking()  # Stop blinking when break starts
        self.screen_blocker.show()  # Show full screen blocker during break
        logging.debug(f"Break timer started. Duration: {self.break_duration} seconds")

    def stop_timer(self):
        """Stop the active timer and hide the break activity window."""
        logging.info("Stopping timer")
        self.timer.stop()
        self.is_active = False
        self.update_icon(0)
        self.setToolTip("")
        self.update_menu_text()
        self.break_window.hide()
        self.screen_blocker.hide()  # Hide screen blocker when timer stops
        self.start_blinking("amber")  # Start amber blinking when timer stops
        self.break_window.hide_custom_widgets()
        logging.debug("Timer stopped and UI updated")

    def update_timer(self):
        """Update the timer countdown and UI elements."""
        if self.time_left > 0:
            minutes, seconds = divmod(self.time_left, 60)
            time_str = f"{minutes:02d}:{seconds:02d}"
            current_state = "Work" if self.is_working else "Break"
            self.setToolTip(f"{current_state}: {time_str}")

            progress = 1 - (
                self.time_left
                / (self.work_duration if self.is_working else self.break_duration)
            )
            self.update_icon(progress)
            self.time_left -= 1
            logging.debug(f"Timer updated: {current_state} - {time_str}")
        else:
            logging.info("Timer finished")
            if self.is_working:
                self.stop_timer()
                # Start blue blinking before break
                self.start_blinking("blue")
                # Start break after a 3-second delay
                self.delay_timer.start(3000)
                logging.info("Work finished. Break will start in 3 seconds.")
            else:
                self.stop_timer()
                logging.info("Break finished.")

    def update_icon(self, progress: float = 0, color: str = None):
        """Update the tray icon to reflect the current progress."""
        self.icon_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(self.icon_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background circle
        background_color = QColor(200, 200, 200)
        painter.setBrush(background_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(0, 0, 32, 32))

        # Draw progress arc if there is progress
        if progress > 0:
            progress_color = (
                QColor(0, 120, 212) if self.is_working else QColor(76, 175, 80)
            )
            painter.setBrush(progress_color)
            start_angle = 90 * 16
            span_angle = int(-progress * 360 * 16)
            painter.drawPie(0, 0, 32, 32, start_angle, span_angle)

        # Draw inner circle
        if color == "amber":
            inner_color = QColor(255, 191, 0)  # Amber color
        elif color == "blue":
            inner_color = QColor(0, 120, 212)  # Blue color
        else:
            inner_color = (
                QColor(0, 120, 212) if self.is_working else QColor(76, 175, 80)
            )
        painter.setBrush(inner_color)
        painter.drawEllipse(QRectF(8, 8, 16, 16))

        painter.end()
        self.setIcon(QIcon(self.icon_pixmap))
        logging.debug(f"Icon updated with progress: {progress:.2f}, color: {color}")

    def update_menu_text(self):
        """Update the text of the menu actions based on the current state."""
        if self.is_active:
            if self.is_working:
                self.work_action.setText("Stop Work")
                self.break_action.setText("Start Break")
            else:
                self.work_action.setText("Start Work")
                self.break_action.setText("Stop Break")
        else:
            self.work_action.setText("Start Work")
            self.break_action.setText("Start Break")
        logging.debug(
            f"Menu text updated. Is active: {self.is_active}, Is working: {self.is_working}"
        )

    def show_settings(self):
        """Display the settings dialog."""
        logging.info("Opening settings dialog")
        dialog = SettingsDialog(
            self.work_duration,
            self.break_duration,
            self.hold_duration,
            self.breath_duration,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            (
                self.work_duration,
                self.break_duration,
                self.hold_duration,
                self.breath_duration,
            ) = dialog.get_settings()
            self.save_settings()
            logging.info(
                f"Settings updated: Work duration: {self.work_duration}, Break duration: {self.break_duration}, Hold duration: {self.hold_duration}, Breath duration: {self.breath_duration}"
            )
        else:
            logging.info("Settings dialog cancelled")

    def save_settings(self):
        """Save the current settings."""
        logging.debug("Saving settings")
        self.settings.setValue("work_duration", self.work_duration)
        self.settings.setValue("break_duration", self.break_duration)
        self.settings.setValue("hold_duration", self.hold_duration)
        self.settings.setValue("breath_duration", self.breath_duration)
        self.settings.sync()
        logging.info("Settings saved")

    def select_random_activity(self):
        if not self.remaining_activities:
            self.remaining_activities = self.break_activities.copy()
            logging.info("All activities have been shown. Resetting the list.")

        activity = random.choice(self.remaining_activities)
        self.remaining_activities.remove(activity)
        logging.debug(f"Selected activity: {activity}")
        logging.debug(f"Remaining activities: {self.remaining_activities}")

        return activity

    def show_break_activity(self):
        """Show the break activity window with a random activity."""
        activity = self.select_random_activity()
        self.break_window.set_activity(activity)

        # Position the window just below the system tray icon
        icon_geometry = self.geometry()
        self.break_window.move(
            icon_geometry.x(), icon_geometry.y() + icon_geometry.height()
        )
        self.break_window.show()
        logging.info(f"Break activity shown: {activity}")

    def quit_app(self):
        """Quit the application."""
        logging.info("Quitting application")
        QApplication.instance().quit()

    def start_blinking(self, color: str):
        """Start blinking the icon with the specified color."""
        self.blink_color = color
        self.blink_timer.start(500)  # Blink every 500 ms
        logging.debug(f"{color.capitalize()} icon blinking started")

    def stop_blinking(self):
        """Stop blinking the icon and reset to normal state."""
        self.blink_timer.stop()
        self.is_icon_visible = True
        self.update_icon()
        logging.debug("Icon blinking stopped")

    def blink_icon(self):
        """Toggle icon visibility for blinking effect with the current blink color."""
        self.is_icon_visible = not self.is_icon_visible
        if self.is_icon_visible:
            self.update_icon(color=self.blink_color)
        else:
            self.setIcon(QIcon())
        logging.debug(
            f"{self.blink_color.capitalize()} icon blink: {'visible' if self.is_icon_visible else 'hidden'}"
        )


def main():
    """Main function to run the Active Breaks application."""
    logging.info("Starting Active Breaks application")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    active_breaks_app = ActiveBreaksApp()
    active_breaks_app.show()
    logging.info("Active Breaks application started and running")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
