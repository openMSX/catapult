import os.path
from bisect import bisect

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, QModelIndex

from openmsx_utils import tclEscape, EscapedStr

class Medium(QtCore.QObject):
	'''All data that belongs to a medium is centralized in this class.
	'''

	@staticmethod
	def create(mediumType, path, patchList = None, mapperType = 'Auto Detect'):
		'''Factory method to create the proper Medium instance.
		The "mediumType" argument can be a media slot name, as long as it starts
		with one of the media type names.
		'''
		if patchList is None:
			patchList = []
		if mediumType.startswith('cart'):
			return CartridgeMedium(path, patchList, str(mapperType))
		if mediumType.startswith('cassette'):
			return CassetteMedium(path)
		if mediumType.startswith('disk'):
			return DiskMedium(path, patchList)
		return Medium(path)

	def __init__(self, path):
		QtCore.QObject.__init__(self)
		self.__path = path

	def getPath(self):
		return self.__path

	def __eq__(self, other):
		# pylint: disable-msg=W0212
		return isinstance(other, Medium) and self.__path == other.__path

	def __ne__(self, other):
		return not self.__eq__(other)

	def __str__(self):
		return 'medium with path %s' % self.__path

class PatchableMedium(Medium):
	'''Abstract base class for patchable media.
	'''

	def __init__(self, path, patchList):
		Medium.__init__(self, path)
		self._ipsPatchList = patchList

	def copyWithNewPatchList(self, patchList):
		return PatchableMedium(self.getPath(), patchList)

	def getIpsPatchList(self):
		return self._ipsPatchList

	def __eq__(self, other):
		# pylint: disable-msg=W0212
		return (
			isinstance(other, PatchableMedium) and
			Medium.__eq__(self, other) and
			self._ipsPatchList == other._ipsPatchList
			)

	def __str__(self):
		return Medium.__str__(self) + ' and %d patches' \
			% len(self._ipsPatchList)

class CartridgeMedium(PatchableMedium):

	def __init__(self, path, patchList, mapperType):
		PatchableMedium.__init__(self, path, patchList)
		self.__mapperType = mapperType

	def copyWithNewPatchList(self, patchList):
		return CartridgeMedium(self.getPath(), patchList, self.__mapperType)

	def getMapperType(self):
		return self.__mapperType

	def __eq__(self, other):
		# pylint: disable-msg=W0212
		return (
			isinstance(other, CartridgeMedium) and
			PatchableMedium.__eq__(self, other) and
			self.__mapperType == other.__mapperType
			)

	def __str__(self):
		return 'cartridge' + PatchableMedium.__str__(self) + \
			' and mapper type ' + self.__mapperType

class DiskMedium(PatchableMedium):

	def __str__(self):
		return 'disk' + PatchableMedium.__str__(self)

class CassetteMedium(Medium):

	def __init__(self, path):
		Medium.__init__(self, path)
		self.__length = 0

	def getLength(self):
		return self.__length

	def setLength(self, length):
		'''Only call this from CassetteDeck!'''
		self.__length = length

	def __str__(self):
		return 'cassette' + Medium.__str__(self)

