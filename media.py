# $Id$

from PyQt4 import QtCore, QtGui

from preferences import preferences
from qt_utils import connect

def addToHistory(comboBox, path):
	# TODO: Do we really need this?
	if path == '':
		return
	topPath = comboBox.itemText(0)
	if topPath == '':
		comboBox.setItemText(0, path)
	elif path != topPath:
		comboBox.insertItem(0, path or '')
		comboBox.setCurrentIndex(0)

def parseMediaSlot(mediaSlot):
	'''Returns a tuple ( medium, identifier) that corresponds to the given
	media slot.
	'''
	if mediaSlot == 'cassetteplayer':
		return 'cassette', None
	else:
		return mediaSlot[ : -1], mediaSlot[-1]

class MediaSwitcher(QtCore.QObject):

	def __init__(self, ui, mediaModel):
		QtCore.QObject.__init__(self)
		self.__mediaModel = mediaModel 
		self.__ui = ui
		self.__mediaSlot = None
		self.__pageMap = {
			'cart': ( ui.cartPage, self.__updateCartPage ),
			'disk': ( ui.diskPage, self.__updateDrivePage ),
			'cassette': (
				ui.cassettePage, self.__updateCassettePage
				),
			'hd': ( ui.hdPage, self.__updateHarddiskPage ),
			'cd': ( ui.cdPage, self.__updateCDROMPage ),
			}
		self.__cartPageInited = False
		# Connect to media model:
		ui.mediaList.setModel(mediaModel)
		mediaModel.dataChanged.connect(self.mediaPathChanged)
		mediaModel.mediaSlotRemoved.connect(self.setInfoPage)
		# Connect view:
		connect(
			ui.mediaList.selectionModel(),
			'currentChanged(QModelIndex, QModelIndex)',
			self.updateMedia
			)
		connect(
			ui.mediaList, 'doubleClicked(QModelIndex)',
			self.browseMedia
			)
		# Connect signals of media panels:
		# It is essential to keep the references, otherwise the classes are
		# garbage collected even though they have signal-slot connections
		# attached to them.
		self.__handlers = [
			handler(ui, self)
			for handler in ( DiskHandler, CartHandler,
				CassetteHandler, HarddiskHandler, CDROMHandler )
			]

	def __updateCartPage(self, mediaSlot, identifier):
		ui = self.__ui
		path = self.__mediaModel.getInserted(mediaSlot)

		ui.cartLabel.setText('Cartridge Slot %s' % identifier.upper())

		fileInfo = QtCore.QFileInfo(path)

		if path == '':
			description = 'No cartridge in slot'
		elif fileInfo.isFile():
			lastDot = path.rfind('.')
			if lastDot == -1:
				ext = None
			else:
				ext = path[lastDot + 1 : ].lower()
			if ext in ('rom', 'ri'):
				description = 'ROM image'
				size = fileInfo.size()
				if size != 0:
					description += ' of %dkB' % (size / 1024)
					megabits = size / 1024 / 128
					if megabits == 1:
						description += ' (MegaROM)'
					elif megabits > 1:
						description += ' (%d MegaROM)' % megabits
			elif ext in ('zip', 'gz'):
				description = 'Compressed ROM image'
			else:
				description = 'ROM image of unknown type'
		elif fileInfo.exists():
			description = 'Special file node'
		else:
			description = 'Not found'
		ui.cartDescriptionLabel.setText(description)

		ui.cartHistoryBox.lineEdit().setText(path)
		
		if not self.__cartPageInited:
			# the next query might be empty, if it happens too soon
			mapperTypes = self.__mediaModel.getRomTypes()
			if len(mapperTypes) != 0:
				self.__cartPageInited = True 
				ui.mapperTypeCombo.addItem('Auto Detect')
				for item in mapperTypes:
					ui.mapperTypeCombo.addItem(QtCore.QString(item))
			else:
				print 'Interesting! We are preventing a race\
					condition here!'

	def __updateDrivePage(self, mediaSlot, identifier):
		ui = self.__ui
		path = self.__mediaModel.getInserted(mediaSlot)
		fileInfo = QtCore.QFileInfo(path)

		ui.diskLabel.setText('Disk Drive %s' % identifier.upper())

		if path == '':
			description = 'No disk in drive'
		elif fileInfo.isDir():
			description = 'Directory as disk (%d entries)' % (
				fileInfo.dir().count()
				)
		elif fileInfo.isFile():
			lastDot = path.rfind('.')
			if lastDot == -1:
				ext = None
			else:
				ext = path[lastDot + 1 : ].lower()
			if ext in ('dsk', 'di1', 'di2'):
				description = 'Raw disk image'
				size = fileInfo.size()
				if size != 0:
					description += ' of %dkB' % (size / 1024)
			elif ext in ('xsa', 'zip', 'gz'):
				description = 'Compressed disk image'
			else:
				description = 'Disk image of unknown type'
		elif fileInfo.exists():
			description = 'Special file node'
		else:
			description = 'Not found'
		ui.diskDescriptionLabel.setText(description)
		# TODO: Display "(read only)" in description label if the disk is
		#       read only for some reason:
		#       - image type that openMSX cannot write (XSA)
		#       - image file that is read-only on host file system
		#       I guess it's best if openMSX detects and reports this.
		#       The "diskX" commands return a flag "readonly", but updates
		#       do not include flags.

		ui.diskHistoryBox.lineEdit().setText(path)

	def __updateHarddiskPage(self, mediaSlot, identifier):
		ui = self.__ui
		path = self.__mediaModel.getInserted(mediaSlot)
		fileInfo = QtCore.QFileInfo(path)

		ui.hdLabel.setText('Hard Disk Drive %s' % identifier.upper())

		if path == '':
			description = 'No hard disk in drive'
		elif fileInfo.isFile():
			lastDot = path.rfind('.')
			if lastDot == -1:
				ext = None
			else:
				ext = path[lastDot + 1 : ].lower()
			if ext == 'dsk':
				description = 'Raw hard disk image'
				size = fileInfo.size()
				if size != 0:
					description += ' of %dMB' % (size / 1024 / 1024)
			elif ext in ('zip', 'gz'):
				description = 'Compressed hard disk image'
			else:
				description = 'Hard disk image of unknown type'
		elif fileInfo.exists():
			description = 'Special file node'
		else:
			description = 'Not found'
		ui.hdDescriptionLabel.setText(description)
		# TODO: Display "(read only)" in description label if the hd is
		#       read only for some reason:
		#       - image file that is read-only on host file system
		#       I guess it's best if openMSX detects and reports this.
		#       The "hdX" commands return a flag "readonly", but updates
		#       do not include flags.

		ui.hdHistoryBox.lineEdit().setText(path)

	def __updateCDROMPage(self, mediaSlot, identifier):
		ui = self.__ui
		path = self.__mediaModel.getInserted(mediaSlot)
		fileInfo = QtCore.QFileInfo(path)

		ui.cdLabel.setText('CD-ROM Drive %s' % identifier.upper())

		if path == '':
			description = 'No CD-ROM in drive'
		elif fileInfo.isFile():
			lastDot = path.rfind('.')
			if lastDot == -1:
				ext = None
			else:
				ext = path[lastDot + 1 : ].lower()
			if ext == 'iso':
				description = 'ISO CD-ROM image'
				size = fileInfo.size()
				if size != 0:
					description += ' of %dMB' % (size / 1024 / 1024)
			elif ext in ('zip', 'gz'):
				description = 'Compressed CD-ROM image'
			else:
				description = 'CD-ROM image of unknown type'
		elif fileInfo.exists():
			description = 'Special file node'
		else:
			description = 'Not found'
		ui.cdDescriptionLabel.setText(description)

		ui.cdHistoryBox.lineEdit().setText(path)

	def __updateCassettePage(self, mediaSlot, identifier
		# identifier is ignored for cassetteplayer:
		# pylint: disable-msg=W0613
		):
		ui = self.__ui
		path = self.__mediaModel.getInserted(mediaSlot)
		fileInfo = QtCore.QFileInfo(path)

		ui.cassetteLabel.setText('Cassette Player') # this could also be removed

		if path == '':
			description = 'No cassette in player'
		elif fileInfo.isFile():
			lastDot = path.rfind('.')
			if lastDot == -1:
				ext = None
			else:
				ext = path[lastDot + 1 : ].lower()
			if ext == 'cas':
				description = 'Cassette image in CAS format'
			elif ext == 'wav':
				description = 'Raw cassette image'
			elif ext in ('zip', 'gz'):
				description = 'Compressed cassette image'
			else:
				description = 'Cassette image of unknown type'
		elif fileInfo.exists():
			description = 'Special file node'
		else:
			description = 'Not found'
		ui.cassetteDescriptionLabel.setText(description)

		ui.cassetteHistoryBox.lineEdit().setText(path)

	def __updateMediaPage(self, mediaSlot):
		medium, identifier = parseMediaSlot(mediaSlot)
		# Look up page widget and update method for this medium.
		page, updater = self.__pageMap[medium]
		# Initialise the UI page for this medium.
		updater(mediaSlot, identifier)
		return page

	@QtCore.pyqtSignature('QModelIndex')
	def updateMedia(self, index):
		# Find out which media entry has become active.
		mediaSlot = str(index.data(QtCore.Qt.UserRole).toString())
		#print "***********"
		#print "mediaslot has currently become active:"
		#print mediaSlot
		if self.__mediaSlot == mediaSlot:
			return
		#quick hack to ignore VIRTUAL_DRIVE selection
		# TODO: find out how to register virtual drive as slot but not
		# display it in the selection list
		if  mediaSlot == 'virtual_drive':
			return
		self.__mediaSlot = mediaSlot
		page = self.__updateMediaPage(mediaSlot)
		# Switch page.
		self.__ui.mediaStack.setCurrentWidget(page)

	@QtCore.pyqtSignature('QModelIndex')
	def browseMedia(self, index):
		# Find out which media entry has become active.
		mediaSlot = str(index.data(QtCore.Qt.UserRole).toString())
		#quick hack to ignore VIRTUAL_DRIVE selection
		# TODO: find out how to register virtual drive as slot but not
		# display it in the selection list
		if  mediaSlot == 'virtual_drive':
			return
		medium, identifier_ = parseMediaSlot(mediaSlot)
		for handler in self.__handlers:
			if handler.medium == medium:
				handler.browseImage()
				break
		else:
			print 'no handler found for medium "%s"' % medium

	@QtCore.pyqtSignature('QModelIndex, QModelIndex')
	def mediaPathChanged(
		self, topLeft, bottomRight
		# pylint: disable-msg=W0613
		# TODO: We use the fact that we know MediaModel will only mark
		# one item changed at a time. This is not correct in general.
		):
		index = topLeft
		mediaSlot = str(index.data(QtCore.Qt.UserRole).toString())
		if self.__mediaSlot == mediaSlot:
			self.__updateMediaPage(mediaSlot)

	def setInfoPage(self):
		# TODO : this is called for each media hardware that is added or removed, 
		# since switching machines will sent this event for each and 
		# every drive/hd/cd/... this will be called several times in a row
		# do we need to handel this in a better way ?
		self.__ui.mediaStack.setCurrentWidget(self.__ui.infoPage)
		self.__ui.mediaList.selectionModel().clear()


	def setPath(self, path, *options):
		'''Sets a new path for the currently selected medium.
		'''
		self.__mediaModel.setInserted(self.__mediaSlot, path,
			lambda message: self.__mediaChangeErrorHandler(
				self.__mediaSlot, message
				)
				, *options
			)

	def __mediaChangeErrorHandler(self, mediaSlot, message):
		messageBox = QtGui.QMessageBox('Media change problem', message,
			QtGui.QMessageBox.Warning, 0, 0, 0,
			self.__ui.centralwidget
			)
		messageBox.show()
		self.__mediaModel.queryMedium(mediaSlot)

