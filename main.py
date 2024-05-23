from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QWidget, QStatusBar, QDialog, QLineEdit, QDialogButtonBox
from PySide6.QtCore import QRunnable, Slot, Signal, QObject, QThreadPool

import serial
import traceback
import sys

from time import sleep

class WorkerSignals(QObject):
  '''
  Defines the signals available from a running worker thread.

  Supported signals are:

  finished
      No data

  error
      tuple (exctype, value, traceback.format_exc() )

  result
      object data returned from processing, anything

  progress
      int indicating % progress

  '''
  finished = Signal()
  error = Signal(tuple)
  result = Signal(object)
  progress = Signal(int)

class Worker(QRunnable):
  '''
  Worker thread

  Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

  :param callback: The function callback to run on this worker thread. Supplied args and
                    kwargs will be passed through to the runner.
  :type callback: function
  :param args: Arguments to pass to the callback function
  :param kwargs: Keywords to pass to the callback function

  '''

  def __init__(self, fn, *args, **kwargs):
    super(Worker, self).__init__()

    # Store constructor arguments (re-used for processing)
    self.fn = fn
    self.args = args
    self.kwargs = kwargs
    self.signals = WorkerSignals()

    # Add the callback to our kwargs
    self.kwargs['progressCallback'] = self.signals.progress

  @Slot()
  def run(self):
    '''
    Initialise the runner function with passed args, kwargs.
    '''

    # Retrieve args/kwargs here; and fire processing using them
    try:
      result = self.fn(*self.args, **self.kwargs)
    except:
      traceback.print_exc()
      exctype, value = sys.exc_info()[:2]
      self.signals.error.emit((exctype, value, traceback.format_exc()))
    else:
      self.signals.result.emit(result)  # Return the result of the processing
    finally:
      self.signals.finished.emit()  # Done

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
  def __init__(self, port, ssid, password):
    super().__init__()

    self.setWindowTitle("Smart Device Control")
    self.resize(300, 75)

    self.statusBar = QStatusBar()
    self.setStatusBar(self.statusBar)
    self.port = port
    self.ssid = ssid
    self.password = password

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
        self.ser.open()
      except:
        self.statusBar.showMessage("Connection failed. retrying in 3s...")
        self.ser = None
        sleep(3)
    progressCallback.emit(50)
    # self.ser.write((self.ssid + "," + self.password).encode())
    sleep(2)
    progressCallback.emit(100)

  def connectionComplete(self):
    self.connectionControlButton.setText("Connected")
    self.statusBar.showMessage("Connected to the device")
  
  def setProgress(self, n):
    self.statusBar.showMessage(f"Establishing connection... {n}%")

  def handleConnectionControl(self):
    self.connectionControlButton.setEnabled(False)
    worker = Worker(self.connectToSerial) # Any other args, kwargs are passed to the run function
    worker.signals.finished.connect(self.connectionComplete)
    worker.signals.progress.connect(self.setProgress)

    # Execute
    self.connectionControlButton.setText("Connecting...")
    self.threadpool.start(worker)

  def handleLightControl(self, checked):
    if checked:
        self.statusBar.showMessage("LED is turned on")
        self.lightControlButton.setText("Turn Off")
    else:
        self.statusBar.showMessage("LED is turned off")
        self.lightControlButton.setText("Turn On")

app = QApplication([])
dialog = UserInputDialog()
dialog.rejected.connect(sys.exit)
dialog.exec()
userInputs = dialog.getInputs()

mainWindow = MainWindow(userInputs[0], userInputs[1], userInputs[2])

app.exec()