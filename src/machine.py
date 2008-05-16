# $Id$

from PyQt4 import QtCore, QtGui
from bisect import insort

from hardware import HardwareModel
from qt_utils import QtSignal, Signal, connect
from preferences import preferences

class MachineModel(HardwareModel):
	__columnKeys = 'manufacturer', 'code', 'type', 'description'
	_hardwareType = 'machine'
	rowsInserted = QtSignal('QModelIndex', 'int', 'int')
	layoutChanged = QtSignal()

	def __init__(self, bridge):
		HardwareModel.__init__(self, bridge)
		self.__machines = []
		self.__allAscending = []
		self.__sortColumn = 0
		self.__sortReversed = False

	def __str__(self):
		return 'MachineModel(%s)' % ', '.join(
			machine[-2] for machine in self.__machines
			)

	def find(self, machine):
		'''Searches for a machine with the given name.
		Returns the row on which the machine is found, or -1 if it is not found.
		'''
		for row, sortRow in enumerate(self.__machines):
			if sortRow[-2] == machine:
				return row
		return -1

	def _clearItems(self):
		self.__machines = []
		self.__allAscending = []

	def _storeItem(self, name, info):
		info.setdefault('code', name)
		sortRow = [
			info.get(key, '').lower() for key in self.__columnKeys
			] + [ name, info ]

		if self.__sortReversed:
			sortSign = -1
		else:
			sortSign = 1
		column = self.__sortColumn
		key = sortRow[column]
		# Unfortunately "bisect" does not offer a way to use a different
		# comparator, so we have to do binary search ourselves.
		low = 0
		high = len(self.__machines)
		while low < high:
			mid = (low + high) / 2
			machine = self.__machines[mid]
			if (cmp(key, machine[column]) or cmp(sortRow, machine)) == sortSign:
				low = mid + 1
			else:
				high = mid
		rowNr = low

		self.__machines.insert(rowNr, sortRow)
		insort(self.__allAscending, sortRow)

		#parent = QtCore.QModelIndex() # invalid model index
		parent = self.createIndex(rowNr, 0).parent()
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
		sortRow = self.__machines[index.row()]
		#print 'data requested for', sortRow[-2], 'column', column, 'role', role
		if role == QtCore.Qt.DisplayRole:
			key = self.__columnKeys[column]
			return QtCore.QVariant(sortRow[-1].get(key, ''))
		elif role == QtCore.Qt.UserRole:
			return QtCore.QVariant(sortRow[-2])

		return QtCore.QVariant()

	def sort(self, column, order = QtCore.Qt.AscendingOrder):
		self.__sortColumn = column
		# It seems (Py)Qt confuses ascending and descending, so we interpret
		# it the other way around, to be consistent with other apps.
		self.__sortReversed = order == QtCore.Qt.AscendingOrder

		self.__machines = list(self.__allAscending)
		self.__machines.sort(key = lambda machine: machine[column])
		if self.__sortReversed:
			self.__machines.reverse()

		self.layoutChanged.emit()

class MachineManager(QtCore.QObject):

	machineChanged = Signal('QString')
	machineAdded = Signal('QString')
	machineRemoved = Signal('QString')

	def __init__(self, parent, ui, bridge):
		QtCore.QObject.__init__(self)
		self.__parent = parent
		self.__machineBox = ui.machineBox
		self.__machineDialog = None
		self.__bridge = bridge
		self.__ui = None
#		self.__cursor = None
		self.__userdir = None
		self.__systemdir = None
		self.__model = model = MachineModel(bridge)
		self.__machines = None
		self.__currentMachineId = None
		self.__currentMachineConfig = None
		self.__selectedMachineConfig = None
		self.__requestedWidths = [ 0 ] * model.columnCount()

		# Load history.
		for machine in preferences.getList('machine/history'):
			ui.machineBox.addItem(
				str(machine).replace('_', ' '), QtCore.QVariant(machine)
				)

		# Make connections.
		connect(ui.machineBox, 'activated(int)', self.__machineSelected)
		connect(ui.setAsDefaultButton, 'clicked()', self.__machineSetDefault)

		bridge.registerUpdatePrefix(
			'hardware', ( 'machine', ), self.__updateHardware
			)
		# Query initial state.
		# and get data directories needed for images
		bridge.registerInitial(self.__queryInitial)

	def __queryInitial(self):
		'''Query initial state.
		'''
		bridge = self.__bridge
		bridge.command('machine')(self.__initialReply)
		bridge.command('return','"$env(OPENMSX_USER_DATA)"')(self.__dirReply)
		bridge.command('return','"$env(OPENMSX_SYSTEM_DATA)"')(self.__dirReply)
	
	def __dirReply(self, dataDir):
		# we use the fact that the response will
		# come in the order they are requested
		print "XXX"
		print dataDir
		if self.__userdir == None:
			self.__userdir = dataDir
		else:
			self.__systemdir = dataDir

	def __initialReply(self, machineId):
		self.machineAdded.emit(machineId)
		self.__updateMachineId(machineId)

	def __updateMachineId(self, machineId):
		print 'ID of current machine:', machineId
		self.__currentMachineId = machineId
		self.machineChanged.emit(machineId)
		self.__bridge.command('machine_info', 'config_name')(self.__machineChanged)

	def __updateHardware(self, machineId, dummy, event):
		print 'Machine', machineId, ':', event
		if event == 'select':
			self.__updateMachineId(machineId)
		elif event == 'add':
			self.machineAdded.emit(machineId)
		elif event == 'remove':
			self.machineRemoved.emit(machineId)

	def getCurrentMachineId(self):
