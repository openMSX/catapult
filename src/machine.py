from bisect import insort
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal, QModelIndex

from hardware import HardwareModel
from preferences import preferences

class MachineModel(HardwareModel):
	__columnKeys = 'manufacturer', 'code', 'type', 'working', 'description'
	_hardwareType = 'machine'
	_testable = True
	rowsInserted = pyqtSignal(QModelIndex, int, int)
	layoutChanged = pyqtSignal()

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

	def _startHardwareTest(self, machineId, name):
		self._bridge.sendCommandRaw('set err [catch { ' + machineId + \
			'::load_machine ' + name + ' } errmsg ] ; delete_machine ' + \
			machineId + ' ; if $err { error $errmsg }',
			lambda testdata: self._testDone(name, machineId, None, True),
			lambda message: self._testDone(name, machineId, message, False)
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
			] + [name, info]

		sortReversed = self.__sortReversed
		column = self.__sortColumn
		key = (sortRow[column], sortRow)
		# Unfortunately "bisect" does not offer a way to use a different
		# comparator, so we have to do binary search ourselves.
		low = 0
		high = len(self.__machines)
		while low < high:
			mid = (low + high) // 2
			machine = self.__machines[mid]
			if (key > (machine[column], machine)) != sortReversed:
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
			if role == QtCore.Qt.TextAlignmentRole:
				return QtCore.QVariant(QtCore.Qt.AlignLeft)

		return QtCore.QVariant()

	def data(self, index, role = QtCore.Qt.DisplayRole):
		if not index.isValid():
			return QtCore.QVariant()

		column = index.column()
		sortRow = self.__machines[index.row()]
		#print('data requested for', sortRow[-2], 'column', column, 'role', role)
		if role == QtCore.Qt.DisplayRole:
			key = self.__columnKeys[column]
			return QtCore.QVariant(sortRow[-1].get(key, ''))
		if role == QtCore.Qt.UserRole:
			return QtCore.QVariant(sortRow[-2]).value()
		if role == QtCore.Qt.ToolTipRole:
			key = self.__columnKeys[column]
			value = sortRow[-1].get(key)
			if key == 'working' and value == 'No':
				return QtCore.QVariant(sortRow[-1].get('brokenreason'))
			return QtCore.QVariant(value)

		return QtCore.QVariant()

	def sort(self, column, order = QtCore.Qt.AscendingOrder):
		self.__sortColumn = column
		# It seems (Py)Qt confuses ascending and descending, so we interpret
		# it the other way around, to be consistent with other apps.
		self.__sortReversed = order == QtCore.Qt.AscendingOrder

		self.__machines = [self.__allAscending]
		self.__machines.sort(
			key = lambda machine: machine[column],
			reverse = self.__sortReversed
			)

		self.layoutChanged.emit()

