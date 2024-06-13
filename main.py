from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QWidget, QStatusBar
from PySide6.QtCore import QThreadPool
from UserInputDialog import UserInputDialog
from AuthWindow import AuthWindow
from Worker import Worker
import serial
from time import sleep
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import binascii

# Provided key and IV in hex
key_hex = "172D38434357620C20222D3843574105"
iv_hex = "7B2B2E591DBB3AD54E32136ACD010507"

# Convert hex key and IV to bytes
key = binascii.unhexlify(key_hex)
iv = binascii.unhexlify(iv_hex)

def encrypt(plaintext, key, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_text = pad(plaintext.encode(), AES.block_size)
    encrypted_bytes = cipher.encrypt(padded_text)
    # Return encrypted bytes as hex
    return binascii.hexlify(encrypted_bytes).decode()

def decrypt(encrypted_hex, key, iv):
    encrypted_bytes = binascii.unhexlify(encrypted_hex)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_padded = cipher.decrypt(encrypted_bytes)
    return unpad(decrypted_padded, AES.block_size).decode()

# create the main window
class MainWindow(QMainWindow):
  def __init__(self, port, ssid, password):
    super().__init__()

    self.setWindowTitle("Smart Device Control")

    self.statusBar = QStatusBar()
    self.setStatusBar(self.statusBar)
    self.port = port
    self.ssid = ssid
    self.password = password

    self.ledOn = False
    self.sirenOn = False
    self.trunkOpen = False

    self.threadpool = QThreadPool()
    self.ser = None
    self.url = ""

    self.statusBar.showMessage("Not connected to the device.")
    
    connectionControlRow = QHBoxLayout()

    connectionControlLabel = QLabel("Connection Control:")
    self.connectionControlButton = QPushButton("Connect")
    self.connectionControlButton.setCheckable(True)
    self.connectionControlButton.clicked.connect(self.handleConnectionControl)

    connectionControlRow.addWidget(connectionControlLabel)
    connectionControlRow.addWidget(self.connectionControlButton)

    lightControlRow = QHBoxLayout()

    lightControlLabel = QLabel("LED Control:")

    self.lightControlButton = QPushButton("Turn On")
    self.lightControlButton.setCheckable(True)
    self.lightControlButton.setEnabled(False)
    self.lightControlButton.clicked.connect(self.handleLightControl)

    lightControlRow.addWidget(lightControlLabel)
    lightControlRow.addWidget(self.lightControlButton)

    sirenControlRow = QHBoxLayout()

    sirenControlLabel = QLabel("Siren Control:")

    self.sirenControlButton = QPushButton("Turn On")
    self.sirenControlButton.setCheckable(True)
    self.sirenControlButton.setEnabled(False)
    self.sirenControlButton.clicked.connect(self.handleSirenControl)

    sirenControlRow.addWidget(sirenControlLabel)
    sirenControlRow.addWidget(self.sirenControlButton)

    trunkControlRow = QHBoxLayout()

    trunkControlLabel = QLabel("Trunk Control:")

    self.trunkControlButton = QPushButton("Open")
    self.trunkControlButton.setCheckable(True)
    self.trunkControlButton.setEnabled(False)
    self.trunkControlButton.clicked.connect(self.handleTrunkControl)

    trunkControlRow.addWidget(trunkControlLabel)
    trunkControlRow.addWidget(self.trunkControlButton)

    layout = QVBoxLayout()
    layout.setContentsMargins(50,50,50,50)
    layout.addLayout(connectionControlRow)
    layout.addLayout(lightControlRow)
    layout.addLayout(sirenControlRow)
    layout.addLayout(trunkControlRow)

    controls = QWidget()
    controls.setLayout(layout)

    self.setCentralWidget(controls)
    
    self.show()

  def enableButtons(self):
    self.lightControlButton.setEnabled(True)
    self.sirenControlButton.setEnabled(True)
    self.trunkControlButton.setEnabled(True)

  def disableButtons(self):
    self.lightControlButton.setEnabled(False)
    self.sirenControlButton.setEnabled(False)
    self.trunkControlButton.setEnabled(False)

  # SERIAL CONNECTION WORKER

  def connectToSerial(self, progressCallback):
    while self.ser is None:
      progressCallback.emit(0)
      try:
        self.ser = serial.Serial(self.port, 115200, timeout=3)
      except:
        progressCallback.emit(-1)
        self.ser = None
        sleep(3)
    progressCallback.emit(33)
    credentials = self.ssid + "," + self.password
    encryptedCredentials = encrypt(credentials, key, iv)
    message = encryptedCredentials + "," + str(len(credentials))
    print(message)
    self.ser.write(message.encode())
    progressCallback.emit(66)
    while True:
      self.url = self.ser.readline().decode().strip()
      
      if self.url.startswith("I"):
        self.url = self.url[3:]
        break


  def connectionComplete(self):
    self.connectionControlButton.setText("Connected")
    self.statusBar.showMessage("Connected to the device")
    self.enableButtons()
  
  def setConnectionProgress(self, n):
    if n == -1:
      self.statusBar.showMessage("Connection failed. retrying in 3s...")
      return
    self.statusBar.showMessage(f"Establishing connection... {n}%")

  def handleConnectionControl(self):
    self.connectionControlButton.setEnabled(False)
    worker = Worker(self.connectToSerial) # Any other args, kwargs are passed to the run function
    worker.signals.finished.connect(self.connectionComplete)
    worker.signals.progress.connect(self.setConnectionProgress)

    # Execute
    self.connectionControlButton.setText("Connecting...")
    self.threadpool.start(worker)

  # SERIAL CONNECTION WORKER END

  # LED CONTROL WORKER
  
  def ledRequest(self, progressCallback):
    self.lightControlButton.setEnabled(False)
    progressCallback.emit(0)
    try:
      requestUrl = "";
      if self.ledOn:
        requestUrl = "https://" + self.url + "/ledoff"
      else:
        requestUrl = "https://" + self.url + "/ledon"

      requests.get(requestUrl, verify=False)
      progressCallback.emit(100)
    except:
      progressCallback.emit(-1)
    
    self.ledOn = not self.ledOn
    
  def setLedProgress(self, n):
    if n == -1:
      self.statusBar.showMessage("Request failed.")
      return
    self.statusBar.showMessage(f"Sending request... {n}%")

  def ledRequestComplete(self):
    if self.ledOn:
      self.lightControlButton.setText("Turn Off")
      self.statusBar.showMessage("LED is turned on")
      self.lightControlButton.setEnabled(True)
    else:
      self.lightControlButton.setText("Turn On")
      self.statusBar.showMessage("LED is turned off")
      self.lightControlButton.setEnabled(True)

  def handleLightControl(self, checked):
    if checked:
      worker = Worker(self.ledRequest)
      worker.signals.progress.connect(self.setLedProgress)
      worker.signals.finished.connect(self.ledRequestComplete)

      self.threadpool.start(worker)
    else:
      worker = Worker(self.ledRequest)
      worker.signals.progress.connect(self.setLedProgress)
      worker.signals.finished.connect(self.ledRequestComplete)

      self.threadpool.start(worker)
    
  # LED CONTROL WORKER END

  # SIREN CONTROL WORKER

  def sirenRequest(self, progressCallback):
    self.sirenControlButton.setEnabled(False)
    progressCallback.emit(0)
    try:
      requestUrl = "";
      if self.sirenOn:
        requestUrl = "https://" + self.url + "/sirenoff"
      else:
        requestUrl = "https://" + self.url + "/sirenon"

      requests.get(requestUrl, verify=False)
      progressCallback.emit(100)
    except:
      progressCallback.emit(-1)
    
    self.sirenOn = not self.sirenOn
    
  def setSirenProgress(self, n):
    if n == -1:
      self.statusBar.showMessage("Request failed.")
      return
    self.statusBar.showMessage(f"Sending request... {n}%")

  def sirenRequestComplete(self):
    if self.sirenOn:
      self.sirenControlButton.setText("Turn Off")
      self.statusBar.showMessage("Siren is turned on")
      self.sirenControlButton.setEnabled(True)
    else:
      self.sirenControlButton.setText("Turn On")
      self.statusBar.showMessage("Siren is turned off")
      self.sirenControlButton.setEnabled(True)

  def handleSirenControl(self, checked):
    if checked:
      worker = Worker(self.sirenRequest)
      worker.signals.progress.connect(self.setSirenProgress)
      worker.signals.finished.connect(self.sirenRequestComplete)

      self.threadpool.start(worker)
    else:
      worker = Worker(self.sirenRequest)
      worker.signals.progress.connect(self.setSirenProgress)
      worker.signals.finished.connect(self.sirenRequestComplete)

      self.threadpool.start(worker)

  # SIREN CONTROL WORKER END

  # TRUNK CONTROL WORKER

  def trunkRequest(self, progressCallback):
    self.trunkControlButton.setEnabled(False)
    progressCallback.emit(0)
    try:
      requestUrl = "";
      if self.trunkOpen:
        requestUrl = "https://" + self.url + "/trunkoff"
      else:
        requestUrl = "https://" + self.url + "/trunkon"

      requests.get(requestUrl, verify=False)
      progressCallback.emit(100)
    except:
      progressCallback.emit(-1)
    
    self.trunkOpen = not self.trunkOpen
    
  def setTrunkProgress(self, n):
    if n == -1:
      self.statusBar.showMessage("Request failed.")
      return
    self.statusBar.showMessage(f"Sending request... {n}%")

  def trunkRequestComplete(self):
    if self.trunkOpen:
      self.trunkControlButton.setText("Close")
      self.statusBar.showMessage("Trunk is open")
      self.trunkControlButton.setEnabled(True)
    else:
      self.trunkControlButton.setText("Open")
      self.statusBar.showMessage("Trunk is closed")
      self.trunkControlButton.setEnabled(True)

  def handleTrunkControl(self, checked):
    if checked:
      worker = Worker(self.trunkRequest)
      worker.signals.progress.connect(self.setTrunkProgress)
      worker.signals.finished.connect(self.trunkRequestComplete)

      self.threadpool.start(worker)
    else:
      worker = Worker(self.trunkRequest)
      worker.signals.progress.connect(self.setTrunkProgress)
      worker.signals.finished.connect(self.trunkRequestComplete)

      self.threadpool.start(worker)


app = QApplication([])

auth = AuthWindow()
app.exec()

dialog = UserInputDialog()
app.exec()
userInputs = dialog.getInputs()

mainWindow = MainWindow(userInputs[0], userInputs[1], userInputs[2])
app.exec()