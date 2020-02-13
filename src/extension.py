# A quick hack of machine.py from mthuurne
# main differences:
#	- s/Machine/Extension/ in most places
#	- added the 'CLI-name'
# This still needs a lot of cleaning up
# There's an awful mixing of code for the extension Add dialog and for the
# extension part in the main view

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal, QModelIndex
from bisect import insort

from hardware import HardwareModel
#from preferences import preferences

class ExtensionModel(HardwareModel):
	__columnKeys = 'name', 'manufacturer', 'code', 'type', 'description'
	_hardwareType = 'extension'
	_testable = False # for now
	rowsInserted = pyqtSignal(QModelIndex, int, int)
	layoutChanged = pyqtSignal()

	def __init__(self, bridge):
		HardwareModel.__init__(self, bridge)
		self.__extensions = []
		self.__allAscending = []
		self.__sortColumn = 0
		self.__sortReversed = False

	def __str__(self):
		return 'ExtensionModel(%s)' % ', '.join(
			extension[-2] for extension in self.__extensions
			)

	def _startHardwareTest(self, machineId, name):
		raise NotImplementedError

	def find(self, extension):
		'''Searches for an extension with the given name.
		Returns the row on which the extension is found, or -1 if it is not found.
		'''
		for row, sortRow in enumerate(self.__extensions):
			if sortRow[-2] == extension:
				return row
		return -1

	def _clearItems(self):
		self.__extensions = []
		self.__allAscending = []

	def _storeItem(self, name, info):
		info.setdefault('code', name)
		sortRow = [
			info.get(key, '').lower() for key in self.__columnKeys
			] + [ name, info ]

		sortReversed = self.__sortReversed
		column = self.__sortColumn
		key = (sortRow[column], sortRow)
		# Unfortunately "bisect" does not offer a way to use a different
		# comparator, so we have to do binary search ourselves.
		low = 0
		high = len(self.__extensions)
		while low < high:
			mid = (low + high) // 2
			extension = self.__extensions[mid]
			if (key > (extension[column], extension)) != sortReversed:
				low = mid + 1
			else:
				high = mid
		rowNr = low

		self.__extensions.insert(rowNr, sortRow)
		insort(self.__allAscending, sortRow)

		#parent = QtCore.QModelIndex() # invalid model index
		parent = self.createIndex(rowNr, 0).parent()
		self.rowsInserted.emit(parent, rowNr, rowNr)

	def rowCount(self, parent = QtCore.QModelIndex()):
		# pylint: disable-msg=W0613
		return len(self.__extensions)

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
		sortRow = self.__extensions[index.row()]
		#print('data requested for', sortRow[-2], 'column', column, 'role', role)
		if role == QtCore.Qt.DisplayRole:
			key = self.__columnKeys[column]
			return QtCore.QVariant(sortRow[-1].get(key, ''))
		elif role == QtCore.Qt.UserRole:
			return QtCore.QVariant(sortRow[-2]).value()
		elif role == QtCore.Qt.ToolTipRole:
			key = self.__columnKeys[column]
			value = sortRow[-1].get(key)
			# TODO: uncomment when extension testing is implemented
			#if key == 'working' and value == 'No':
			#	return QtCore.QVariant(sortRow[-1].get('brokenreason'))
			#else:
			return QtCore.QVariant(value)


		return QtCore.QVariant()

	def sort(self, column, order = QtCore.Qt.AscendingOrder):
		self.__sortColumn = column
		# It seems (Py)Qt confuses ascending and descending, so we interpret
		# it the other way around, to be consistent with other apps.
		self.__sortReversed = order == QtCore.Qt.AscendingOrder

		self.__extensions = [self.__allAscending]
		self.__extensions.sort(key = lambda extension: extension[column])
		if self.__sortReversed:
			self.__extensions.reverse()

		self.layoutChanged.emit()

