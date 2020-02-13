from PyQt5 import QtCore, QtWidgets
from player import PlayState
from settings import BooleanSetting

class Autorun(QtWidgets.QWidget):

	def __init__(self, mainwindow, settingsManager, bridge):
		QtWidgets.QWidget.__init__(self)
		self.__dmDialog = None
		self.__ui = None
		self.__mainwindow = mainwindow
		self.__settingsManager = settingsManager
		self.__bridge = bridge
		self.__timerinit = 30
		self.timer = QtCore.QTimer()
		self.__cursor = None

		self.__runAfterApply = False
		self.__sendState = 0
		self.__MSX = "msx2"
		self.__diska = "Empty"
		self.__carta = "Empty"
		self.__diskb = "Empty"
		self.__cartb = "Empty"
		self.__extensions = "Empty"

		self.timer.timeout.connect(self.counterTimeOut)

		settingsManager.registerSetting('power', BooleanSetting)
		settingsManager['power'].valueChanged.connect(self.updatePowerInfo)

	def updatePowerInfo(self, value):
		if self.__ui == None:
			return
		if value:
			# User is running openMSX, so shouldn't be looking
			# anymore at the autorun slides :-)
			self.__ui.slideshowWidget.setSlideStopped(False)
			# extra stop timer in case the user manually
			# powered on the openmsx
			self.stopTimer()
		else:
			# MSX powered off after autorun started it,so we
			# restart counting,swicth to next game and
			# restart the slideshow
			if self.__runAfterApply:
				self.nextGame()
				self.startTimer()
				self.__ui.slideshowWidget.setSlideStopped(True)
				self.__runAfterApply = False

	def counterTimeOut(self):
		lcd = self.__ui.lcdNumber
		if lcd.intValue() > 0:
			lcd.display(lcd.intValue() - 1)
		else:
			self.stopTimer()
			self.__ui.slideshowWidget.setSlideStopped(False)
			self.__runAfterApply = True
			self.applySettings()

	def startTimer(self):
		self.__ui.lcdNumber.display(self.__timerinit)
		self.timer.start(1000)
		self.__ui.pushButtonCounter.setText(self.tr("stop timer"))

	def stopTimer(self):
		self.timer.stop()
		self.__ui.pushButtonCounter.setText(self.tr("start timer"))
		self.__ui.lcdNumber.display(self.__timerinit)

	def show(self):
		dialog = self.__dmDialog
		if dialog is None:
			self.__dmDialog = dialog = QtWidgets.QDialog(
				None, # TODO: find a way to get the real parent
				QtCore.Qt.Dialog
				| QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowSystemMenuHint
				)
			from pysqlite2 import dbapi2 as sqlite
			cursor = self.__cursor
			if cursor is None:
				connection = sqlite.connect('autorun.db')
				self.__cursor = cursor = connection.cursor()
			# Setup UI made in Qt Designer.
			from ui_autorun import Ui_Autorun
			ui = Ui_Autorun()
			ui.setupUi(dialog)
			self.__ui = ui
			#fill the components with values
			cursor.execute('SELECT Title FROM autorun')
			for row in cursor:
				ui.comboBoxGames.addItem(row[0])
			# Connect signals.
			#ui.dirUpButton.clicked.connect(self.updir)
			dialog.finished.connect(self.getsHidden)
			# connect regular buttons
			ui.comboBoxGames.activated.connect(self.selectionChanged)
			ui.pushButtonApply.clicked.connect(self.applySettings)
			ui.pushButtonCounter.clicked.connect(self.on_pushButtonCounter_clicked)
			self.selectionChanged(0)
		self.startTimer()
		dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	def applySettings(self):
		self.__sendState = 0
		if self.__ui.checkBoxExtensions.isChecked() and \
				not self.__ui.checkBoxMSX.isChecked():
			# Extensions are removed when switching machine,
			# but here we do not want to switch machine!
			self.__bridge.command('list_extensions', )(self.clearExtensions)
		else:
			self.applySettingsCont("bogus")

	def clearExtensions(self, extlist):
		for ext in extlist.split(' '):
			self.__bridge.command('remove_extension', ext)()

		self.applySettingsCont("bogus")

	def applySettingsCont(self, dummy):
		switch = self.__sendState
		self.__sendState = 1 + self.__sendState
		if switch == 0:
			if self.__ui.checkBoxMSX.isChecked():
				self.__bridge.command('machine', self.__MSX)(self.applySettingsCont)
			else:
				self.applySettingsCont("bogus")

		elif switch == 1:
			if self.__ui.checkBoxExtensions.isChecked() and self.__extensions != "Empty":
				#TODO Fix this thing since it creates
				#to much callbacks if more then one ext is given...
				#For now it is a it-just-works solution
				for ext in self.__extensions.split(','):
					self.__bridge.command('ext', ext)(
						self.applySettingsCont,self.applySettingsCont
						)
			else:
				self.applySettingsCont("bogus")

		elif switch == 2:
			if self.__ui.checkBoxDiska.isChecked():
				disk = self.__diska
				if disk == "Empty":
					disk = "eject"
				self.__bridge.command('diska', disk)(
					self.applySettingsCont,
					self.applySettingsCont)
			else:
				self.applySettingsCont("bogus")

		elif switch == 3:
			if self.__ui.checkBoxDiskb.isChecked():
				disk = self.__diskb
				if disk == "Empty":
					disk = "eject"
				self.__bridge.command('diskb', disk)(
					self.applySettingsCont,
					self.applySettingsCont)
			else:
				self.applySettingsCont("bogus")

		elif switch == 4:
			if self.__ui.checkBoxCarta.isChecked():
				cart = self.__carta
				if cart == "Empty":
					cart = "eject"
				self.__bridge.command('carta', cart)(
					self.applySettingsCont,
					self.applySettingsCont)
			else:
				self.applySettingsCont("bogus")

		elif switch == 5:
			if self.__ui.checkBoxCartb.isChecked():
				cart = self.__cartb
				if cart == "Empty":
					cart = "eject"
				self.__bridge.command('cartb', cart)(
					self.applySettingsCont,
					self.applySettingsCont)
			else:
				self.applySettingsCont("bogus")

		elif switch == 6:
			if self.__runAfterApply:
				self.__mainwindow.getPlayState().setState(PlayState.play)
				self.__bridge.command('reset')()
				if self.__ui.checkBoxShutdown.isChecked():
					self.__bridge.command('after', 'idle',
						self.__ui.spinBoxShutdown.value(),
						'quit')()

	def nextGame(self):
		combo = self.__ui.comboBoxGames
		index = 1 + combo.currentIndex()
		if index == combo.count():
			index = 0
		combo.setCurrentIndex(index)
		# setCurrentIndex doesn't emit signal
		# so we call the slot ourself
		self.selectionChanged(index)


	# Slots:

	#Stop timer when window is closed/hidden
	def getsHidden(self, result):
		print(" def getsHidden(self, result): ", result)
		self.stopTimer()

	def selectionChanged(self, index):
		cursor = self.__cursor
		index = index + 1
		cursor.execute('SELECT Machine, Title, Info, Extensions,' +
			' Timeout, Media, File FROM autorun WHERE id = ' +
			str(index) )
		for row in cursor:
			#TODO this is a quick hack to see something move :-)
			# will be fixed in next commit
			self.__MSX = row[0]
			self.__extensions = row[3]
			self.__carta = "Empty"
			self.__cartb = "Empty"
			self.__diska = "Empty"
			self.__diskb = "Empty"
			if row[5] == "diska":
				self.__diska = row[6]
			else:
				self.__carta = row[6]

			self.__ui.checkBoxMSX.setText(
				"MSX: " + self.__MSX
				)
			self.__ui.checkBoxDiska.setText(
				"diska: " + self.__diska
				)
			self.__ui.checkBoxDiskb.setText(
				"diskb: " + self.__diskb
				)
			self.__ui.checkBoxCarta.setText(
				"carta: " + self.__carta
				)
			self.__ui.checkBoxCartb.setText(
				"cartb: " + self.__cartb
				)
			self.__ui.checkBoxExtensions.setText(
				"extensions: " + self.__extensions
				)
			self.__ui.labelGames.setText(row[2])
			self.__ui.spinBoxShutdown.setValue(int(row[4]))
			self.__ui.slideshowWidget.reset()
			self.__ui.slideshowWidget.findImagesForMedia(row[6])

	def on_pushButtonCounter_clicked(self):
		lcd = self.__ui.lcdNumber
		if lcd.intValue() == self.__timerinit:
			self.startTimer()
			# also restart the slideshow in case we stopped it
			# because of manual launching openmsx
			self.__ui.slideshowWidget.setSlideStopped(True)
		else:
			self.stopTimer()