class MachineManager(QtCore.QObject):

	machineChanged = pyqtSignal(str)
	machineAdded = pyqtSignal(str)
	machineRemoved = pyqtSignal(str)

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
		self.__requestedWidths = [0] * model.columnCount()

		# Load history.
		for machine in preferences.getList('machine/history'):
			ui.machineBox.addItem(
				str(machine).replace('_', ' '), QtCore.QVariant(machine)
				)

		# Make connections.
		ui.machineBox.activated.connect(self.__machineSelected)
		ui.setAsDefaultButton.clicked.connect(self.__machineSetDefault)

		bridge.registerUpdatePrefix(
			'hardware', ('machine',), self.__updateHardware
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
		print(dataDir)
		if self.__userdir is None:
			self.__userdir = dataDir
		else:
			self.__systemdir = dataDir

	def __initialReply(self, machineId):
		self.machineAdded.emit(machineId)
		self.__updateMachineId(machineId)

	def __updateMachineId(self, machineId):
		print('ID of current machine:', machineId)
		self.__currentMachineId = machineId
		self.machineChanged.emit(machineId)
		self.__bridge.command('machine_info', 'config_name')(self.__machineChanged)

	def __updateHardware(self, machineId, _, event):
		print('Machine', machineId, ':', event)
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
			self.__machineDialog = dialog = QtWidgets.QDialog(
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
			horizontalHeader.setSectionsClickable(True)
			ui.machineTable.verticalHeader().hide()
			model = self.__model
			ui.machineTable.setModel(model)
			# for now hide the slideshow if not the openMSX-CD version.
			if not self.__parent.openmsxcd :
				ui.previewWidget.hide()
				#ui.slideshowWidget.hide()
			#else:
			#	#else load the DB stuff
			#	from pysqlite2 import dbapi2 as sqlite
			#	cursor = self.__cursor
			#	if cursor is None:
			#		connection = sqlite.connect('hwimages.db')
			#		self.__cursor = cursor = connection.cursor()

			# Make connections.
			dialog.accepted.connect(self.__machineDialogAccepted)
			horizontalHeader.sectionClicked.connect(
				ui.machineTable.sortByColumn
				)
			ui.refreshButton.clicked.connect(model.repopulate)
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
			ui.machineTable.selectionModel().currentChanged.connect(self.__machineHighlighted)
			# Fetch machine info.
			self.__model.repopulate()
		else:
			self.__setSelection()
		dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	def __machineHighlighted(self, current, _):
		self.__ui.okButton.setEnabled(True)
		self.__selectedMachineConfig = \
			self.__model.data(current, QtCore.Qt.UserRole)
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
			if self.__userdir is not None:
				print("XXX userdir")
				theDir = self.__userdir + "/machines/" + \
					str(self.__selectedMachineConfig) + \
					"/images"
				print(theDir)
				self.__ui.slideshowWidget.addImagesInDirectory(theDir)
				theDir = self.__userdir + "/images/" + \
					str(self.__selectedMachineConfig)
				print(theDir)
				self.__ui.slideshowWidget.findImagesForMedia(dir)
			if self.__systemdir is not None:
				print("XXX systemdir")
				theDir = self.__systemdir + "/machines/" + \
					str(self.__selectedMachineConfig) + \
					"/images"
				print(theDir)
				self.__ui.slideshowWidget.addImagesInDirectory(theDir)
				theDir = self.__systemdir + "/images/" + \
					str(self.__selectedMachineConfig)
				print(theDir)
				self.__ui.slideshowWidget.findImagesForMedia(theDir)
			print("XXX end images")

			#filenames = "/opt/openMSX/share/images/" + \
			#	str(self.__selectedMachineConfig).lower()
			#print("filenames => " + filenames)
			#self.__ui.slideshowWidget.findImagesForMedia(filenames)


	def __machineDialogAccepted(self):
		index = self.__ui.machineTable.currentIndex()
		machine = self.__model.data(index, QtCore.Qt.UserRole)
		self.__setMachine(machine)

	def __setMachine(self, machine):
		# Request machine change from openMSX.
		self.__bridge.command('machine', machine)(None,
			self.__machineChangeErrorHandler
			)

	def __machineChangeErrorHandler(self, message):
		messageBox =  QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
				'Problem changing machine:', message, QtWidgets.QMessageBox.Ok,
				self.__machineBox
				)
		messageBox.show()

	def __machineChanged(self, value):
		print('current machine:', value)
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
			if machineBox.itemData(index) == value:
				machineBox.removeItem(index)
			else:
				index += 1
		# Persist history.
		history = list()
		for index in range(machineBox.count()):
			history.append(machineBox.itemData(index))
		preferences['machine/history'] = history

	def __machineSelected(self, index):
		machine = self.__machineBox.itemData(index)
		print('selected machine:', machine)
		# TODO: Ask user for confirmation if current machine is different and
		#       currently powered on.
		self.__setMachine(machine)

	def __machinesAdded(self, _, start, end):
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
		machine = machineBox.itemData(machineBox.currentIndex())
		self.__bridge.command('set', 'default_machine', machine)()
