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

		self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.counterTimeOut)

	def counterTimeOut(self):
		lcd = self.__ui.lcdNumber
		if lcd.intValue() > 0:
			lcd.display(lcd.intValue() - 1)
		else:
			self.stopTimer()

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
			# Setup UI made in Qt Designer.
			from ui_autorun import Ui_Autorun
			ui = Ui_Autorun()
			ui.setupUi(dialog)
			self.__ui = ui
			self.startTimer()

			# Connect signals.
			#connect(ui.dirUpButton, 'clicked()', self.updir)

			# connect regular buttons
			connect(
				ui.pushButtonCounter,
				'clicked()',
				self.on_pushButtonCounter_clicked
				)
		dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	# Slots:

	@QtCore.pyqtSignature("")
	def on_pushButtonCounter_clicked(self):
		lcd = self.__ui.lcdNumber
		if lcd.intValue() == self.__timerinit:
			self.startTimer()
		else:
			self.stopTimer()

