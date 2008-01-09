# $Id: softwaredb.py 7510 2008-01-03 17:10:17Z mthuurne $

from PyQt4 import QtCore, QtGui
from qt_utils import connect
from slideshow import Slideshow

class Autorun(QtGui.QWidget):

	def __init__(self, bridge):
		QtGui.QWidget.__init__(self)
		self.__dmDialog = None
		self.__ui = None
		self.__bridge = bridge
		self.__timerinit = 120
		self.timer = QtCore.QTimer()
		self.__cursor = None

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
			self.startSoftware()

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
				ui.pushButtonCounter,
				'clicked()',
				self.on_pushButtonCounter_clicked
				)
			self.selectionChanged(0)
		dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	# Slots:

	@QtCore.pyqtSignature("")
	def selectionChanged(self,index):
		cursor = self.__cursor
		index = index + 1
		cursor.execute('SELECT Machine, Title, Info, Extentions, Timeout, Media, File FROM autorun WHERE id = ' + str(index) )
		for row in cursor:
			#TODO this is a quick hack to see something move :-)
			# will be fixed in next commit
			self.__MSX = row[0]
			self.__diska = row[6]
			self.__carta = "Empty"

			self.__ui.checkBoxMSX.setText( QtCore.QString("MSX: " + self.__MSX ))
			self.__ui.checkBoxDiska.setText( QtCore.QString("diska: " + self.__diska ))
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

