# $Id: softwaredb.py 7510 2008-01-03 17:10:17Z mthuurne $

from PyQt4 import QtCore, QtGui
from qt_utils import connect
from player import PlayState
from slideshow import Slideshow

class Autorun(QtGui.QWidget):

	def __init__(self, mainwindow,bridge):
		QtGui.QWidget.__init__(self)
		self.__dmDialog = None
		self.__ui = None
		self.__mainwindow = mainwindow
		self.__bridge = bridge
		self.__timerinit = 20
		self.timer = QtCore.QTimer()
		self.__cursor = None

		self.__runAfterAply = 1
		self.__sendState = 0
		self.__MSX = "msx2"
		self.__diska = "Empty"
		self.__carta = "Empty"
		self.__diskb = "Empty"
		self.__cartb = "Empty"
		self.__extensions = "Empty"

		self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.counterTimeOut)

	def counterTimeOut(self):
		lcd = self.__ui.lcdNumber
		if lcd.intValue() > 0:
			lcd.display(lcd.intValue() - 1)
		else:
			self.stopTimer()
			self.__runAfterAply = 1
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
			self.__dmDialog = dialog = QtGui.QDialog(
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
				ui.comboBoxGames.addItem(QtCore.QString(row[0]))


			self.startTimer()

			# Connect signals.
			#connect(ui.dirUpButton, 'clicked()', self.updir)

			# connect regular buttons
			connect(
				ui.comboBoxGames,
				'activated(int)',
				self.selectionChanged
				)
			connect(
				ui.pushButtonApply,
				'clicked()',
				self.applySettings
				)
			connect(
				ui.pushButtonCounter,
				'clicked()',
				self.on_pushButtonCounter_clicked
				)
			self.selectionChanged(0)
		dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	@QtCore.pyqtSignature("")
	def applySettings(self):
		self.__sendState = 0
		if self.__ui.checkBoxExtensions.isChecked() and not self.__ui.checkBoxMSX.isChecked():
			#extensions are removed when switching machine, but
			#here we do not want to switch machine!
			self.__bridge.command('list_extensions', )(self.clearExtensions)
		else:
			self.applySettingsCont("bogus")
	
	def clearExtensions(self,extlist):
		for ext in self.__extensions.split(' '):
			self.__bridge.command('remove_extension', ext)()
		
		self.applySettingsCont("bogus")

	def applySettingsCont(self,ignoredReturnValue):
		switch = self.__sendState
		self.__sendState = 1 + self.__sendState
		if switch == 0:
			if self.__ui.checkBoxMSX.isChecked():
				self.__bridge.command('machine', self.__MSX)(self.applySettingsCont)
			else:
				self.applySettingsCont()

		if switch == 1:
			if self.__ui.checkBoxExtensions.isChecked():
				#TODO Fix this thing since it creates to much callbacks if more then one ext is given...
				for ext in self.__extensions.split(','):
					self.__bridge.command('ext', ext)(self.applySettingsCont)
			else:
				self.applySettingsCont()

		if switch == 2:
			if self.__ui.checkBoxDiska.isChecked():
				disk = self.__diska
				if disk == "Empty":
					disk = "eject"
				self.__bridge.command('diska', disk)(self.applySettingsCont,self.applySettingsCont)
			else:
				self.applySettingsCont()

		if switch == 3:
			if self.__ui.checkBoxDiskb.isChecked():
				disk = self.__diskb
				if disk == "Empty":
					disk = "eject"
				self.__bridge.command('diskb', disk)(self.applySettingsCont,self.applySettingsCont)
			else:
				self.applySettingsCont()

		if switch == 4:
			if self.__ui.checkBoxCarta.isChecked():
				cart = self.__carta
				if cart == "Empty":
					cart = "eject"
				self.__bridge.command('carta', cart)(self.applySettingsCont,self.applySettingsCont)
			else:
				self.applySettingsCont()

		if switch == 5:
			if self.__ui.checkBoxCartb.isChecked():
				cart = self.__cartb
				if cart == "Empty":
					cart = "eject"
				self.__bridge.command('cartb', cart)(self.applySettingsCont,self.applySettingsCont)
			else:
				self.applySettingsCont()

		if switch == 6:
			if self.__runAfterAply:
				self.__runAfterAply = 0
				self.__mainwindow.getPlayState().setState(PlayState.play)
				self.__bridge.command('reset')()

	# Slots:

	@QtCore.pyqtSignature("")
	def selectionChanged(self,index):
		cursor = self.__cursor
		index = index + 1
		cursor.execute('SELECT Machine, Title, Info, Extensions, Timeout, Media, File FROM autorun WHERE id = ' + str(index) )
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

			self.__ui.checkBoxMSX.setText( QtCore.QString("MSX: " + self.__MSX ))
			self.__ui.checkBoxDiska.setText( QtCore.QString("diska: " + self.__diska ))
			self.__ui.checkBoxDiskb.setText( QtCore.QString("diskb: " + self.__diskb ))
			self.__ui.checkBoxCarta.setText( QtCore.QString("carta: " + self.__carta ))
			self.__ui.checkBoxCartb.setText( QtCore.QString("cartb: " + self.__cartb ))
			self.__ui.checkBoxExtensions.setText( QtCore.QString("extensions: " + self.__extensions ))
			self.__ui.labelGames.setText( QtCore.QString(row[2]) )
			self.__ui.slideshowWidget.reset()
			self.__ui.slideshowWidget.findImagesForMedia( row[6] )

	@QtCore.pyqtSignature("")
	def on_pushButtonCounter_clicked(self):
		lcd = self.__ui.lcdNumber
		if lcd.intValue() == self.__timerinit:
			self.startTimer()
		else:
			self.stopTimer()

