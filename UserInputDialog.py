from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDialogButtonBox
import sys

class UserInputDialog(QDialog):
  def __init__(self):
    super().__init__()

    self.setWindowTitle("Control Configuration")

    layout = QVBoxLayout()
    layout.setContentsMargins(50,50,50,50)

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
    self.rejected.connect(sys.exit)

    layout.addWidget(buttonBox)

    self.setLayout(layout)
    self.show()

  def getInputs(self):
    return self.configPortLineEdit.text(), self.configSsidLineEdit.text(), self.configPasswordLineEdit.text()