class ExtensionManager(QtCore.QObject):

	extensionChanged = pyqtSignal()

	def __init__(self, parent, ui, bridge):
		QtCore.QObject.__init__(self)
		self.__parent = parent
		self.__extensionList = ui.extensionList
		self.__extensionDialog = None
		self.__bridge = bridge
		self.__ui = ui
		self.__userdir = None
		self.__systemdir = None
		self.__model = model = ExtensionModel(bridge)
		self.__extensions = None
		self.__currentExtensionId = None
		self.__currentExtensionConfig = None
		self.__selectedExtensionConfig = None
		self.__requestedWidths = [ 0 ] * model.columnCount()

		## Load history.
		#for extension in preferences.getList('extension/history'):
		#	extensionBox.addItem(
		#		str(extension).replace('_', ' '), QtCore.QVariant(extension)
		#		)

		# Make connections.
		#extensionBox.activated.connect(self.__extensionSelected)
		ui.removeExtensionsButton.clicked.connect(self.__removeExtensions)

		bridge.registerUpdate(
			'extension', self.__updateExtension
		)
		# Query initial state.
		bridge.registerInitial(self.__queryInitial)


	def __queryInitial(self):
		'''Query initial state.
		'''
		bridge = self.__bridge
		#bridge.command('machine')(self.__updateMachineId)
		bridge.command('return','"$env(OPENMSX_USER_DATA)"')(self.__dirReply)
		bridge.command('return','"$env(OPENMSX_SYSTEM_DATA)"')(self.__dirReply)

	def __dirReply(self, dataDir):
		# we use the fact that the response will
		# come in the order they are requested
		print(dataDir)
		if self.__userdir == None:
			self.__userdir = dataDir
		else:
			self.__systemdir = dataDir

	def __removeExtensions(self):
		# Request extension remove from openMSX.
		extensions = self.__extensionList.selectedItems()
		for extension in extensions:
			self.__bridge.command('remove_extension', extension.text())()

	def __updateExtension(self, extension, machineId, event):
		print('Extension', extension, ':', event, '(on machine ', machineId, ')')
		# TODO: shouldn't we do something with the machineId?
		self.extensionChanged.emit()
		if event == 'add':
			self.__extensionList.addItem(extension)
		elif event == 'remove':
			widget = self.__extensionList
			widget.takeItem(widget.row(widget.findItems(
				extension,
				QtCore.Qt.MatchFixedString | QtCore.Qt.MatchCaseSensitive
				)[0]))

	def __disableRefreshButton(self):
		self.__ui.refreshButton.setEnabled(False)

	def __enableRefreshButton(self):
		self.__ui.refreshButton.setEnabled(True)

	def chooseExtension(self):
		self.__selectedExtensionConfig = self.__currentExtensionConfig
		dialog = self.__extensionDialog
		if dialog is None:
			self.__extensionDialog = dialog = QtWidgets.QDialog(
				self.__parent, QtCore.Qt.Dialog
				)
			# Setup UI made in Qt Designer.
			from ui_extension import Ui_Dialog
			self.__ui = ui = Ui_Dialog()
			ui.setupUi(dialog)
			horizontalHeader = ui.extensionTable.horizontalHeader()
			horizontalHeader.setSortIndicator(0, QtCore.Qt.DescendingOrder)
			horizontalHeader.setStretchLastSection(True)
			horizontalHeader.setSortIndicatorShown(True)
			horizontalHeader.setHighlightSections(False)
			horizontalHeader.setSectionsClickable(True)
			ui.extensionTable.verticalHeader().hide()
			model = self.__model
			ui.extensionTable.setModel(model)
			# for now hide the slideshow if not the openMSX-CD version.
			if not self.__parent.openmsxcd :
				ui.previewWidget.hide()
				#ui.slideshowWidget.hide()

			# Make connections.
			dialog.accepted.connect(self.__extensionDialogAccepted)
			horizontalHeader.sectionClicked.connect(
				ui.extensionTable.sortByColumn
				)
			ui.refreshButton.clicked.connect(model.repopulate)
			model.populating.connect(self.__disableRefreshButton)
			model.populated.connect(self.__enableRefreshButton)
			model.rowsInserted.connect(self.__extensionsAdded)
			model.layoutChanged.connect(self.__setSelection)
			model.populated.connect(
				# A queued connection is used because the table view needs some
				# time to process the added items before being able to scroll
				# to the currently selected one.
				self.__setSelection, QtCore.Qt.QueuedConnection
				)
			ui.extensionTable.selectionModel().currentChanged.connect(self.__extensionHighlighted)
			# Fetch extension info.
			self.__model.repopulate()
		else:
			self.__setSelection()
		dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	def __extensionHighlighted(self, current, previous):
		# pylint: disable-msg=W0613
		self.__ui.okButton.setEnabled(True)
		self.__selectedExtensionConfig = \
			self.__model.data(current, QtCore.Qt.UserRole)
		self.__ui.extensionTable.scrollTo(current)
		# Display images of this machine if we are in the openmsxcd version
		if self.__parent.openmsxcd :
			self.__ui.slideshowWidget.reset()

			#Use system and user dir to find images inside
			#the <dir>/machines/<selected-machine>/images/
			#or in the images pool
			#the <dir>/images/<selected-machine>*.(jpeg|jpg|gif|png)
			if not (self.__userdir == None):
				dir = self.__userdir + "/extensions/" + \
					str(self.__selectedExtensionConfig) + \
					"/images"
				print(dir)
				self.__ui.slideshowWidget.addImagesInDirectory(dir)
				dir = self.__userdir + "/images/" + \
					str(self.__selectedExtensionConfig)
				print(dir)
				self.__ui.slideshowWidget.findImagesForMedia(dir)
			if not (self.__systemdir == None):
				dir = self.__systemdir + "/extensions/" + \
					str(self.__selectedExtensionConfig) + \
					"/images"
				print(dir)
				self.__ui.slideshowWidget.addImagesInDirectory(dir)
				dir = self.__systemdir + "/images/" + \
					str(self.__selectedExtensionConfig)
				print(dir)
				self.__ui.slideshowWidget.findImagesForMedia(dir)


	def __extensionDialogAccepted(self):
		index = self.__ui.extensionTable.currentIndex()
		extension = self.__model.data(index, QtCore.Qt.UserRole)
		self.__setExtension(extension)

	def __setExtension(self, extension):
		# Request extension add from openMSX.
		self.__bridge.command('ext', extension)()

	def __extensionChanged(self, value):
		print('current extension:', value)
		self.__currentExtensionConfig = value
		# TODO: make extension history? Or save extensions for this machine?
		# Remove duplicates of the path from the history.
#		index = 1
#		while index < machineBox.count():
#			if machineBox.itemData(index) == value:
#				machineBox.removeItem(index)
#			else:
#				index += 1
#		# Persist history.
#		history = list()
#		for index in range(machineBox.count()):
#			history.append(machineBox.itemData(index))
#		preferences['machine/history'] = history

	def __extensionSelected(self, index):
		#print('selected index %d of combo box' % index)
		extension = self.__extensionBox.itemData(index)
		print('selected extension:', extension)
		# TODO: Ask user for confirmation if current extension is different and
		#       currently powered on.
		self.__setExtension(extension)

	def __extensionsAdded(self, parent, start, end): # pylint: disable-msg=W0613
		model = self.__model
		table = self.__ui.extensionTable
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
		row = model.find(self.__selectedExtensionConfig)
		if row != -1:
			table = self.__ui.extensionTable
			index = model.createIndex(row, 0)
			table.setCurrentIndex(index)
			table.scrollTo(index)
