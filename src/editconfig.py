from PyQt5 import QtCore, QtWidgets
from preferences import preferences

# Some useful notes on how to improve things:
# (not necessarily in this file, though!)
# to check if executable: os.access(path, os.X_OK)
# to expand PATH: os.environ['PATH'].split(os.path.pathsep)
# to find the Program Files dir on Windows:
# import _winreg
#key = _winreg.OpenKey(
#	_winreg.HKEY_LOCAL_MACHINE,
#	"Software\\Microsoft\\Windows\\CurrentVersion"
#	)
#value, type = _winreg.QueryValueEx(key, "ProgramFilesDir")
#print("Your Program Files dir is here: %s" % value)
# to check if we're on windows:
#if hasattr(sys, 'getwindowsversion'):
#	 print('Windows found')
#else:
#	print('Windows not found')

class ConfigDialog(object):

	def __init__(self):
		self.__configDialog = None
		self.__browseExecutableButton = None
		self.__execEdit = None

	def show(self, block = False):
		dialog = self.__configDialog
		if dialog is None:
			self.__configDialog = dialog = QtWidgets.QDialog(
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
			self.__browseExecutableButton.clicked.connect(self.__browseExec)
			self.__execEdit.editingFinished.connect(self.__setExec)
		if block:
			dialog.exec_()
		else:
			dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	def __setExec(self):
		preferences['system/executable'] = self.__execEdit.text()

	def __browseExec(self):
		path = QtWidgets.QFileDialog.getOpenFileName(
			self.__browseExecutableButton,
			'Select openMSX executable',
			QtCore.QDir.currentPath(),
			'All Files (*)'
			)
		if path:
			self.__execEdit.setText(path[0])
		self.__setExec()

configDialog = ConfigDialog()
