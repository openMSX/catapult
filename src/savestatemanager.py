# $Id$

from PyQt4 import QtGui
from qt_utils import connect

class SaveStateManager(object):

	def __init__(self, bridge):
		self.__bridge = bridge
		
		self.__saveStateListWidget = None
		self.__newFileLineEdit = None
		self.__newFileWidget = None
		self.__deleteStateButton = None
		self.__saveStateButton = None
		self.__loadStateButton = None
		self.__cancelButton = None

		self.__saveStateDialog = dialog = QtGui.QDialog(
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

		connect(self.__cancelButton, 'clicked()', lambda: dialog.reject())
		connect(self.__deleteStateButton, 'clicked()', self.__delete)
		connect(self.__loadStateButton, 'clicked()', self.__load)
		connect(self.__saveStateButton, 'clicked()', self.__save)
		connect(self.__newFileLineEdit, 'returnPressed()', self.__save)

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
		self.__bridge.command('loadstate',
			self.__saveStateListWidget.currentItem().text()
			)(
				lambda dummy: self.__saveStateDialog.accept(),
				lambda message: self.__generalFailHandler(message, 'Problem loading state')
			)

	def __save(self):
		selected = self.__newFileLineEdit.text()
		if selected == '':
			currentItem =  self.__saveStateListWidget.currentItem()
			if currentItem == None:
				return
			selected = currentItem.text()
			if selected == '':
				return
			reply = QtGui.QMessageBox.question(
				self.__saveStateDialog,
				'Overwrite \"' + selected + '\"?',
				'<p>Overwrite save state \"' + selected + '\".</p><p>Are you sure?</p>',
				QtGui.QMessageBox.Yes,
				QtGui.QMessageBox.Cancel)
			if reply == QtGui.QMessageBox.Cancel:
				return
		self.__newFileLineEdit.clear()
		self.__bridge.command('savestate',
				selected
			)(
				lambda dummy: self.__refreshList(),
				lambda message: self.__generalFailHandler(message, 'Problem saving state')
			)

	def __generalFailHandler(self, message, title):
		messageBox = QtGui.QMessageBox(title, message,
			QtGui.QMessageBox.Warning, 0, 0, 0,
			self.__saveStateDialog
			)
		messageBox.show()
