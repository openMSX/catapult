# $Id$

from PyQt4 import QtCore, QtGui
from preferences import preferences
from qt_utils import connect

class ConfigDialog:

	def __init__(self):
		self.__configDialog = None
		self._browseExecutableButton = None
		self._execEdit = None

	def show(self):
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
			self._browseExecutableButton = getattr(ui, "BrowseExecutableButton")
			self._execEdit = getattr(ui, "ExecEdit")
			self._execEdit.setText(preferences['system/executable'])
			connect(self._browseExecutableButton, 'clicked()', self.browseExec)
			connect(self._execEdit, 'editingFinished()', self.setExec)
		dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	def setExec(self):
		preferences['system/executable'] = self._execEdit.text()

	def browseExec(self):
		path =  QtGui.QFileDialog.getOpenFileName(
			self._browseExecutableButton,
			'Select openMSX executable',
			QtCore.QDir.currentPath(),
			'All Files (*)'
			)
		if not path.isNull():
			self._execEdit.setText(path)
		self.setExec()

configDialog = ConfigDialog()
