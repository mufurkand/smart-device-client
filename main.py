from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QWidget, QStatusBar

app = QApplication([])

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Smart Device Control")

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        controls = Controls(self.statusBar)

        self.setCentralWidget(controls)

class Controls(QWidget):
    def __init__(self, statusBar):
        super().__init__()

        self.statusBar = statusBar

        lightControlRow = QHBoxLayout()

        lightControlLabel = QLabel("LED Control:")
  
        self.lightControlButton = QPushButton("Turn On")
        self.lightControlButton.setCheckable(True)
        self.lightControlButton.clicked.connect(self.handleLightControl)

        lightControlRow.addWidget(lightControlLabel)
        lightControlRow.addWidget(self.lightControlButton)

        layout = QVBoxLayout()
        layout.addLayout(lightControlRow)

        self.setLayout(layout)

    def handleLightControl(self, checked):
        if checked:
            self.statusBar.showMessage("LED is turned on")
            self.lightControlButton.setText("Turn Off")
        else:
            self.statusBar.showMessage("LED is turned off")
            self.lightControlButton.setText("Turn On")

mainWindow = MainWindow()
mainWindow.show()

app.exec()