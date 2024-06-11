from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QLineEdit, QMainWindow, QStatusBar
from PySide6.QtCore import QThreadPool, Qt
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
    self.loginButton.setDefault(True)
    self.registerButton = QPushButton("Register")
    self.registerButton.clicked.connect(self.handleRegister)
    self.registerButton.setEnabled(False)
    buttonRow.addWidget(self.loginButton)
    buttonRow.addWidget(self.registerButton)

    layout = QVBoxLayout()
    layout.setContentsMargins(50,50,50,50)
    layout.addLayout(emailRow)
    layout.addLayout(passwordRow)
    layout.addLayout(buttonRow)

    auth = QWidget()
    auth.setLayout(layout)

    self.setCentralWidget(auth)
    self.show()

    # FIXME: timer errors are probably due to the fact gui updates are not happening in signal-connected functions
    worker = Worker(self.connectToDatabase)
    worker.signals.progress.connect(self.setConnectionProgress)
    worker.signals.finished.connect(self.handleDatabaseConnected)

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

  def keyPressEvent(self, event):
    if event.key() == Qt.Key_Return:
      self.handleLogin()

  def connectToDatabase(self, progressCallback):
    progressCallback.emit(0)
    while True:
      try:
        cred = firebase_admin.credentials.Certificate("firebase.json")
        firebase_admin.initialize_app(cred, {
          "databaseURL": self.config["FIREBASE_URL"]
        })
        progressCallback.emit(100)
        break
      except:
        progressCallback.emit(-1)
        sleep(3)

  def setConnectionProgress(self, n):
    if n == -1:
      self.statusBar.showMessage("Connection failed. retrying in 3s...")
      return
    self.statusBar.showMessage(f"Connecting to the database... {n}%")

  def handleDatabaseConnected(self):
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
      progressCallback.emit(-1)
      return

    try:
      auth.create_user(email=email, password=password)
    except:
      progressCallback.emit(-1)

  def setRegisterProgress(self, n):
    match n:
      case -1:
        self.statusBar.showMessage("Please fill in the email and password fields.")
        return
      case -2:
        self.statusBar.showMessage("User registration failed. Please try again.")
        return

    self.statusBar.showMessage(f"Registering user... {n}%")
  
  def handleRegisterComplete(self):
    self.clearFields()
    self.statusBar.showMessage("User registered successfully.")
    self.unlockButtons()

  def handleRegister(self):
    worker = Worker(self.registerUserToDatabase)
    worker.signals.progress.connect(self.setRegisterProgress)
    worker.signals.finished.connect(self.handleRegisterComplete)

    self.statusBar.showMessage("Preparing to register user...")
    self.threadpool.start(worker)

  def loginUser(self, progressCallback):
    email = self.emailLineEdit.text()
    password = self.passwordLineEdit.text()

    self.lockButtons()

    if email == "" or password == "":
      return False

    try:
      payload = json.dumps({"email":email, "password":password})
      FIREBASE_API_KEY = self.config["FIREBASE_API_KEY"] 
      rest_api_url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"

      r = requests.post(rest_api_url,
        params={"key": FIREBASE_API_KEY},
        data=payload)

      response = r.json()

      if 'error' in response and response['error']['message'] == 'INVALID_EMAIL':
        return False

      if 'error' in response and response['error']['message'] == 'INVALID_LOGIN_CREDENTIALS':
        return False

    except Exception as e:
      print(e)
      return

    return True
  
  def loginResult(self, result):
    if result:
      self.programmaticClose = True
      self.close()
      self.programmaticClose = False
      return
    
    self.statusBar.showMessage("User login failed. Please try again.")


  def handleLogin(self):
    worker = Worker(self.loginUser)
    worker.signals.result.connect(self.loginResult)
    worker.signals.finished.connect(self.unlockButtons)

    self.statusBar.showMessage("Preparing to log in...")
    self.threadpool.start(worker)