class MediaHandler(QtCore.QObject):
	medium = None
	browseTitle = None
	imageSpec = None

	def __init__(self, ui, switcher):
		QtCore.QObject.__init__(self)
		self._ui = ui
		self._switcher = switcher

		# Look up UI elements.
		self._ejectButton = getattr(ui, self.medium + 'EjectButton', None)
		self._browseButton = getattr(ui, self.medium + 'BrowseImageButton')
		self._historyBox = getattr(ui, self.medium + 'HistoryBox')

		# Load history.
		history = preferences.getList(self.medium + '/history')
		self._historyBox.addItems(history)
		# On OS X, the top item of the history is automatically put into
		# the edit box; this is not what we want, so we clear it.
		self._historyBox.clearEditText()

		# Connect signals.
		if (self._ejectButton):
			connect(self._ejectButton, 'clicked()', self.eject)
		connect(self._browseButton, 'clicked()', self.browseImage)
		connect(self._historyBox, 'activated(QString)', self.insert)
		connect(self._historyBox.lineEdit(), 'editingFinished()', self.edited)

	def insert(self, path):
		'''Tells the model to insert a new medium with the given path.
		'''
		print 'selected:', path or '<nothing>'
		if not path:
			return

		historyBox = self._historyBox
		# Insert path at the top of the list.
		historyBox.insertItem(0, path)
		historyBox.setCurrentIndex(0)
		# Remove duplicates of the path from the history.
		index = 1
		while index < historyBox.count():
			if historyBox.itemText(index) == path:
				historyBox.removeItem(index)
			else:
				index += 1

		# Update the model.
		self._switcher.setPath(str(path))

		# Persist history.
		history = QtCore.QStringList()
		for index in range(historyBox.count()):
			history.append(historyBox.itemText(index))
		preferences[self.medium + '/history'] = history

	def eject(self):
		'''Removes the currently inserted medium.
		'''
		self._historyBox.clearEditText()
		self._switcher.setPath('')

	def edited(self):
		'''Inserts the medium specified in the combobox line edit.
		'''
		self.insert(self._historyBox.lineEdit().text())

	def browseImage(self):
		self.insert(QtGui.QFileDialog.getOpenFileName(
			self._ui.mediaStack, self.browseTitle,
			self._historyBox.itemText(0) or QtCore.QDir.homePath(),
			self.imageSpec, None #, 0
			))

