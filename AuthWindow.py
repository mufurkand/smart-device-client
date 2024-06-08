from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QLineEdit, QMainWindow, QStatusBar
from PySide6.QtCore import QThreadPool
import firebase_admin
from firebase_admin import auth
import sys
from dotenv import dotenv_values
from Worker import Worker
from time import sleep
import requests
import json

class AuthWindow(QMainWindow):
  def __init__(self):
    super().__init__()

    self.setWindowTitle("Authorization")
    self.resize(300, 75)

    self.threadpool = QThreadPool()

    self.statusBar = QStatusBar()
    self.setStatusBar(self.statusBar)
    self.config = dotenv_values(".env")
    self.programmaticClose = False

    emailRow = QHBoxLayout()
    emailLabel = QLabel("Email:")
    self.emailLineEdit = QLineEdit()
    emailRow.addWidget(emailLabel)
    emailRow.addWidget(self.emailLineEdit)

    passwordRow = QHBoxLayout()
    passwordLabel = QLabel("Password:")
    self.passwordLineEdit = QLineEdit()
    passwordRow.addWidget(passwordLabel)
    passwordRow.addWidget(self.passwordLineEdit)

    buttonRow = QHBoxLayout()
    self.loginButton = QPushButton("Log In")
    self.loginButton.clicked.connect(self.handleLogin)
    self.loginButton.setEnabled(False)
    self.registerButton = QPushButton("Register")
    self.registerButton.clicked.connect(self.handleRegister)
    self.registerButton.setEnabled(False)
    buttonRow.addWidget(self.loginButton)
    buttonRow.addWidget(self.registerButton)

    layout = QVBoxLayout()
    layout.addLayout(emailRow)
    layout.addLayout(passwordRow)
    layout.addLayout(buttonRow)

    auth = QWidget()
    auth.setLayout(layout)

    self.setCentralWidget(auth)
    self.show()

    # FIXME: timer errors are probably due to the fact gui updates are not happening in signal-connected functions
    worker = Worker(self.connectToDatabase)
    worker.signals.finished.connect(self.handleDatabaseConnection)

    self.statusBar.showMessage("Preparing to connect to the database...")
    self.threadpool.start(worker)
  
  def lockButtons(self):
    self.loginButton.setEnabled(False)
    self.registerButton.setEnabled(False)

  def unlockButtons(self):
    self.loginButton.setEnabled(True)
    self.registerButton.setEnabled(True)

  def clearFields(self):
    self.emailLineEdit.clear()
    self.passwordLineEdit.clear()

  def closeEvent(self, _):
    if not self.programmaticClose:
      sys.exit()

  def connectToDatabase(self, progressCallback):
    while True:
      try:
        cred = firebase_admin.credentials.Certificate("firebase.json")
        firebase_admin.initialize_app(cred, {
          "databaseURL": self.config["FIREBASE_URL"]
        })
        break
      except:
        self.statusBar.showMessage("Connection failed. retrying in 3s...")
        sleep(3)

  def handleDatabaseConnection(self):
    self.statusBar.showMessage("Connected to the database.")
    self.unlockButtons()

  def handleDatabaseConnectionProgress(self, n):
    self.statusBar.showMessage(f"Connecting to the database... {n}%")

  def registerUserToDatabase(self, progressCallback):
    email = self.emailLineEdit.text()
    password = self.passwordLineEdit.text()
    print(email, password)

    self.lockButtons()

    if email == "" or password == "":
      self.statusBar.showMessage("Please fill in the email and password fields.")
      return

    try:
      auth.create_user(email=email, password=password)
    except:
      self.statusBar.showMessage("User registration failed. Please try again.")
      return

    self.statusBar.showMessage("User registered successfully.")
    self.clearFields()

  def handleRegister(self):
    worker = Worker(self.registerUserToDatabase)
    worker.signals.finished.connect(self.unlockButtons)

    self.statusBar.showMessage("Preparing to register user...")
    self.threadpool.start(worker)

  def loginUser(self, progressCallback):
    email = self.emailLineEdit.text()
    password = self.passwordLineEdit.text()

    self.lockButtons()

    if email == "" or password == "":
      self.statusBar.showMessage("Please fill in the email and password fields.")
      return

    try:
      payload = json.dumps({"email":email, "password":password})
      FIREBASE_API_KEY = self.config["FIREBASE_API_KEY"] 
      rest_api_url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"

      r = requests.post(rest_api_url,
        params={"key": FIREBASE_API_KEY},
        data=payload)

      response = r.json()

      if 'error' in response and response['error']['message'] == 'INVALID_EMAIL':
        self.statusBar.showMessage("Invalid email. Please try again.")
        return False

      if 'error' in response and response['error']['message'] == 'INVALID_LOGIN_CREDENTIALS':
        self.statusBar.showMessage("Invalid password. Please try again.")
        return False

    except Exception as e:
      print(e)
      self.statusBar.showMessage("User login failed. Please try again.")
      return

    self.statusBar.showMessage("User logged in successfully.")
    self.clearFields()
    return True
  
  def closeWindow(self, result):
    if result:
      self.programmaticClose = True
      self.close()
      self.programmaticClose = False

  def handleLogin(self):
    worker = Worker(self.loginUser)
    worker.signals.result.connect(self.closeWindow)
    worker.signals.finished.connect(self.unlockButtons)

    self.statusBar.showMessage("Preparing to log in...")
    self.threadpool.start(worker)