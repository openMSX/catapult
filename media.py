# $Id$

from PyQt4 import QtCore, QtGui
import os.path

from preferences import preferences
from qt_utils import QtSignal, Signal

class MediaModel(QtCore.QAbstractListModel):
	dataChanged = Signal('QModelIndex', 'QModelIndex')

	def __init__(self, bridge):
		QtCore.QAbstractListModel.__init__(self)
		self.__bridge = bridge
		self.__mediaSlots = []
		bridge.registerInitial(self.__updateAll)
		bridge.registerUpdate('media', self.__updateMedium)

	def __updateAll(self):
		# Query cartridge slots.
		self.__bridge.command('info', 'command', 'cart?')(self.__cartListReply)
		# Query disks.
		# TODO: The idea of the name "updateAll" was to be able to deal with
		#       openMSX crashes. However, that means we will have to resync
		#       the inserted media, not just the list of slots.
		self.__bridge.command('info', 'command', 'disk?')(self.__diskListReply)
		# Query cassetteplayer.
		self.__bridge.command(
			'info', 'command', 'cassetteplayer'
			)(self.__casListReply)

	def __setMedium(self, mediaSlot, path):
		index = 0
		for name, oldPath in self.__mediaSlots:
			if name == mediaSlot:
				if oldPath == path:
					return False
				else:
					print 'insert into %s: %s' % (name, path or '<empty>')
					self.__mediaSlots[index] = name, path
					modelIndex = self.createIndex(index, 0)
					self.dataChanged.emit(modelIndex, modelIndex)
					return True
			index += 1
		else:
			raise KeyError(mediaSlot)

	def __updateMedium(self, mediaSlot, path):
		try:
			self.__setMedium(mediaSlot, path)
		except KeyError:
			# This can happen if we don't monitor the creation of new media
			# slots.
			# TODO: Is that a temporary situation?
			print 'received update for non-existing media slot "%s"' % mediaSlot

	def __cartListReply(self, *carts):
		# TODO: Make sure this method is called every time when carts are
		#       added or removed.
		self.__listReply('cart', carts)

	def __diskListReply(self, *drives):
		# TODO: Make sure this method is called every time when drives are
		#       added or removed.
		self.__listReply('disk', drives)

	def __casListReply(self, *cassetteplayer):
		# TODO: Make sure this method is called every time when
		#       cassetteplayers are added or removed, if that is even
		#       possible.
		self.__listReply('cassette', cassetteplayer)

	def __listReply(self, medium, mediaSlots):
		# Determine which segment of the media slots list (which is sorted)
		# contains the given medium.
		first = None
		last = None
		index = 0
		for name, path_ in self.__mediaSlots:
			if name >= medium and first is None:
				first = index
			index += 1
			if name.startswith(medium):
				last = index
		if first is None:
			# name < medium throughout, so add at the end
			first = index
		if last is None:
			# no prefix matches, so segment of this medium is empty
			last = first

		# Prepare lists; append None as sentinel.
		oldSlots = [
			name for name, path_ in self.__mediaSlots[first : last]
			] + [ None ]
		newSlots = list(mediaSlots)
		newSlots.sort()
		newSlots.append(None)

		# Initialise iteration variables.
		# Note: index in self.__mediaSlots is at oldIndex + first.
		oldIndex = 0 # index in oldSlots
		oldSlot = oldSlots[oldIndex]
		newIndex = 0 # index in newSlots
		newSlot = newSlots[newIndex]

		# Merge the two sorted drive lists.
		parent = QtCore.QModelIndex() # invalid model index
		while not (oldSlot is None and newSlot is None):
			# Remove old drives that no longer occur in the new list.
			oldStart = oldIndex
			while (oldSlot is not None) and (
				newSlot is None or oldSlot < newSlot
				):
				oldIndex += 1
				oldSlot = oldSlots[oldIndex]
			if oldStart != oldIndex:
				self.beginRemoveRows(parent, oldStart, oldIndex - 1)
				del self.__mediaSlots[first + oldStart : first + oldIndex]
				del oldSlots[oldStart : oldIndex]
				self.endInsertRows()
				oldIndex = oldStart

			# Preserve drives that exist in both lists.
			while oldSlot is not None and oldSlot == newSlot:
				oldIndex += 1
				oldSlot = oldSlots[oldIndex]
				newIndex += 1
				newSlot = newSlots[newIndex]

			# Insert new drives that don't occur in the old list.
			newStart = newIndex
			while (newSlot is not None) and (
				oldSlot is None or newSlot < oldSlot
				):
				newIndex += 1
				newSlot = newSlots[newIndex]
			if newStart != newIndex:
				oldStart = oldIndex
				oldIndex += newIndex - newStart
				insertedDrives = newSlots[newStart : newIndex]
				self.beginInsertRows(parent, oldStart, oldIndex - 1)
				self.__mediaSlots[first + oldStart : first + oldStart] = [
					( drive, None ) for drive in insertedDrives
					]
				oldSlots[oldStart : oldStart] = insertedDrives
				self.endInsertRows()
				for drive in insertedDrives:
					# TODO: Query current path from openMSX.
					self.__bridge.command(drive)(self.__diskReply)
					print 'query drive', drive

	def __diskReply(self, drive, path, flags):
		print 'disk update', drive, 'to', path, 'flags', flags
		if drive[-1] == ':':
			drive = drive[ : -1]
		else:
			print 'disk change reply does not start with "<disk>:", '\
				'but with "%s"' % drive
			return
		# TODO: Do something with the flags.
		self.__updateMedium(drive, path)

	def getInserted(self, mediaSlot):
		'''Returns the path of the medium currently inserted in the given slot.
		If the path is not yet known, None is returned.
		Raises KeyError if no media slot exists by the given name.
		'''
		for name, path in self.__mediaSlots:
			if name == mediaSlot:
				return path
		else:
			raise KeyError(mediaSlot)

	def setInserted(self, mediaSlot, path):
		'''Sets the path of the medium currently inserted in the given slot.
		Raises KeyError if no media slot exists by the given name.
		'''
		changed = self.__setMedium(mediaSlot, path)
		if changed:
			# TODO: Deal with errors (register callback/errback).
			if path == '':
				path = '-eject'
			self.__bridge.command(mediaSlot, path)()

	def rowCount(self, parent):
		# TODO: What does this mean?
		if parent.isValid():
			return 0
		else:
			return len(self.__mediaSlots)

	def data(self, index, role = QtCore.Qt.DisplayRole):
		if not index.isValid():
			return QtCore.QVariant()

		name, path = self.__mediaSlots[index.row()]
		if role == QtCore.Qt.DisplayRole:
			if name.startswith('cart'):
				description = 'Cartridge slot %s' % name[-1].upper()
			elif name.startswith('disk'):
				description = 'Disk drive %s' % name[-1].upper()
			elif name.startswith('cassette'):
				description = 'Cassette player'
			else:
				description = name.upper()
			if path:
				dirName, fileName = os.path.split(path)
				if fileName == '':
					fileName = dirName[dirName.rfind(os.path.sep) + 1 : ]
			else:
				fileName = '<empty>'
			return QtCore.QVariant(
				'%s: %s' % ( description, fileName )
				)
		elif role == QtCore.Qt.UserRole:
			return QtCore.QVariant(name)

		return QtCore.QVariant()

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

