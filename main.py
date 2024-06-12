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

    layout = QVBoxLayout()
    layout.setContentsMargins(50,50,50,50)
    layout.addLayout(connectionControlRow)
    layout.addLayout(lightControlRow)

    controls = QWidget()
    controls.setLayout(layout)

    self.setCentralWidget(controls)
    
    self.show()

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
      print(self.url)
      
      if self.url.startswith("I"):
        self.url = self.url[3:]
        break


  def connectionComplete(self):
    self.connectionControlButton.setText("Connected")
    self.statusBar.showMessage("Connected to the device")
    self.lightControlButton.setEnabled(True)
  
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
  
  def RequestToServer(self, progressCallback):
    self.lightControlButton.setEnabled(False)
    progressCallback.emit(0)
    try:
      requestUrl = "https://" + self.url + ("/ledoff" if self.ledOn else "/ledon")
      requests.get(requestUrl, verify=False)
      progressCallback.emit(100)
    except:
      progressCallback.emit(-1)
    
    self.ledOn = not self.ledOn
    
  def setRequestProgress(self, n):
    if n == -1:
      self.statusBar.showMessage("Request failed.")
      return
    self.statusBar.showMessage(f"Sending request... {n}%")

  def requestComplete(self):
    if self.ledOn:
      self.lightControlButton.setText("Turn Off")
      self.statusBar.showMessage("LED is turned on")
      self.lightControlButton.setEnabled(True)
    else:
      self.lightControlButton.setText("Turn On")
      self.statusBar.showMessage("LED is turned off")
      self.lightControlButton.setEnabled(True)


  # TODO: spawn a worker for the requests
  def handleLightControl(self, checked):
    if checked:
      worker = Worker(self.RequestToServer)
      worker.signals.progress.connect(self.setRequestProgress)
      worker.signals.finished.connect(self.requestComplete)

      self.threadpool.start(worker)
    else:
      worker = Worker(self.RequestToServer)
      worker.signals.progress.connect(self.setRequestProgress)
      worker.signals.finished.connect(self.requestComplete)

      self.threadpool.start(worker)

app = QApplication([])

auth = AuthWindow()
app.exec()

dialog = UserInputDialog()
app.exec()
userInputs = dialog.getInputs()

mainWindow = MainWindow(userInputs[0], userInputs[1], userInputs[2])
app.exec()