#		assert self.__currentMachineId is not None, 'No current machine known yet!'
		return self.__currentMachineId

	def __disableRefreshButton(self):
		self.__ui.refreshButton.setEnabled(False)

	def __enableRefreshButton(self):
		self.__ui.refreshButton.setEnabled(True)

	def chooseMachine(self):
		self.__selectedMachineConfig = self.__currentMachineConfig
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
			model = self.__model
			ui.machineTable.setModel(model)
			# for now hide the slideshow if not the openMSX-CD version.
			if not self.__parent.openmsxcd :
				ui.slideshowWidget.hide()
			#else:
			#	#else load the DB stuff
			#	from pysqlite2 import dbapi2 as sqlite
			#	cursor = self.__cursor
			#	if cursor is None:
			#		connection = sqlite.connect('hwimages.db')
			#		self.__cursor = cursor = connection.cursor()

			# Make connections.
			connect(dialog, 'accepted()', self.__machineDialogAccepted)
			connect(
				horizontalHeader, 'sectionClicked(int)',
				ui.machineTable.sortByColumn
				)
			connect(ui.refreshButton, 'clicked()', model.repopulate)
			model.populating.connect(self.__disableRefreshButton)
			model.populated.connect(self.__enableRefreshButton)
			model.rowsInserted.connect(self.__machinesAdded)
			model.layoutChanged.connect(self.__setSelection)
			model.populated.connect(
				# A queued connection is used because the table view needs some
				# time to process the added items before being able to scroll
				# to the currently selected one.
				self.__setSelection, QtCore.Qt.QueuedConnection
				)
			# This is a slot rather than a signal, so we connect it by
			# overriding the method implementation.
			ui.machineTable.currentChanged = self.__machineHighlighted
			# Fetch machine info.
			self.__model.repopulate()
		else:
			self.__setSelection()
		dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	def __machineHighlighted(self, current, previous):
		# pylint: disable-msg=W0613
		self.__ui.okButton.setEnabled(True)
		self.__selectedMachineConfig = \
			self.__model.data(current, QtCore.Qt.UserRole).toString()
		self.__ui.machineTable.scrollTo(current)
		# Display images of this machine if we are in the openmsxcd version
		if self.__parent.openmsxcd :
			self.__ui.slideshowWidget.reset()
			#cursor = self.__cursor
			#cursor.execute('SELECT File FROM hwimages WHERE Hardware = \'' +
			#	str(self.__selectedMachineConfig) + "'" )
			#for row in cursor:
			#	self.__ui.slideshowWidget.findImagesForMedia(row[0])

			#Use system and user dir to find images inside
			#the <dir>/machines/<selected-machine>/images/
			#or in the images pool
			#the <dir>/images/<selected-machine>*.(jpeg|jpg|gif|png)
			if not (self.__userdir == None):
				print "XXX userdir"
				dir = self.__userdir + "/machines/" + \
					str(self.__selectedMachineConfig) + \
					"/images"
				print dir
				self.__ui.slideshowWidget.addImagesInDirectory(dir)
				dir = self.__userdir + "/images/" + \
					str(self.__selectedMachineConfig)
				print dir
				self.__ui.slideshowWidget.findImagesForMedia(dir)
			if not (self.__systemdir == None):
				print "XXX systemdir"
				dir = self.__systemdir + "/machines/" + \
					str(self.__selectedMachineConfig) + \
					"/images"
				print dir
				self.__ui.slideshowWidget.addImagesInDirectory(dir)
				dir = self.__systemdir + "/images/" + \
					str(self.__selectedMachineConfig)
				print dir
				self.__ui.slideshowWidget.findImagesForMedia(dir)
			print "XXX end images"

			#filenames = "/opt/openMSX/share/images/" + str(self.__selectedMachineConfig).lower()
			#print "filenames => " + filenames
			#self.__ui.slideshowWidget.findImagesForMedia(filenames)


	def __machineDialogAccepted(self):
		index = self.__ui.machineTable.currentIndex()
		machine = self.__model.data(index, QtCore.Qt.UserRole).toString()
		self.__setMachine(machine)

	def __setMachine(self, machine):
		# Request machine change from openMSX.
		self.__bridge.command('machine', machine)(None,
			self.__machineChangeErrorHandler
			)

	def __machineChangeErrorHandler(self, message):
		messageBox =  QtGui.QMessageBox('Problem changing machine:', message,
				QtGui.QMessageBox.Warning, 0, 0, 0,
				self.__machineBox
				)
		messageBox.show()

	def __machineChanged(self, value):
		print 'current machine:', value
		self.__currentMachineConfig = value
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
		machine = self.__machineBox.itemData(index).toString()
		print 'selected machine:', machine
		# TODO: Ask user for confirmation if current machine is different and
		#       currently powered on.
		self.__setMachine(machine)

	def __machinesAdded(self, parent, start, end): # pylint: disable-msg=W0613
		model = self.__model
		table = self.__ui.machineTable
		header = table.horizontalHeader()
		for row in range(start, end + 1):
			# Widen columns if new content is larger than requested size.
			for column in range(model.columnCount() - 1):
				requestedWidth = max(
					self.__requestedWidths[column],
					table.sizeHintForColumn(column)
					)
				index = model.createIndex(row, column)
				itemWidth = table.sizeHintForIndex(index).width() + 16
				if itemWidth > requestedWidth:
					self.__requestedWidths[column] = itemWidth
					header.resizeSection(column, itemWidth)

	def __setSelection(self):
		model = self.__model
		row = model.find(self.__selectedMachineConfig)
		if row != -1:
			table = self.__ui.machineTable
			index = model.createIndex(row, 0)
			table.setCurrentIndex(index)
			table.scrollTo(index)

	def __machineSetDefault(self):
		machineBox = self.__machineBox
		machine = machineBox.itemData(machineBox.currentIndex()).toString()
		self.__bridge.command('set', 'default_machine', machine)()

