# $Id$

from PyQt4 import QtCore, QtGui
from qt_utils import QtSignal, Signal
from preferences import preferences

class MachineModel(QtCore.QAbstractTableModel):
	__columnKeys = 'manufacturer', 'code', 'type', 'description'
	rowsInserted = Signal('QModelIndex', 'int', 'int')
	layoutChanged = Signal()

	def __init__(self):
		QtCore.QAbstractTableModel.__init__(self)
		self.__machines = []
		self.__allAscending = None

	def __str__(self):
		return 'MachineModel(%s)' % ', '.join([
			name for name, info_ in self.__machines
			])

	def addMachine(self, name, info):
		rowNr = len(self.__machines)
		parent = QtCore.QModelIndex() # invalid model index
		self.__machines.append(( name, info ))
		self.rowsInserted.emit(parent, rowNr, rowNr)

	def rowCount(self, parent = QtCore.QModelIndex()):
		# pylint: disable-msg=W0613
		return len(self.__machines)

	def columnCount(self, parent = QtCore.QModelIndex()):
		# pylint: disable-msg=W0613
		return len(self.__columnKeys)

	def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
		if orientation == QtCore.Qt.Horizontal:
			if role == QtCore.Qt.DisplayRole:
				return QtCore.QVariant(self.__columnKeys[section].capitalize())
			elif role == QtCore.Qt.TextAlignmentRole:
				return QtCore.QVariant(QtCore.Qt.AlignLeft)

		return QtCore.QVariant()

	def data(self, index, role = QtCore.Qt.DisplayRole):
		if not index.isValid():
			return QtCore.QVariant()

		column = index.column()
		machine = self.__machines[index.row()]
		#print 'data requested for', machine[0], 'column', column, 'role', role
		if role == QtCore.Qt.DisplayRole:
			key = self.__columnKeys[column]
			return QtCore.QVariant(machine[1][key])
		elif role == QtCore.Qt.UserRole:
			return QtCore.QVariant(machine[0])

		return QtCore.QVariant()

	def sort(self, column, order = QtCore.Qt.AscendingOrder):
		print 'sort', column, order

		# TODO: Do this when last machine reply is in.
		if self.__allAscending is None:
			# Sort in ascending order, with first column as primary key,
			# second column as secondary key etc.
			# By using this as a base, we only have to re-sort once when the
			# primary sort key changes.
			self.__allAscending = list(self.__machines)
			for index in range(len(self.__columnKeys)):
				key = self.__columnKeys[-(index + 1)]
				self.__allAscending.sort(
					lambda m1, m2: cmp(m1[1][key].lower(), m2[1][key].lower())
					)

		self.__machines = list(self.__allAscending)
		key = self.__columnKeys[column]
		self.__machines.sort(
			lambda m1, m2: cmp(m1[1][key].lower(), m2[1][key].lower())
			)
		# It seems (Py)Qt confuses ascending and descending, so we interpret
		# it the other way around, to be consistent with other apps.
		if order == QtCore.Qt.AscendingOrder:
			self.__machines.reverse()

		self.layoutChanged.emit()

class MachineManager(QtCore.QObject):

	def __init__(self, parent, machineBox, settingsManager, bridge):
		QtCore.QObject.__init__(self)
		self.__parent = parent
		self.__machineBox = machineBox
		self.__bridge = bridge
		#self.__settingsManager = settingsManager
		self.__machineDialog = None
		self.__ui = None
		self.__model = MachineModel()
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
				self.__parent, QtCore.Qt.Dialog
				)
			# Setup UI made in Qt Designer.
			from ui_machine import Ui_Dialog
			self.__ui = ui = Ui_Dialog()
			ui.setupUi(dialog)
			horizontalHeader = ui.machineTable.horizontalHeader()
			horizontalHeader.setSortIndicator(0, QtCore.Qt.DescendingOrder)
			horizontalHeader.setStretchLastSection(True)
			horizontalHeader.setSortIndicatorShown(True)
			horizontalHeader.setHighlightSections(False)
			horizontalHeader.setClickable(True)
			ui.machineTable.verticalHeader().hide()
			ui.machineTable.setModel(self.__model)
			# Make connections.
			QtSignal(
				dialog, 'accepted'
				).connect(self.__machineDialogAccepted)
			QtSignal(
				horizontalHeader, 'sectionClicked', 'int'
				).connect(ui.machineTable.sortByColumn)
			# This is a slot rather than a signal, so we connect it by
			# overriding the method implementation.
			ui.machineTable.currentChanged = self.__machineHighlighted
			# Ask openMSX for list of machines.
			self.__bridge.command(
				'openmsx_info', 'machines'
				)(self.__machineListReply)
		dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	def __machineHighlighted(self, current, previous):
		# pylint: disable-msg=W0613
		self.__ui.okButton.setEnabled(True)

	def __machineDialogAccepted(self):
		index = self.__ui.machineTable.currentIndex()
		machine = self.__model.data(index, QtCore.Qt.UserRole).toString()
		self.__machineSetting.setValue(machine)

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
			# Note: The request is done in a separate method, so the current
			#       value of "machine" is passed rather than this method's
			#       context in which "machine" is changing each iteration.
			self.__requestMachineInfo(machine)

	def __requestMachineInfo(self, machine):
		# TODO: Add support for registerable error handlers, so we can
		#       catch errors when executing these commands.
		self.__bridge.command(
			'openmsx_info', 'machines', machine
			)(lambda *info: self.__machineInfoReply(machine, info))

	def __machineInfoReply(self, name, info):
		machineTable = self.__ui.machineTable
		infodict = dict([ info[i : i + 2] for i in xrange(0, len(info), 2) ])
		self.__model.addMachine(name, infodict)
		if self.__model.rowCount() == len(self.__machines):
			machineTable.resizeColumnsToContents()
			#for column in range(4):
				#machineTable.resizeColumnToContents(column)

