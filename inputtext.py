# $Id$

from PyQt4 import QtCore, QtGui

from qt_utils import connect
from openmsx_utils import tclEscape

class InputText(object):

	def __init__(self, bridge):
		self.__cfDialog = None
		self.__ui = None
		self.__bridge = bridge

	def show(self):
		dialog = self.__cfDialog
		if dialog is None:
			self.__cfDialog = dialog = QtGui.QDialog(
				None, # TODO: find a way to get the real parent
				QtCore.Qt.Dialog
				| QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowSystemMenuHint
				)
			# Setup UI made in Qt Designer.
			from ui_inputtext import Ui_InputTextDialog
			ui = Ui_InputTextDialog()
			ui.setupUi(dialog)
			self.__ui = ui

			# the following property is missing in Designer somehow
			ui.inputText.setWordWrapMode(QtGui.QTextOption.WrapAnywhere)

			# Connect signals.
			connect(ui.sendButton, 'clicked()', self.__typeInputText)
			connect(ui.clearButton, 'clicked()', self.__clearInputText)

		dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	def __typeInputText(self):
		#TODO: Capture Regular expressions chars like { [ at the beginning of a line
		strText = tclEscape(self.__ui.inputText.toPlainText())
		self.__bridge.sendCommandRaw('type "%s"' % strText)

	def __clearInputText(self):
		self.__ui.inputText.clear()
