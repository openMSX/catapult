from PyQt4 import QtCore
from bisect import bisect
from openmsx_utils import tclEscape, EscapedStr
import os.path

from qt_utils import QtSignal, Signal

class MediaModel(QtCore.QAbstractListModel):
	dataChanged = QtSignal('QModelIndex', 'QModelIndex')
	mediumChanged = Signal('QString', 'QString')
	mediaSlotRemoved = Signal('QString')
	mediaSlotAdded = Signal('QString')

	def __init__(self, bridge):
		QtCore.QAbstractListModel.__init__(self)
		self.__bridge = bridge
		self.__mediaSlots = []
		self.__romTypes = []
		bridge.registerInitial(self.__updateAll)
		bridge.registerUpdate('media', self.__updateMedium)
		bridge.registerUpdatePrefix(
			'hardware',
			( 'virtual_drive', 'cart', 'disk', 'cassette', 'hd', 'cd' ),
			self.__updateHardware
			)

	def doUpdateAll(self):
		self.__updateAll()

	def __updateAll(self):
		# TODO: The idea of the name "updateAll" was to be able to deal with
		#       openMSX crashes. So, we should go back to knowing nothing about
		#       the openMSX state.
		#self.__mediaSlots = []
		for pattern in ( 'cart?', 'disk?', 'virtual_drive', 'cassetteplayer', 'hd?',
				'cd?' 
			       ):
			# Query medium slots.
			self.__bridge.command('info', 'command', pattern)(
				self.__mediumListReply
				)
		self.__bridge.command('openmsx_info', 'romtype')(self.__romTypeReply)

	def __romTypeReply(self, *romTypes):
		for romType in romTypes:
			self.__romTypes.append(romType)

	def __mediumListReply(self, *slots):
		'''Callback to list the initial media slots of a particular type.
		'''
		if len(slots) == 0:
			return
		for medium in ( 'virtual_drive', 'cart', 'disk', 'cassette', 'hd', 'cd' ):
			if slots[0].startswith(medium):
				break
		else:
			print 'media slot "%s" not recognised' % slots[0]
			return
		for slot in slots:
			self.__mediaSlotAdded(slot)

	def queryMedium(self, slot):
		'''Queries the medium info of the specified slot'''
		self.__bridge.command(slot)(self.__mediumReply)

	def __mediaSlotAdded(self, slot):
		newEntry = ( slot, None )
		index = bisect(self.__mediaSlots, newEntry)
		parent = QtCore.QModelIndex() # invalid model index
		self.beginInsertRows(parent, index, index)
		self.__mediaSlots.insert(index, newEntry)
		self.endInsertRows()
		self.mediaSlotAdded.emit(slot)
		self.queryMedium(slot)

	def __mediaSlotRemoved(self, slot):
		index = bisect(self.__mediaSlots, ( slot, ))
		if 0 <= index < len(self.__mediaSlots) \
		and self.__mediaSlots[index][0] == slot:
			parent = QtCore.QModelIndex() # invalid model index
			self.beginRemoveRows(parent, index, index)
			del self.__mediaSlots[index]
			self.endRemoveRows()
			self.mediaSlotRemoved.emit(slot)
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
			if self.__setMedium(mediaSlot, path):
				self.mediumChanged.emit(mediaSlot, path)
		except KeyError:
			# This can happen if we don't monitor the creation of new media
			# slots.
			# TODO: Is that a temporary situation?
			print 'received update for non-existing media slot "%s"' % mediaSlot

	def __updateHardware(self, hardware, action):
		if action == 'add':
			self.__mediaSlotAdded(hardware)
		elif action == 'remove':
			self.__mediaSlotRemoved(hardware)
		else:
			print 'received update for unsupported action "%s" for ' \
				'hardware "%s".' % ( action, hardware )

	def __mediumReply(self, mediaSlot, path, flags = ''):
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

	def setInserted(self, mediaSlot, path, errorHandler, *options):
		'''Sets the path of the medium currently inserted in the given slot.
		Raises KeyError if no media slot exists by the given name.
		'''
		changed = self.__setMedium(mediaSlot, path)
		if changed:
			if path == '':
				self.__bridge.command(mediaSlot, 'eject')(
					None, errorHandler
					)
			else:
				self.__bridge.command(mediaSlot, 'insert',
					EscapedStr(tclEscape(path)), *options)(
					None, errorHandler
					)
			self.mediumChanged.emit(mediaSlot, path)

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
			elif name.startswith('hd'):
				description = 'Hard disk drive %s' % name[-1].upper()
			elif name.startswith('cd'):
				description = 'CD-ROM drive %s' % name[-1].upper()
			elif name.startswith('virtual'):
				# Don't display anything for this entry!!
				return QtCore.QVariant()
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

	def getDriveNames(self):
		driveNames = []
		driveNames.append('virtual_drive')
		for name, path in self.__mediaSlots:
			if name.startswith('disk') or name.startswith('hd'):
				driveNames.append(name)
		return driveNames

	def getRomTypes(self):
		return self.__romTypes
