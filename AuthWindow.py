from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QLineEdit, QMainWindow, QStatusBar
import sys

class AuthWindow(QMainWindow):
  def __init__(self):
    super().__init__()

    self.setWindowTitle("Authorization")
    self.resize(300, 75)

    self.statusBar = QStatusBar()
    self.setStatusBar(self.statusBar)

    self.statusBar.showMessage("Please provide the user credentials.")

    usernameRow = QHBoxLayout()
    usernameLabel = QLabel("Username:")
    self.usernameLineEdit = QLineEdit()
    usernameRow.addWidget(usernameLabel)
    usernameRow.addWidget(self.usernameLineEdit)

    passwordRow = QHBoxLayout()
    passwordLabel = QLabel("Password:")
    self.passwordLineEdit = QLineEdit()
    passwordRow.addWidget(passwordLabel)
    passwordRow.addWidget(self.passwordLineEdit)

    buttonRow = QHBoxLayout()
    self.loginButton = QPushButton("Log In")
    self.registerButton = QPushButton("Register")
    buttonRow.addWidget(self.loginButton)
    buttonRow.addWidget(self.registerButton)

    layout = QVBoxLayout()
    layout.addLayout(usernameRow)
    layout.addLayout(passwordRow)
    layout.addLayout(buttonRow)

    auth = QWidget()
    auth.setLayout(layout)

    self.setCentralWidget(auth)

    self.show()

  def closeEvent(self, _):
    sys.exit()

  def getInputs(self):
    return self.usernameLineEdit.text(), self.passwordLineEdit.text()