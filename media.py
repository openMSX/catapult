# $Id$

from PyQt4 import QtCore, QtGui
from bisect import bisect
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
		bridge.registerUpdate('hardware', self.__updateHardware)

	def __updateAll(self):
		# TODO: The idea of the name "updateAll" was to be able to deal with
		#       openMSX crashes. So, we should go back to knowing nothing about
		#       the openMSX state.
		#self.__mediaSlots = []
		for pattern in ( 'cart?', 'disk?', 'cassetteplayer' ):
			# Query medium slots.
			self.__bridge.command('info', 'command', pattern)(
				self.__mediumListReply
				)

	def __mediumListReply(self, *slots):
		'''This method is called to list the initial media slots of a
		particular type.
		'''
		if len(slots) == 0:
			return
		for medium in ( 'cart', 'disk', 'cassette' ):
			if slots[0].startswith(medium):
				break
		else:
			print 'media slot "%s" not recognised' % slots[0]
			return
		for slot in slots:
			self.__mediaSlotAdded(slot)

	def __mediaSlotAdded(self, slot):
		newEntry = ( slot, None )
		index = bisect(self.__mediaSlots, newEntry)
		parent = QtCore.QModelIndex() # invalid model index
		self.beginInsertRows(parent, index, index)
		self.__mediaSlots.insert(index, newEntry)
		self.endInsertRows()
		self.__bridge.command(slot)(self.__mediumReply)

	def __mediaSlotRemoved(self, slot):
		index = bisect(self.__mediaSlots, ( slot, ))
		if 0 <= index < len(self.__mediaSlots) \
		and self.__mediaSlots[index][0] == slot:
			parent = QtCore.QModelIndex() # invalid model index
			self.beginRemoveRows(parent, index, index)
			del self.__mediaSlots[index]
			self.endRemoveRows()
		else:
			print 'removed slot "%s" did not exist' % slot

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

	def __updateHardware(self, hardware, action):
		for medium in ( 'cart', 'disk', 'cassette' ):
			if hardware.startswith(medium):
				break
		else:
			print 'received update for unknown hardware "%s"' % hardware
			return
		if action == 'add':
			self.__mediaSlotAdded(hardware)
		elif action == 'remove':
			self.__mediaSlotRemoved(hardware)
		else:
			print 'received update for unsupported action "%s" for ' \
				'hardware "%s".' % ( action, hardware )

	def __mediumReply(self, mediaSlot, path, flags):
		print 'media update %s to "%s" flags "%s"' % ( mediaSlot, path, flags )
		if mediaSlot[-1] == ':':
			mediaSlot = mediaSlot[ : -1]
		else:
			print 'medium slot query reply does not start with "<medium>:", '\
				'but with "%s"' % mediaSlot
			return
		# TODO: Do something with the flags.
		self.__updateMedium(mediaSlot, path)

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

		# Look up UI elements.
		self._ejectButton = getattr(ui, self.medium + 'EjectButton')
		self._browseButton = getattr(ui, self.medium + 'BrowseImageButton')
		self._historyBox = getattr(ui, self.medium + 'HistoryBox')

		# Load history.
		history = preferences.getList(self.medium + '/history')
		if history is not None:
			self._historyBox.addItems(history)
			# On OS X, the top item of the history is automatically put into
			# the edit box; this is not what we want, so we clear it.
			self._historyBox.clearEditText()

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
		self._browseDirButton = getattr(ui, 'diskBrowseDirectoryButton')

		# Connect signals.
		QtSignal(self._browseDirButton, 'clicked').connect(self.browseDirectory)

	def browseDirectory(self):
		self.insert(QtGui.QFileDialog.getExistingDirectory(
			self._ui.mediaStack, 'Select Directory',
			self._historyBox.itemText(0) or QtCore.QDir.homePath()
			))

class CartHandler(MediaHandler):
	medium = 'cart'
	browseTitle = 'Select ROM Image'
	imageSpec = 'ROM Images (*.rom *.ri *.zip *.gz);;All Files (*)'

class CassetteHandler(MediaHandler):
	medium = 'cassette'
	browseTitle = 'Select Cassette Image'
	imageSpec = 'Cassette Images (*.cas *.wav *.zip *.gz);;All Files (*)'