class DiskHandler(MediaHandler):
	medium = 'disk'
	browseTitle = 'Select Disk Image'
	imageSpec = 'Disk Images (*.dsk *.di? *.xsa *.zip *.gz);;All Files (*)'

	def __init__(self, ui, switcher):
		MediaHandler.__init__(self, ui, switcher)

		# Look up UI elements.
		self._browseDirButton = ui.diskBrowseDirectoryButton

		# Connect signals.
		connect(self._browseDirButton, 'clicked()', self.browseDirectory)

	def browseDirectory(self):
		self.insert(QtGui.QFileDialog.getExistingDirectory(
			self._ui.mediaStack, 'Select Directory',
			self._historyBox.itemText(0) or QtCore.QDir.homePath()
			))

class CartHandler(MediaHandler):
	medium = 'cart'
	browseTitle = 'Select ROM Image'
	imageSpec = 'ROM Images (*.rom *.ri *.zip *.gz);;All Files (*)'
	mapperType = 'Auto Detect'

	def __init__(self, ui, switcher):
		MediaHandler.__init__(self, ui, switcher)

		# Look up UI elements.
		self._mapperTypeCombo = ui.mapperTypeCombo

		# Connect signals.
		connect(self._mapperTypeCombo, 'activated(QString)', 
			self.__mapperTypeSelected)
	
	def __mapperTypeSelected(self, mapperType):
		# reinsert to set the mappertype
		self.mapperType = mapperType
		path = self._historyBox.currentText()
		self._switcher.setPath('')
		self.insert(path)

	def insert(self, path):
		'''Tells the model to insert a new cart with the given path.
		'''
		# TODO: remove code duplication with base class
		print 'selected:', path or '<nothing>'
		if not path:
			return

		historyBox = self._historyBox
		# Insert path at the top of the list.
		historyBox.insertItem(0, path)
		historyBox.setCurrentIndex(0)
		# Remove duplicates of the path from the history.
		index = 1
		while index < historyBox.count():
			if historyBox.itemText(index) == path:
				historyBox.removeItem(index)
			else:
				index += 1

		# Update the model.
		if (self.mapperType == 'Auto Detect'):
			self._switcher.setPath(str(path))
		else:
			self._switcher.setPath(str(path), '-romtype', 
				self.mapperType)

		# Persist history.
		history = QtCore.QStringList()
		for index in range(historyBox.count()):
			history.append(historyBox.itemText(index))
		preferences[self.medium + '/history'] = history

		# TODO: persist history of mapperTypes with carts

class CassetteHandler(MediaHandler):
	medium = 'cassette'
	browseTitle = 'Select Cassette Image'
	imageSpec = 'Cassette Images (*.cas *.wav *.zip *.gz);;All Files (*)'

class HarddiskHandler(MediaHandler):
	medium = 'hd'
	browseTitle = 'Select Hard Disk Image'
	imageSpec = 'Hard Disk Images (*.dsk *.zip *.gz);;All Files (*)'

class CDROMHandler(MediaHandler):
	medium = 'cd'
	browseTitle = 'Select CD-ROM Image'
	imageSpec = 'CD-ROM Images (*.iso *.zip *.gz);;All Files (*)'
