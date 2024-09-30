import logging
import random
import sys
from pathlib import Path

from PyQt6.QtCore import QRectF
from PyQt6.QtCore import QSettings
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QTimer
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

# Set up logging
log_dir = Path.home() / ".logs" / "active_breaks"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "active_breaks.log"

logging.basicConfig(
    filename=str(log_file),
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logging
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class SettingsDialog(QDialog):
    """Dialog to configure work and break durations."""

    def __init__(self, work_duration: int, break_duration: int, parent=None):
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

    def get_settings(self) -> tuple[int, int]:
        """Retrieve the work and break durations from the dialog."""
        work_duration = self.work_spinbox.value() * 60
        break_duration = self.break_spinbox.value() * 60
        logging.debug(
            f"Settings retrieved: Work duration: {work_duration}, Break duration: {break_duration}"
        )
        return work_duration, break_duration


class BreakActivityWindow(QWidget):
    """Window to display a random break activity."""

    def __init__(self, parent=None):
        super().__init__(
            parent,
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint,
        )
        logging.debug("Initializing BreakActivityWindow")
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
        self.activity_label.setStyleSheet("font-size: 16px; padding: 10px;")
        main_layout.addWidget(self.activity_label)

        self.setLayout(main_layout)
        logging.debug("BreakActivityWindow initialized")

    def set_activity(self, activity):
        """Set the activity text and adjust the window size."""
        logging.debug(f"Setting break activity: {activity}")
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
        logging.debug(
            f"Initial settings: Work duration: {self.work_duration}, Break duration: {self.break_duration}"
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
            "Stand up and stretch",
            "Take a short walk",
            "Do some deep breathing exercises",
            "Perform desk exercises",
            "Get a glass of water",
            "Rest your eyes by looking at something 20 feet away for 20 seconds",
        ]

        # Initialize break activity window
        self.break_window = BreakActivityWindow()

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
        logging.info("Starting work timer")
        self.is_working = True
        self.is_active = True
        self.time_left = self.work_duration
        self.timer.start(1000)  # Update every second
        self.update_timer()
        self.update_menu_text()
        self.stop_blinking()  # Stop blinking when work starts
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
        self.start_blinking("amber")  # Start amber blinking when timer stops
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
        dialog = SettingsDialog(self.work_duration, self.break_duration)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.work_duration, self.break_duration = dialog.get_settings()
            self.save_settings()
            logging.info(
                f"Settings updated: Work duration: {self.work_duration}, Break duration: {self.break_duration}"
            )
        else:
            logging.info("Settings dialog cancelled")

    def save_settings(self):
        """Save the current settings."""
        logging.debug("Saving settings")
        self.settings.setValue("work_duration", self.work_duration)
        self.settings.setValue("break_duration", self.break_duration)
        self.settings.sync()
        logging.info("Settings saved")

    def show_break_activity(self):
        """Show the break activity window with a random activity."""
        activity = random.choice(self.break_activities)
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