class MediaSwitcher(QtCore.QObject):

	def __init__(self, mediaModel, ui):
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
			}
		# Connect to media model:
		mediaModel.dataChanged.connect(self.mediaPathChanged)
		# Connect signals of media panels:
		# It is essential to keep the references, otherwise the classes are
		# garbage collected even though they have signal-slot connections
		# attached to them.
		self.__handlers = [
			handler(ui, self)
			for handler in ( DiskHandler, CartHandler, CassetteHandler )
			]

	def __updateCartPage(self, mediaSlot, identifier):
		ui = self.__ui
		path = self.__mediaModel.getInserted(mediaSlot)

		ui.cartLabel.setText('Cartridge %s' % identifier.upper())

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

	def __updateDrivePage(self, mediaSlot, identifier):
		ui = self.__ui
		path = self.__mediaModel.getInserted(mediaSlot)
		fileInfo = QtCore.QFileInfo(path)

		ui.diskLabel.setText('Drive %s' % identifier.upper())

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
		if mediaSlot == 'cassetteplayer':
			medium = 'cassette'
			identifier = None # is ignored for cassetteplayer
		else:
			medium = mediaSlot[ : -1]
			identifier = mediaSlot[-1]
		# Look up page widget and update method for this medium.
		page, updater = self.__pageMap[medium]
		# Initialise the UI page for this medium.
		updater(mediaSlot, identifier)
		return page

	#@QtCore.pyqtSignature('QModelIndex')
	def updateMedia(self, index):
		# Find out which media entry has become active.
		mediaSlot = str(index.data(QtCore.Qt.UserRole).toString())
		if self.__mediaSlot == mediaSlot:
			return
		self.__mediaSlot = mediaSlot
		page = self.__updateMediaPage(mediaSlot)
		# Switch page.
		self.__ui.mediaStack.setCurrentWidget(page)

	#@QtCore.pyqtSignature(QModelIndex, QModelIndex)
	def mediaPathChanged(
		self, topLeft, bottomRight
		# pylint: disable-msg=W0613
		# TODO: We use the fact that we know MediaModel will only mark one
		#       item changed at a time. This is not correct in general.
		):
		index = topLeft
		mediaSlot = str(index.data(QtCore.Qt.UserRole).toString())
		if self.__mediaSlot == mediaSlot:
			self.__updateMediaPage(mediaSlot)

	def setPath(self, path):
		'''Sets a new path for the currently selected medium.
		'''
		self.__mediaModel.setInserted(self.__mediaSlot, path)

