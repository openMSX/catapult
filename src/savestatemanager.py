from PyQt5 import QtWidgets, QtCore, QtGui
from player import PlayState

class SaveStateManager(object):

	def __init__(self, bridge, playState):
		self.__bridge = bridge
		self.__playState = playState
		
		self.__saveStateListWidget = None
		self.__newFileLineEdit = None
		self.__newFileWidget = None
		self.__deleteStateButton = None
		self.__saveStateButton = None
		self.__loadStateButton = None
		self.__cancelButton = None

		self.__saveStateDialog = dialog = QtWidgets.QDialog(
			None # TODO: find a way to get the real parent
			)

		from ui_savestatemanager import Ui_saveStateManager
		ui = Ui_saveStateManager()
		ui.setupUi(dialog)

		self.__saveStateListWidget = ui.saveStateListWidget
		self.__newFileLineEdit = ui.newFileLineEdit
		self.__newFileWidget = ui.newFileWidget
		self.__deleteStateButton = ui.deleteStateButton
		self.__saveStateButton = ui.saveStateButton
		self.__loadStateButton = ui.loadStateButton
		self.__cancelButton = ui.cancelButton

		# insert custom widget into generated gridlayout
		# (be careful, this may break if you change the layout...!)
		self.__imageView = ScaledImageView()
		self.__imageView.setText('No preview available...')
		ui.gridLayout.addWidget(self.__imageView, 0, 1, 1, 1)

		self.__cancelButton.clicked.connect( lambda: dialog.reject())
		self.__deleteStateButton.clicked.connect(self.__delete)
		self.__loadStateButton.clicked.connect(self.__load)
		self.__saveStateButton.clicked.connect(self.__save)
		self.__newFileLineEdit.returnPressed.connect(self.__save)
		self.__saveStateListWidget.itemSelectionChanged.connect(
			self.__updatePreview)

	def exec_(self, mode, parent = None):
		dialog = self.__saveStateDialog
		if mode == 'save':
			self.__loadStateButton.setVisible(False)
			self.__saveStateButton.setVisible(True)
			self.__newFileWidget.setVisible(True)
			self.__newFileWidget.setFocus()
			dialog.setWindowTitle('Save State')
		elif mode == 'load':
			self.__loadStateButton.setVisible(True)
			self.__saveStateButton.setVisible(False)
			self.__newFileWidget.setVisible(False)
			dialog.setWindowTitle('Load State')
		else:
			assert False, 'Invalid mode for dialog: ' + mode

		self.__newFileLineEdit.clear()
		self.__refreshList()
		self.__clearPreview()

		#dialog.setParent(parent) # why does this hang up the app?
		return dialog.exec_()

	def __refreshList(self):
		self.__bridge.command('list_savestates')(
			lambda *reply: self.__fill(*reply), None
			)

	def __fill(self, *saveStateList):
		self.__saveStateListWidget.clear()
		for saveState in saveStateList:
			self.__saveStateListWidget.addItem(saveState)

	def __delete(self):
		currentItem = self.__saveStateListWidget.currentItem()
		if currentItem == None:
			return
		selected = currentItem.text()
		if selected == '':
			return
		self.__bridge.command('delete_savestate',
			selected,
			)(
				lambda: self.__refreshList(),
				lambda message: self.__generalFailHandler(message, 'Problem deleting state')
			)

	def __load(self):
		currentItem = self.__saveStateListWidget.currentItem()
		if currentItem == None:
			return
		selected = currentItem.text()
		if selected == '':
			return
		# TODO: when loading fails, while state was STOP,
		# you see a nasty flicker (openMSX window becomes
		# visible for a short amount of time). Fix this!

		# save old play state
		state = self.__playState.getState()
		# set to play *before* loading the state
		self.__playState.setState(PlayState.play)

		self.__bridge.command('loadstate',
			selected
			)(
				lambda dummy: self.__saveStateDialog.accept(),
				lambda message: failHelper(message)
			)
		def failHelper(message):
			# failed, restore play state
			self.__playState.setState(state)
			self.__generalFailHandler(
				message, 'Problem loading state'
			)

	def __save(self):
		selected = self.__newFileLineEdit.text()
		if selected == '':
			currentItem = self.__saveStateListWidget.currentItem()
			if currentItem == None:
				return
			selected = currentItem.text()
			if selected == '':
				return
			reply = QtWidgets.QMessageBox.question(
				self.__saveStateDialog,
				'Overwrite \"' + selected + '\"?',
				'<p>Overwrite save state \"' + selected + '\".</p><p>Are you sure?</p>',
				QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel,
				QtWidgets.QMessageBox.Cancel)
			if reply == QtWidgets.QMessageBox.Cancel:
				return
		self.__newFileLineEdit.clear()
		self.__bridge.command('savestate',
				selected
			)(
				lambda dummy: self.__refreshList(),
				lambda message: self.__generalFailHandler(message, 'Problem saving state')
			)

	def __generalFailHandler(self, message, title):
		messageBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
			title, message, QtWidgets.QMessageBox.Ok,
			self.__saveStateDialog
			)
		messageBox.show()

	def __updatePreview(self):
		currentItem = self.__saveStateListWidget.currentItem()
		if currentItem == None:
			self.__clearPreview()
			return
		selected = currentItem.text()
		
		# get filename from openMSX
		self.__bridge.command('return',
			'"$::env(OPENMSX_USER_DATA)/../savestates/' + selected + '.png"'
			)(self.__updatePreview2)

	def __updatePreview2(self, fileName):
		image = QtGui.QImage(fileName)
		if image:
			self.__imageView.setImage(image)
		else:
			self.__clearPreview()

	def __clearPreview(self):
		self.__imageView.setImage(None)

class ScaledImageView(QtWidgets.QWidget):
	def __init__ (self, *args):
		QtWidgets.QWidget.__init__(self, *args)
		self.setSizePolicy(QtWidgets.QSizePolicy(
			QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
			))
		self.__image = None
		self.__scaledImage = None
		self.__text = ''

	def setImage(self, image):
		self.__image = image
		if image != None:
			self.__updateScaledImage()
		else:
			self.__scaledImage = None
		self.update()

	def setText(self, text):
		self.__text = text
		self.update()

	def sizeHint(self):
		if self.__scaledImage != None:
			return self.__scaledImage.size()
		else:
			if self.__image == None:
				return QtCore.QSize(320, 240)
			else:
				return self.__image.size()

	def resizeEvent(self, event):
		if self.__image == None:
			return
		self.__updateScaledImage()

	def __updateScaledImage(self):
		self.__scaledImage = self.__image.scaled(self.size(),
			QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

	def paintEvent(self, event):
		painter = QtGui.QPainter(self)
		
		if self.__scaledImage != None:
			xpos = (self.width() - self.__scaledImage.width()) / 2
			ypos = (self.height() - self.__scaledImage.height()) / 2
		
			# draw the image on the widget
			painter.drawImage(xpos, ypos, self.__scaledImage)
		else:
			painter.drawText(QtCore.QRect(0, 0, self.width(), self.height()),
				QtCore.Qt.AlignCenter, self.__text)
