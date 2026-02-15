from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QSystemTrayIcon,
    QMenu
)
from PyQt6.QtGui import QFont, QIcon, QAction
from PyQt6.QtCore import Qt
import pyqtgraph as pg


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Sound Recorder")
        self.setFixedSize(500, 400)  # Fixed window size

        # ---------------- Dark/Light Styles ----------------
        self.DARK_STYLE = """
        QWidget {
            background-color: #1e1e1e;
            color: #ffffff;
            font-family: 'Segoe UI';
        }
        QPushButton {
            background-color: #2d2d2d;
            border: 1px solid #555555;
            padding: 6px;
            border-radius: 6px;
        }
        QPushButton:hover {
            background-color: #3e3e3e;
        }
        QLabel {
            color: #ffffff;
        }
        QCheckBox {
            color: #ffffff;
        }
        """

        self.LIGHT_STYLE = """
        QWidget {
            background-color: #f2f2f2;
            color: #000000;
            font-family: 'Segoe UI';
        }
        QPushButton {
            background-color: #e0e0e0;
            border: 1px solid #bbbbbb;
            padding: 6px;
            border-radius: 6px;
        }
        QPushButton:hover {
            background-color: #d5d5d5;
        }
        QLabel {
            color: #000000;
        }
        QCheckBox {
            color: #000000;
        }
        """

        # Set default dark mode
        self.setStyleSheet(self.DARK_STYLE)

        # ---------------- UI Elements ----------------
        self.init_ui()

        # ---------------- System Tray ----------------
        self.init_tray()

    # ---------------- UI Setup ----------------
    def init_ui(self):
        main_layout = QVBoxLayout()

        # Title
        self.title_label = QLabel("Sound Recorder")
        self.title_label.setFont(QFont("Segoe UI", 20))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Timer Label
        self.timer_label = QLabel("00:00")
        self.timer_label.setFont(QFont("Segoe UI", 24))
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Waveform Plot
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setYRange(-1, 1)  # Audio amplitude
        self.plot_widget.setBackground("#1e1e1e")
        self.curve = self.plot_widget.plot(pen=pg.mkPen('#00d4ff', width=2))

        # Buttons Layout
        button_layout = QHBoxLayout()
        self.record_button = QPushButton("Record")
        self.pause_button = QPushButton("Pause")
        self.stop_button = QPushButton("Stop")
        self.play_button = QPushButton("Play")

        # Disable buttons initially
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.play_button.setEnabled(False)

        button_layout.addWidget(self.record_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.play_button)

        # Dark mode toggle
        self.dark_mode_toggle = QCheckBox("Dark Mode")
        self.dark_mode_toggle.setChecked(True)
        self.dark_mode_toggle.stateChanged.connect(self.toggle_dark_mode)
        button_layout.addWidget(self.dark_mode_toggle)

        # Add widgets to main layout
        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.timer_label)
        main_layout.addWidget(self.plot_widget)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    # ---------------- Dark/Light Mode ----------------
    def toggle_dark_mode(self, state):
        """Toggle between dark and light UI"""
        if state:  # dark mode
            self.setStyleSheet(self.DARK_STYLE)
            self.plot_widget.setBackground("#1e1e1e")
            self.curve.setPen('#00d4ff')
        else:  # light mode
            self.setStyleSheet(self.LIGHT_STYLE)
            self.plot_widget.setBackground("#ffffff")
            self.curve.setPen('#007acc')

    # ---------------- System Tray ----------------
    def init_tray(self):
        # Make sure you have an icon file named "icon.png" in your project folder
        self.tray_icon = QSystemTrayIcon(QIcon("icons.ico"), self)
        self.tray_icon.setToolTip("Sound Recorder")

        # Tray menu
        menu = QMenu()
        restore_action = QAction("Restore", self)
        restore_action.triggered.connect(self.show)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        menu.addAction(restore_action)
        menu.addAction(quit_action)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    # ---------------- Close Event ----------------
    def closeEvent(self, event):
        """Close app completely, remove tray icon"""
        self.tray_icon.hide()  # Remove tray icon
        event.accept()          # Accept the close event

