# The Vague Reminder
# A strange and unsettling desktop companion.
#
# Instructions:
# 1. Make sure you have Python installed.
# 2. Install the required library, PyQt6, by running this command in your terminal:
#    pip install PyQt6
# 3. Save this code as a Python file (e.g., vague_reminder.py).
# 4. Run the file from your terminal:
#    python vague_reminder.py
#
# How it works:
# An eye will appear on your screen. It will follow your mouse cursor.
# Right-click the eye to open a menu with options.
# The application will periodically send you strange, vague "reminders".

import sys
import random
from PyQt6.QtCore import Qt, QPoint, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QAction, QIcon, QPainterPath
from PyQt6.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu, QColorDialog

class VagueReminderEye(QWidget):
    """
    The main widget for the eye itself. It's a frameless, transparent,
    always-on-top window that draws the eye and makes it follow the cursor.
    """
    def __init__(self, parent_app):
        super().__init__()
        self.parent_app = parent_app
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |       # No window border
            Qt.WindowType.WindowStaysOnTopHint |      # Always on top
            Qt.WindowType.Tool                        # Doesn't appear in the task bar
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(100, 100, 150, 150) # Initial position and size

        # --- Eye Properties ---
        # Start with a default blue color instead of a random one.
        self.iris_color = QColor(100, 150, 220)
        self.sclera_color = QColor(245, 245, 245)
        self.pupil_color = QColor(10, 10, 10)
        self.outline_pen = QPen(QColor(20, 20, 20), 3)

        self.pupil_position = QPoint(0, 0)
        self.is_dragging = False
        self.drag_position = QPoint()

        # --- Timers ---
        # Timer to update the eye's gaze
        self.follow_timer = QTimer(self)
        self.follow_timer.timeout.connect(self.update_gaze)
        self.follow_timer.start(16) # ~60 FPS update

    def paintEvent(self, event):
        """Handles the drawing of the eye."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        center_x, center_y = rect.width() // 2, rect.height() // 2
        eye_radius = min(center_x, center_y) - 5

        # 1. Draw the Sclera (the white part)
        painter.setBrush(QBrush(self.sclera_color))
        painter.setPen(self.outline_pen)
        painter.drawEllipse(QPoint(center_x, center_y), eye_radius, eye_radius)

        # 2. Draw the Iris (the colored part)
        iris_radius = eye_radius * 0.7
        # The iris moves slightly with the pupil for a better effect
        iris_x = center_x + self.pupil_position.x() * 0.2
        iris_y = center_y + self.pupil_position.y() * 0.2
        painter.setBrush(QBrush(self.iris_color))
        painter.drawEllipse(QPoint(int(iris_x), int(iris_y)), int(iris_radius), int(iris_radius))

        # 3. Draw the Pupil (the black part)
        pupil_radius = iris_radius * 0.5
        pupil_x = center_x + self.pupil_position.x()
        pupil_y = center_y + self.pupil_position.y()
        painter.setBrush(QBrush(self.pupil_color))
        painter.setPen(Qt.PenStyle.NoPen) # No outline for the pupil
        painter.drawEllipse(QPoint(int(pupil_x), int(pupil_y)), int(pupil_radius), int(pupil_radius))

    def update_gaze(self):
        """Calculates where the pupil should be to look at the cursor."""
        try:
            # This can sometimes fail if the cursor is on another screen, so we have a fallback.
            cursor_pos = self.mapFromGlobal(self.cursor().pos())
        except Exception:
            # Fallback to screen center if getting cursor position fails.
            # This is the correct way to get the screen's geometry.
            screen_geo = QApplication.primaryScreen().geometry()
            cursor_pos = self.mapFromGlobal(screen_geo.center())


        center_x, center_y = self.width() // 2, self.height() // 2
        center_point = QPoint(center_x, center_y)

        # Vector from eye center to cursor
        vector = cursor_pos - center_point
        distance = (vector.x()**2 + vector.y()**2)**0.5

        # Max distance the pupil can travel from the center
        max_pupil_distance = (self.width() / 2) * 0.35

        if distance == 0:
            self.pupil_position = QPoint(0, 0)
        else:
            # Normalize the vector and scale it
            norm_x = vector.x() / distance
            norm_y = vector.y() / distance
            # Clamp the distance so the pupil stays within the iris
            pupil_distance = min(distance, max_pupil_distance)
            self.pupil_position = QPoint(int(norm_x * pupil_distance), int(norm_y * pupil_distance))

        self.update() # Trigger a repaint

    def contextMenuEvent(self, event):
        """Creates the right-click menu."""
        context_menu = QMenu(self)
        
        # Action to change eye color
        change_color_action = QAction("Choose Iris Color", self)
        change_color_action.triggered.connect(self.choose_iris_color)
        context_menu.addAction(change_color_action)

        context_menu.addSeparator()

        # Action to quit the application
        quit_action = QAction("Banish", self)
        quit_action.triggered.connect(self.parent_app.quit)
        context_menu.addAction(quit_action)

        context_menu.exec(event.globalPos())

    def choose_iris_color(self):
        """Opens a color dialog to let the user choose the iris color."""
        new_color = QColorDialog.getColor(self.iris_color, self, "Choose Iris Color")
        # If the user selected a color and didn't cancel the dialog
        if new_color.isValid():
            self.iris_color = new_color
            self.update()

    # --- Window Dragging Logic ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.is_dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.is_dragging = False
        event.accept()


class VagueReminderApp(QApplication):
    """
    The main application class that manages the eye, the system tray icon,
    and the reminder notifications.
    """
    def __init__(self, args):
        super().__init__(args)
        self.setQuitOnLastWindowClosed(False) # App continues running in tray

        # --- Reminder Content ---
        self.reminders = [
            "Remember that thing you forgot?",
            "It's probably later than you think.",
            "Are you sure you locked it?",
            "They know.",
            "Don't forget to breathe. Manually.",
            "You left something important behind.",
            "Check the date. Is it the right year?",
            "That quiet sound is not in your head.",
            "You are now aware of your own tongue.",
            "Was that a dream or a memory?",
            "Your keys are not where you think they are.",
            "Did you reply to that urgent message?",
            "The deadline is closer.",
            "Consider the weight of your choices.",
            "Look behind you. No, don't.",
            "It's still there.",
        ]

        # --- System Tray Icon ---
        # This allows the app to run in the background.
        self.tray_icon = QSystemTrayIcon(self)
        # A simple icon is drawn programmatically to avoid external files.
        self.tray_icon.setIcon(self.create_tray_icon())
        self.tray_icon.setToolTip("It's watching.")

        # Create the menu for the tray icon
        tray_menu = QMenu()
        show_action = QAction("It's gone...", self)
        show_action.triggered.connect(self.show_eye)
        tray_menu.addAction(show_action)

        quit_action = QAction("Banish Permanently", self)
        quit_action.triggered.connect(self.quit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # --- Main Components ---
        self.eye_widget = VagueReminderEye(self)
        self.eye_widget.show()

        # --- Reminder Timer ---
        # Triggers a random reminder at a random interval.
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self.show_reminder)
        self.schedule_next_reminder()

    def show_eye(self):
        """Shows the eye if it was hidden."""
        if not self.eye_widget.isVisible():
            self.eye_widget.show()
            self.tray_icon.showMessage(
                "It's Back",
                "You can't get rid of it that easily.",
                QSystemTrayIcon.MessageIcon.Warning,
                2000
            )

    def show_reminder(self):
        """Displays a random reminder notification."""
        if not self.tray_icon.isVisible():
            return

        reminder_text = random.choice(self.reminders)
        self.tray_icon.showMessage(
            "A Vague Reminder",
            reminder_text,
            QSystemTrayIcon.MessageIcon.Information,
            5000  # Show for 5 seconds
        )
        # Schedule the next one after this one is shown
        self.schedule_next_reminder()

    def schedule_next_reminder(self):
        """Sets the timer for the next reminder to a random interval."""
        # Random interval between 45 seconds and 3 minutes
        random_interval_ms = random.randint(45 * 1000, 180 * 1000)
        self.reminder_timer.start(random_interval_ms)

    def create_tray_icon(self) -> QIcon:
        """
        Generates a QIcon for the system tray without needing an image file.
        It's a simple black circle, representing the pupil.
        """
        from PyQt6.QtGui import QPixmap
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor("black")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(4, 4, 56, 56)
        painter.end()
        return QIcon(pixmap)


if __name__ == "__main__":
    app = VagueReminderApp(sys.argv)
    sys.exit(app.exec())