class MediaHandler(QtCore.QObject):
	medium = None
	browseTitle = None
	imageSpec = None

	def __init__(self, ui, switcher):
		QtCore.QObject.__init__(self)
		self._ui = ui
		self._switcher = switcher
		self._mediumToImageDir = {
			'disk': preferences.value('dirs/initialdisk'),
			'cart': preferences.value('dirs/initialrom'),
			'cassette': preferences.value('dirs/initialcas'),
			}

		# Look up UI elements.
		self._ejectButton = getattr(ui, self.medium + 'EjectButton')
		self._browseButton = getattr(ui, self.medium + 'BrowseImageButton')
		self._historyBox = getattr(ui, self.medium + 'HistoryBox')

		# Connect signals.
		QtSignal(self._ejectButton, 'clicked').connect(self.eject)
		QtSignal(self._browseButton, 'clicked').connect(self.browseImage)
		QtSignal(self._historyBox, 'activated', 'QString').connect(self.insert)
		QtSignal(self._historyBox.lineEdit(), 'editingFinished').connect(
			self.edited
			)

	def insert(self, path):
		'''Tells the model to insert a new medium with the given path.
		'''
		self._switcher.setPath(str(path))

	def eject(self):
		'''Removes the currently inserted medium.
		'''
		# TODO: I think it looks strange to insert empty string (no medium)
		#       into the history.
		self._historyBox.clearEditText()
		self.insert('')

	def edited(self):
		'''Inserts the medium specified in the combobox line edit.
		'''
		self.insert(str(self._historyBox.lineEdit().text()))

	def browsed(self, path):
		'''Inserts the result of a browse dialog into the history combobox
		and informs openMSX.
		'''
		print 'selected:', path or '<empty>'
		self._historyBox.insertItem(0, path)
		self._historyBox.setCurrentIndex(0)
		self.insert(path)

	def browseImage(self):
		path = QtGui.QFileDialog.getOpenFileName(
			self._ui.mediaStack, self.browseTitle,
			# TODO: Remember previous path.
			#QtCore.QDir.currentPath(),
			self._mediumToImageDir.get(self.medium)
			or QtCore.QDir.currentPath(),
			self.imageSpec, None #, 0
			)
		if not path.isNull():
			self.browsed(path)

class DiskHandler(MediaHandler):
	medium = 'disk'
	browseTitle = 'Select Disk Image'
	imageSpec = 'Disk Images (*.dsk *.di? *.xsa *.zip *.gz);;All Files (*)'

	def __init__(self, ui, switcher):
		MediaHandler.__init__(self, ui, switcher)

		# Look up UI elements.
		self._browseDirButton = getattr(ui, 'diskBrowseDirectoryButton')

		# Connect signals.
		QtSignal(self._browseDirButton, 'clicked').connect(
			self.diskBrowseDirectory
			)

	def diskBrowseDirectory(self):
		directory = QtGui.QFileDialog.getExistingDirectory(
			self._ui.mediaStack, 'Select Directory',
			# TODO: Remember previous path.
			#QtCore.QDir.currentPath()
			preferences.value('dirs/initialdisk'),
			#QtGui.QFileDialog.Option()
			)
		if not directory.isNull():
			self.browsed(directory)

class CartHandler(MediaHandler):
	medium = 'cart'
	browseTitle = 'Select ROM Image'
	imageSpec = 'ROM Images (*.rom *.ri *.zip *.gz);;All Files (*)'

class CassetteHandler(MediaHandler):
	medium = 'cassette'
	browseTitle = 'Select Cassette Image'
	imageSpec = 'Cassette Images (*.cas *.wav *.zip *.gz);;All Files (*)'

