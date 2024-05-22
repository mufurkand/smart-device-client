from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QWidget, QStatusBar, QDialog, QLineEdit, QDialogButtonBox

app = QApplication([])

# query the user for the serial port, SSID, and password
class UserInputDialog(QDialog):
  def __init__(self):
    super().__init__()

    self.setWindowTitle("Control Configuration")

    layout = QVBoxLayout()

    configPortRow = QHBoxLayout()
    configPortLabel = QLabel("Enter the serial port:")
    self.configPortLineEdit = QLineEdit()
    configPortRow.addWidget(configPortLabel)
    configPortRow.addWidget(self.configPortLineEdit)
    layout.addLayout(configPortRow)

    configSsidRow = QHBoxLayout()
    configSsidLabel = QLabel("Enter the SSID:")
    self.configSsidLineEdit = QLineEdit()
    configSsidRow.addWidget(configSsidLabel)
    configSsidRow.addWidget(self.configSsidLineEdit)
    layout.addLayout(configSsidRow)

    configPasswordRow = QHBoxLayout()
    configPasswordLabel = QLabel("Enter the password:")
    self.configPasswordLineEdit = QLineEdit()
    configPasswordRow.addWidget(configPasswordLabel)
    configPasswordRow.addWidget(self.configPasswordLineEdit)
    layout.addLayout(configPasswordRow)

    buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    buttonBox.accepted.connect(self.accept)
    buttonBox.rejected.connect(self.reject)

    layout.addWidget(buttonBox)

    self.setLayout(layout)

  def getInputs(self):
    return self.configPortLineEdit.text(), self.configSsidLineEdit.text(), self.configPasswordLineEdit.text()

# create the main window
class MainWindow(QMainWindow):
  def __init__(self):
    super().__init__()

    self.setWindowTitle("Smart Device Control")

    self.statusBar = QStatusBar()
    self.setStatusBar(self.statusBar)
    controls = Controls(self.statusBar)

    self.setCentralWidget(controls)

# create the controls
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

dialog = UserInputDialog()
if dialog.exec() == QDialog.Accepted:
  userInputs = dialog.getInputs()
  print(userInputs)
  # connect to the serial port using pyserial
  mainWindow = MainWindow()
  mainWindow.show()
  app.exec()