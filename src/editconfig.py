# $Id$

from PyQt4 import QtCore, QtGui
from preferences import preferences
from qt_utils import connect

class ConfigDialog(object):

	def __init__(self):
		self.__configDialog = None
		self.__browseExecutableButton = None
		self.__execEdit = None

	def show(self, block = False):
		dialog = self.__configDialog
		if dialog is None:
			self.__configDialog = dialog = QtGui.QDialog(
				None, # TODO: find a way to get the real parent
				QtCore.Qt.Dialog
				| QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowSystemMenuHint
				)
			# Do not keep openMSX running just because of this dialog.
			dialog.setAttribute(QtCore.Qt.WA_QuitOnClose, False)
			# Setup UI made in Qt Designer.
			from ui_config import Ui_Dialog
			ui = Ui_Dialog()
			ui.setupUi(dialog)
			self.__browseExecutableButton = ui.browseExecutableButton
			self.__execEdit = ui.execEdit
			try:
				self.__execEdit.setText(preferences['system/executable'])
			except KeyError:
				self.__execEdit.setText('')
			connect(self.__browseExecutableButton, 'clicked()', self.__browseExec)
			connect(self.__execEdit, 'editingFinished()', self.__setExec)
		if block:
			dialog.exec_()
		else:
			dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	def __setExec(self):
		preferences['system/executable'] = self.__execEdit.text()

	def __browseExec(self):
		path =  QtGui.QFileDialog.getOpenFileName(
			self.__browseExecutableButton,
			'Select openMSX executable',
			QtCore.QDir.currentPath(),
			'All Files (*)'
			)
		if not path.isNull():
			self.__execEdit.setText(path)
		self.__setExec()

configDialog = ConfigDialog()
