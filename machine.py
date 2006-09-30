# $Id$

from PyQt4 import QtCore, QtGui
from qt_utils import QtSignal

class MachineManager(QtCore.QObject):

	def __init__(self, parent, machineBox, settingsManager):
		QtCore.QObject.__init__(self)
		self.__parent = parent
		self.__machineBox = machineBox
		#self.__bridge = bridge
		#self.__settingsManager = settingsManager
		self.__machineDialog = None

		# TODO: Load machine history from preferences.

		# Make connections.
		self.__machineSetting = machineSetting = settingsManager['machine']
		machineSetting.valueChanged.connect(self.__machineChanged)
		QtSignal(
			machineBox, 'activated', 'int'
			).connect(self.__machineSelected)

	def chooseMachine(self):
		dialog = self.__machineDialog
		if dialog is None:
			self.__machineDialog = dialog = QtGui.QDialog(
				self.__parent, QtCore.Qt.Dialog | QtCore.Qt.WindowTitleHint
				)
			# Setup UI made in Qt Designer.
			from ui_machine import Ui_Dialog
			ui = Ui_Dialog()
			ui.setupUi(dialog)
			# Make connections.
			# ...
		dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	def __machineChanged(self, value):
		print 'current machine:', value
		# TODO: Replace current item (edit text?) as well.
		machineBox = self.__machineBox
		machineBox.insertItem(
			0, str(value).replace('_', ' '), QtCore.QVariant(value)
			)
		machineBox.setCurrentIndex(0)
		# Remove duplicates of the path from the history.
		index = 1
		while index < machineBox.count():
			if machineBox.itemData(index).toString() == value:
				machineBox.removeItem(index)
			else:
				index += 1
		# TODO: Save machine history to preferences.

	def __machineSelected(self, index):
		#print 'selected index %d of combo box' % index
		machine = self.__machineBox.itemData(index).toString()
		print 'selected machine:', machine
		# TODO: Ask user for confirmation if current machine is different and
		#       currently powered on.
		self.__machineSetting.setValue(machine)