class MediaSlot(QtCore.QObject):
	slotDataChanged = pyqtSignal(object) # slot

	@staticmethod
	def create(slotName, bridge):
		'''Factory method to create the proper MediaSlot instance.
		slotName a mediaSlot name, which will also be stored in the object.
		'''
		if slotName.startswith('cassette'):
			return CassetteDeck(slotName, bridge)
		if slotName.startswith('cart'):
			return CartridgeSlot(slotName, bridge)
		if slotName.startswith('disk'):
			return DiskDrive(slotName, bridge)
		return MediaSlot(slotName, bridge)

	def __init__(self, name, bridge):
		QtCore.QObject.__init__(self)
		self.__name = name
		self._bridge = bridge
		self._medium = None # empty slot
		self.__queryMedium()

	def __queryMedium(self):
		self._bridge.command(self.__name)(self.__mediumQueryReply)

	def __mediumQueryReply(self, slotName, path, flags = ''):
		print('media query result of %s "%s" flags "%s"' % (
			slotName, path, flags
			))
		if slotName[-1] == ':':
			slotName = slotName[:-1]
		else:
			print('medium slot query reply does not start with "<medium>:", '\
				'but with "%s"' % slotName)
			return
		assert slotName == self.__name, 'medium slot reply not for ' \
			'this slot? Got %s, expected %s.' % (slotName, self.__name)
		# TODO: Do something with the flags
		# TODO: Can we be sure that this reply was indeed for this (machine's)
		#       slot?
		self.updateMedium(path)

	def updateMedium(self, path):
		if str(path) == '':
			medium = None
		else:
			medium = Medium.create(self.__name, path)
		self._medium = medium
		self.slotDataChanged.emit(self)

	def getName(self):
		return self.__name

	def setMedium(self, medium, errorHandler):
		if medium == self._medium:
			return
		if medium is None:
			print('ejecting from %s: %s' % (self.__name, self._medium))
			self._bridge.command(self.__name, 'eject')(
				None, errorHandler
				)
		else:
			optionList = self._createOptionList(medium)
			print('insert into %s: %s (with options: %s)' % (self.__name,
				medium, str(optionList)
				))
			self._bridge.command(self.__name, 'insert',
				EscapedStr(tclEscape(medium.getPath())), *optionList)(
				None, lambda message, realHander = errorHandler: \
					self.__errorHandler(realHander, message)
				)
		self._medium = medium # no update sent, so we do it ourselves
		self.slotDataChanged.emit(self)

	def __errorHandler(self, realHandler, message):
		# call the actual errorhandler
		realHandler(message)
		# but also re-query openMSX for the actual situation
		self.__queryMedium()

	@staticmethod
	def _createOptionList(medium):
		assert medium is not None, 'We should never insert None'
		optionList = []
		return optionList

	def getMedium(self):
		return self._medium

	def __lt__(self, other):
		# pylint: disable-msg=W0212
		return not isinstance(other, MediaSlot) \
			or self.__name < other.__name

	def __str__(self):
		return 'MediaSlot with name %s and inserted medium %s' % (self.__name,
			self._medium or '<none>')

class MediaSlotWithPatchableMedia(MediaSlot):

	@staticmethod
	def _createOptionList(medium):
		optionList = MediaSlot._createOptionList(medium)
		patchList = medium.getIpsPatchList()
		for option in patchList:
			optionList.append('-ips')
			optionList.append(option)
		return optionList

class CassetteDeck(MediaSlot):

	stateChanged = pyqtSignal(str)

	def __init__(self, name, bridge):
		MediaSlot.__init__(self, name, bridge)
		self.__state = ''
		self.__queryState()

	def __queryState(self):
		self._bridge.command('cassetteplayer')(self.__stateReply)

	def __stateReply(self, *words):
		self.setState(str(words[2]))

	def setMedium(self, medium, errorHandler):
		MediaSlot.setMedium(self, medium, errorHandler)
		if medium is not None:
			self._bridge.command('cassetteplayer', 'getlength')(
				self.__lengthReply, None)

	def __lengthReply(self, length):
		self._medium.setLength(length)
		self.slotDataChanged.emit(self)

	def getPosition(self, replyHandler, errorHandler):
		'''Query position of this medium to openMSX.
		It is not stored in this class, because there are no updates
		for it. This way, the user of this class can control the polling.
		'''
		self._bridge.command('cassetteplayer', 'getpos')(
			replyHandler, errorHandler)

	def setState(self, state):
		'''Only call this from MediaModel and from __stateReply and rewind!
		'''
		self.__state = state
		self.stateChanged.emit(state)

	def getState(self):
		assert self.__state != '', 'Illegal state!'
		return self.__state

	def rewind(self, errorHandler):
		self.setState('rewind') # rewind state is not sent by openMSX
		self._bridge.command('cassetteplayer', 'rewind')(
			lambda *dummy: self.__queryState(), errorHandler
			)

	def record(self, filename, errorHandler):
		self._bridge.command('cassetteplayer', 'new', filename)(
			None, errorHandler
			)

	def play(self, errorHandler):
		self._bridge.command('cassetteplayer', 'play')(
			None, errorHandler
			)

class DiskDrive(MediaSlotWithPatchableMedia):
	pass

class CartridgeSlot(MediaSlotWithPatchableMedia):

	@staticmethod
	def _createOptionList(medium):
		optionList = MediaSlotWithPatchableMedia._createOptionList(medium)
		assert isinstance(medium, CartridgeMedium), 'Wrong medium in cartridgeslot!'
		mapper = medium.getMapperType()
		if mapper != 'Auto Detect':
			optionList.append('-romtype')
			optionList.append(mapper)
		return optionList

