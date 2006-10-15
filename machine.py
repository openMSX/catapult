# $Id$

from PyQt4 import QtCore, QtGui
from qt_utils import QtSignal
from preferences import preferences

class MachineManager(QtCore.QObject):

	def __init__(self, parent, machineBox, settingsManager, bridge):
		QtCore.QObject.__init__(self)
		self.__parent = parent
		self.__machineBox = machineBox
		self.__bridge = bridge
		#self.__settingsManager = settingsManager
		self.__machineDialog = None
		self.__ui = None
		self.__machines = None

		# Load history.
		for machine in preferences.getList('machine/history'):
			machineBox.addItem(
				str(machine).replace('_', ' '), QtCore.QVariant(machine)
				)

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
			self.__ui = ui = Ui_Dialog()
			ui.setupUi(dialog)
			ui.machineTable.horizontalHeader().setResizeMode(
				3, QtGui.QHeaderView.Stretch
				)
			ui.machineTable.verticalHeader().hide()
			# Make connections.
			QtSignal(
				ui.machineTable, 'itemSelectionChanged'
				).connect(self.__machineHighlighted)
			QtSignal(
				dialog, 'accepted'
				).connect(self.__machineDialogAccepted)
			#ui.machineTable.currentItemChanged.connect(self.__
			# ...
			# Ask openMSX for list of machines.
			self.__bridge.command(
				'openmsx_info', 'machines'
				)(self.__machineListReply)
		dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	def __machineHighlighted(self):
		self.__ui.okButton.setEnabled(True)

	def __machineDialogAccepted(self):
		row = self.__ui.machineTable.currentIndex().row()
		self.__machineSetting.setValue(self.__machines[row])

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
		# Persist history.
		history = QtCore.QStringList()
		for index in range(machineBox.count()):
			history.append(machineBox.itemData(index).toString())
		preferences['machine/history'] = history

	def __machineSelected(self, index):
		#print 'selected index %d of combo box' % index
		machine = self.__machineBox.itemData(index).toString()
		print 'selected machine:', machine
		# TODO: Ask user for confirmation if current machine is different and
		#       currently powered on.
		self.__machineSetting.setValue(machine)

	def __machineListReply(self, *machines):
		self.__machines = machines
		for machine in machines:
			self.__bridge.command(
				'openmsx_info', 'machines', machine
				)(self.__machineInfoReply)

	def __machineInfoReply(self, *info):
		machineTable = self.__ui.machineTable
		infodict = dict([ info[i : i + 2] for i in xrange(0, len(info), 2) ])
		row = machineTable.rowCount()
		machineTable.insertRow(row)
		for column, key in enumerate((
			'manufacturer', 'code', 'type', 'description'
			)):
			item = QtGui.QTableWidgetItem()
			item.setText(infodict[key])
			machineTable.setItem(row, column, item)
		if row == len(self.__machines) - 1:
			for column in range(3):
				machineTable.resizeColumnToContents(column)