class MediaModel(QtCore.QAbstractListModel):
	dataChanged = pyqtSignal(QModelIndex, QModelIndex)
	mediaSlotRemoved = pyqtSignal(str, str)
	mediaSlotAdded = pyqtSignal(str, str)
	connected = pyqtSignal()

	def __init__(self, bridge, machineManager):
		QtCore.QAbstractListModel.__init__(self)
		self.__bridge = bridge
		self.__mediaSlotListForMachine = {} # keeps order, per machine
		# virtual_drive always exists and is machine independent
		self.__virtualDriveSlot = MediaSlot.create('virtual_drive', bridge)
		self.__romTypes = []
		self.__machineManager = machineManager

		bridge.registerInitial(self.__updateAll)
		bridge.registerUpdate('media', self.__updateMedium)
		bridge.registerUpdate('status', self.__updateCassetteDeckState)
		bridge.registerUpdatePrefix(
			'hardware',
			('cart', 'disk', 'cassette', 'hd', 'cd'),
			self.__updateHardware
			)
		machineManager.machineAdded.connect(self.__machineAdded)
		machineManager.machineRemoved.connect(self.__machineRemoved)

	def __updateAll(self):
		# this is in the registerInitial callback, so:
		self.connected.emit()
		# TODO: The idea of the name "updateAll" was to be able to deal with
		#       openMSX crashes. So, we should go back to knowing nothing about
		#       the openMSX state.
		#self.__mediaSlotList = []

		for pattern in ('cart?', 'disk?', 'cassetteplayer', 'hd?', 'cd?'):
			# Query medium slots.
			self.__bridge.command('info', 'command', pattern)(
				self.__mediumListReply
				)
		self.__bridge.command('openmsx_info', 'romtype')(self.__romTypeReply)

	def __romTypeReply(self, *romTypes):
		self.__romTypes.append('Auto Detect')
		for romType in romTypes:
			self.__romTypes.append(romType)

	def __mediumListReply(self, *slots):
		'''Callback to list the initial media slots of a particular type.
		'''
		if len(slots) == 0:
			return
		for mediumName in ('cart', 'disk', 'cassette', 'hd', 'cd'):
			if slots[0].startswith(mediumName):
				break
		else:
			print('media slot "%s" not recognised' % slots[0])
			return
		for slot in slots:
			self.__mediaSlotAdded(slot,
				 # TODO: is this machineId still valid at this point in time?
				 self.__machineManager.getCurrentMachineId()
				)


	def __machineAdded(self, machineId):
		print('Adding media admin for machine with id ', machineId)
		self.__mediaSlotListForMachine[str(machineId)] = []

	def __machineRemoved(self, machineId):
		print('Removing media admin for machine with id ', machineId)
		del self.__mediaSlotListForMachine[str(machineId)]

	def __mediaSlotAdded(self, slotName, machineId):
		print('Adding media slot to admin admin for machine with id ', machineId, ' and slot name ', slotName)
		slotList = self.__mediaSlotListForMachine[machineId]
		# add empty slot
		slot = MediaSlot.create(slotName, self.__bridge)
		index = bisect(slotList, slot)
		# we shouldn't have a slot with this name yet
		if slot in slotList:
			assert slot.getName() != slotName
		parent = QtCore.QModelIndex() # invalid model index
		self.beginInsertRows(parent, index, index)
		slotList.insert(index, slot)
		self.endInsertRows()
		self.mediaSlotAdded.emit(slotName, machineId)
		slot.slotDataChanged.connect(self.__slotDataChanged)

	def __mediaSlotRemoved(self, slotName, machineId):
		slotList = self.__mediaSlotListForMachine[machineId]
		for index, slot in enumerate(slotList):
			if slot.getName() == slotName:
				parent = QtCore.QModelIndex() # invalid model index
				print('Removing "%s" for machine %s' % (slot, machineId))
				self.beginRemoveRows(parent, index, index)
				del slotList[index]
				self.endRemoveRows()
				slot.slotDataChanged.disconnect(self.__slotDataChanged)
				self.mediaSlotRemoved.emit(slotName, machineId)
				return
		assert False, 'removed slot "%s" did not exist' % slotName

	# this is for the updates coming from openMSX
	# forward to the slot
	def __updateMedium(self, mediaSlotName, machineId, path):
		slot = self.getMediaSlotByName(mediaSlotName, machineId)
		slot.updateMedium(path)

	def __slotDataChanged(self, slot):
		# virtual drive has no index
		if slot == self.__virtualDriveSlot:
			return
		# find this slot and emit a signal with its index
		for slotList in self.__mediaSlotListForMachine.values():
			for index, iterSlot in enumerate(slotList):
				if slot is iterSlot:
					modelIndex = self.createIndex(index, 0)
					self.dataChanged.emit(modelIndex, modelIndex)
					return
		assert False, 'Slot not found: %s' % slot

	def __updateHardware(self, hardware, machineId, action):
		if action == 'add':
			self.__mediaSlotAdded(hardware, machineId)
		elif action == 'remove':
			self.__mediaSlotRemoved(hardware, machineId)
		else:
			print('received update for unsupported action "%s" for ' \
				'hardware "%s" on machine "%s".' \
				% (action, hardware, machineId))


	def getMediaSlotByName(self, name, machineId = ''):
		'''Returns the media slot of the given machine, identified by the given
		name. Raises KeyError if no media slot exists by the given name.
		'''
		if name == 'virtual_drive':
			print('Ignoring machineId "%s" for virtual_drive, ' \
				'which is not machine bound...' % machineId)
			return self.__virtualDriveSlot

		assert machineId != '', 'You need to pass a machineId!'
		slotList = self.__mediaSlotListForMachine[machineId]
		for slot in slotList:
			if slot.getName() == name:
				return slot
		raise KeyError(name)

	def rowCount(self, parent):
		# TODO: What does this mean?
		if parent.isValid():
			return 0
		machineId = self.__machineManager.getCurrentMachineId()
		try:
			count = len(self.__mediaSlotListForMachine[machineId])
		except KeyError:
			# can happen when switching machines or when the
			# current machine is not known yet
			count = 0
		return count

	def data(self, index, role = QtCore.Qt.DisplayRole):
		if not index.isValid():
			return QtCore.QVariant()

		machineId = self.__machineManager.getCurrentMachineId()
		slotList = self.__mediaSlotListForMachine[machineId]

		row = index.row()
		if row < 0 or row > (len(slotList) - 1):
			# can happen when switching machines (race conditions?)
			# print('*********************************************************')
			return QtCore.QVariant()
		slot = slotList[row]
		slotName = slot.getName()

		if role == QtCore.Qt.DisplayRole:
			if slotName.startswith('cart'):
				description = 'Cartridge slot %s' % slotName[-1].upper()
			elif slotName.startswith('disk'):
				description = 'Disk drive %s' % slotName[-1].upper()
			elif slotName.startswith('cassette'):
				description = 'Cassette deck'
			elif slotName.startswith('hd'):
				description = 'Hard disk drive %s' % slotName[-1].upper()
			elif slotName.startswith('cd'):
				description = 'CD-ROM drive %s' % slotName[-1].upper()
#			elif slotName.startswith('virtual'):
#				# Don't display anything for this entry!!
#				return QtCore.QVariant()
			else:
				description = slotName.upper()

			medium = slot.getMedium()
			if medium:
				path = medium.getPath()
				dirName, fileName = os.path.split(path)
				if fileName == '':
					fileName = dirName[dirName.rfind(os.path.sep) + 1:]
			else:
				fileName = '<empty>'
			return QtCore.QVariant(
				'%s: %s' % (description, fileName)
				)
		if role == QtCore.Qt.UserRole:
			return QtCore.QVariant(slotName)

		return QtCore.QVariant()

	def iterDriveNames(self):
		machineId = self.__machineManager.getCurrentMachineId()
		slotList = self.__mediaSlotListForMachine[machineId][:]
		slotList.append(self.__virtualDriveSlot)
		for slot in slotList:
			name = slot.getName()
			if name.startswith('disk') or name.startswith('hd') \
					or name == 'virtual_drive':
				yield name

	def getRomTypes(self):
		return self.__romTypes

	# forward cassette deck state update to the proper slot
	def __updateCassetteDeckState(self, name, machineId, state):
		name = str(name)
		if name == 'cassetteplayer':
			print('State of cassetteplayer updated to ', state)
			deck = self.getMediaSlotByName(name, machineId)
			deck.setState(state)
