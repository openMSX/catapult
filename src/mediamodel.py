# $Id$

from PyQt4 import QtCore
from bisect import bisect, bisect_left
from openmsx_utils import tclEscape, EscapedStr
import os.path

from qt_utils import QtSignal, Signal

# All data that belongs to a mediaslot is centralized in this class
class MediaSlot(QtCore.QObject):
	ipsPatchListChanged = Signal('QString')
	mapperTypeChanged = Signal('QString')

	def __init__(self, name, machine):
		QtCore.QObject.__init__(self)
		self.__name = name
		self.__machine = machine
		self.__ipsPatchList = None
		self.__mapperType = None
		self.__path = None # unknown path
		self.__patchesSetToZero = False
		self.__reset()
	
	def __reset(self):
		self.__ipsPatchList = []
		self.__mapperType = 'Auto Detect'

	def setPath(self, path):
		if self.__path != path:
			self.__reset()
			self.__path = path

	def getPath(self):
		return self.__path

	def setMapperType(self, mapperType):
		self.__mapperType = mapperType
		self.mapperTypeChanged.emit(self.__name)

	def getMapperType(self):
		return self.__mapperType

	def getIpsPatchList(self):
		return self.__ipsPatchList

	def setIpsPatchList(self, patchList):
		self.__patchesSetToZero = len(self.__ipsPatchList) > 0 and len(patchList) == 0
		self.__ipsPatchList = patchList
		self.ipsPatchListChanged.emit(self.__name)

	def getPatchesSetToZero(self):
		return self.__patchesSetToZero

	def getName(self):
		return self.__name

	def getMachine(self):
		return self.__machine

class MediaModel(QtCore.QAbstractListModel):
	dataChanged = QtSignal('QModelIndex', 'QModelIndex')
	mediumChanged = Signal('QString', 'QString')
	ipsPatchListChanged = Signal('QString')
	mapperTypeChanged = Signal('QString')
	mediaSlotRemoved = Signal('QString')
	mediaSlotAdded = Signal('QString')
	connected = Signal()

	def __init__(self, bridge, machineManager):
		QtCore.QAbstractListModel.__init__(self)
		self.__bridge = bridge
		self.__mediaSlotsForMachine = {} # keeps name -> object mapping per machine
		self.__mediaSlotListForMachine = {} # keeps order, per machine
		self.__romTypes = []
		self.__machineManager = machineManager
		self.__cassetteDeckStateModel = CassetteDeckStateModel(bridge)

		bridge.registerInitial(self.__updateAll)
		bridge.registerUpdate('media', self.__updateMedium)
		bridge.registerUpdatePrefix(
			'hardware',
			( 'virtual_drive', 'cart', 'disk', 'cassette', 'hd', 'cd' ),
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

		for pattern in ( 'cart?', 'disk?', 'virtual_drive', 'cassetteplayer', 'hd?',
				'cd?'
			       ):
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
		for medium in ( 'virtual_drive', 'cart', 'disk', 'cassette', 'hd', 'cd' ):
			if slots[0].startswith(medium):
				break
		else:
			print 'media slot "%s" not recognised' % slots[0]
			return
		for slot in slots:
			self.__mediaSlotAdded(slot,
				 # TODO: is this machineId still valid at this point in time?
				 self.__machineManager.getCurrentMachineId()
				)

	def queryMedium(self, slot):
		'''Queries the medium info of the specified slot'''
		self.__bridge.command(slot)(self.__mediumReply)

	def __machineAdded(self, machineId):
		print 'Adding media admin for machine with id ', machineId
		self.__mediaSlotsForMachine[unicode(machineId)] = {}
		self.__mediaSlotListForMachine[unicode(machineId)] = []

	def __machineRemoved(self, machineId):
		print 'Removing media admin for machine with id ', machineId
		del self.__mediaSlotsForMachine[unicode(machineId)]
		del self.__mediaSlotListForMachine[unicode(machineId)]

	def __mediaSlotAdded(self, slotName, machineId):
		slotList = self.__mediaSlotListForMachine[machineId]
		self.__mediaSlotsForMachine[machineId][slotName] = slot = \
				MediaSlot(slotName, machineId)
		slot.ipsPatchListChanged.connect(self.__ipsPatchListChanged)
		slot.mapperTypeChanged.connect(self.__mapperTypeChanged)
		index = bisect(slotList, slotName)
		if not slotName in slotList:
			parent = QtCore.QModelIndex() # invalid model index
			self.beginInsertRows(parent, index, index)
			slotList.insert(index, slotName)
			self.endInsertRows()
		# consistency check:
		assert len(slotList) == len(
				self.__mediaSlotsForMachine[machineId].keys()
				), 'Inconsistent media administration! %s %s' \
				% (slotList,
				self.__mediaSlotsForMachine[machineId].keys()
				)
		self.mediaSlotAdded.emit(slotName) # TODO: add machine id
		self.queryMedium(slotName) # TODO: add machine id???

	def __mediaSlotRemoved(self, slotName, machineId):
		slotList = self.__mediaSlotListForMachine[machineId]
		index = bisect_left(slotList, slotName)
		if 0 <= index < len(slotList) and slotList[index] == slotName:
			# bisect actually found it
			parent = QtCore.QModelIndex() # invalid model index
			print 'Removing media slot ', slotName, ' for machine ', machineId
			self.beginRemoveRows(parent, index, index)
			del slotList[index]
			del self.__mediaSlotsForMachine[machineId][slotName]
			self.endRemoveRows()
			# consistency check
			assert len(slotList) == len(
						self.__mediaSlotsForMachine[machineId].keys()
				), 'Inconsistent media administration!'
			self.mediaSlotRemoved.emit(slotName) # TODO: add machine id
		else:
			print 'removed slot "%s" did not exist' % slotName

	def __setMedium(self, mediaSlot, path, machineId):
		index = 0
		for slotName in self.__mediaSlotListForMachine[machineId]:
			if slotName == mediaSlot:
				slot = self.__mediaSlotsForMachine[machineId][slotName]
				if slot.getPath() == path:
					return False
				else:
					print 'insert into %s: %s' % (slotName, path or '<empty>')
					slot.setPath(path)
					modelIndex = self.createIndex(index, 0)
					self.dataChanged.emit(modelIndex, modelIndex)
					return True
			index += 1
		else:
			raise KeyError(mediaSlot)

	def __updateMedium(self, mediaSlot, machineId, path):
		if self.__setMedium(mediaSlot, path, machineId):
			self.mediumChanged.emit(mediaSlot, path) # TODO: add machine Id?

	def __updateHardware(self, hardware, machineId, action):
		if action == 'add':
			self.__mediaSlotAdded(hardware, machineId)
		elif action == 'remove':
			self.__mediaSlotRemoved(hardware, machineId)
		else:
			print 'received update for unsupported action "%s" for ' \
				'hardware "%s" on machine "%s".' \
				% ( action, hardware, machineId )

	def __mediumReply(self, mediaSlot, path, flags = ''):
		print 'media update %s to "%s" flags "%s"' % ( mediaSlot, path, flags )
		if mediaSlot[-1] == ':':
			mediaSlot = mediaSlot[ : -1]
		else:
			print 'medium slot query reply does not start with "<medium>:", '\
				'but with "%s"' % mediaSlot
			return
		# TODO: Do something with the flags
		# TODO: can the current machine Id have changed??
		self.__updateMedium(mediaSlot,
				self.__machineManager.getCurrentMachineId(), path)

	def getInserted(self, mediaSlot):
		'''Returns the path of the medium currently inserted in the given slot.
		If the path is not yet known, None is returned.
		Raises KeyError if no media slot exists by the given name.
		'''
		machineId = self.__machineManager.getCurrentMachineId()
		return self.__mediaSlotsForMachine[machineId][mediaSlot].getPath()

	def setInserted(self, mediaSlot, path, errorHandler):
		'''Sets the path of the medium currently inserted in the given slot.
		Raises KeyError if no media slot exists by the given name.
		'''
		machineId = self.__machineManager.getCurrentMachineId()
		changed = self.__setMedium(mediaSlot, path, machineId)
		if changed:
			if path == '':
				self.__bridge.command(mediaSlot, 'eject')(
					None, errorHandler
					)
			else:
				self.__bridge.command(mediaSlot, 'insert',
					EscapedStr(tclEscape(path)))(
					None, errorHandler
					)
			self.mediumChanged.emit(mediaSlot, path)

	def applyOptions(self, mediaSlot, errorHandler = None):
		print 'Applying options...'
		machineId = self.__machineManager.getCurrentMachineId()
		slot = self.__mediaSlotsForMachine[machineId][mediaSlot]
		patchList = slot.getIpsPatchList()
		path = slot.getPath()
		mapper = slot.getMapperType()
		if path != '':
			optionList = []
			if len(patchList) > 0 or slot.getPatchesSetToZero():
				for option in patchList:
					optionList.append('-ips')
					optionList.append(option)
			if mapper != 'Auto Detect':
				optionList.append('-romtype')
				optionList.append(mapper)
			self.__bridge.command(mediaSlot, 'insert',
				EscapedStr(tclEscape(path)), *optionList
				)(
				None, errorHandler
				)

	def rowCount(self, parent):
		# TODO: What does this mean?
		if parent.isValid():
			return 0
		else:
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
			# print '*********************************************************'
			return QtCore.QVariant()
		slot = self.__mediaSlotsForMachine[machineId][slotList[row]]
		
		name = slot.getName()
		path = slot.getPath()
		
		if role == QtCore.Qt.DisplayRole:
			if name.startswith('cart'):
				description = 'Cartridge slot %s' % name[-1].upper()
			elif name.startswith('disk'):
				description = 'Disk drive %s' % name[-1].upper()
			elif name.startswith('cassette'):
				description = 'Cassette deck'
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

	def iterDriveNames(self):
		machineId = self.__machineManager.getCurrentMachineId()
		for name in self.__mediaSlotListForMachine[machineId]:
			if name.startswith('disk') or name.startswith('hd') \
					or name == 'virtual_drive':
				yield name

	def getRomTypes(self):
		return self.__romTypes

	def getCassetteDeckStateModel(self):
		return self.__cassetteDeckStateModel
	
	### wrapper methods around MediaSlots ###
	
	def getIpsPatchList(self, slot):
		machineId = self.__machineManager.getCurrentMachineId()
		return self.__mediaSlotsForMachine[machineId][slot].getIpsPatchList()

	def setIpsPatchList(self, slot, patchList):
		machineId = self.__machineManager.getCurrentMachineId()
		self.__mediaSlotsForMachine[machineId][slot].setIpsPatchList(patchList)

	# this is basically transmitting the signal from the
	# internally used MediaSlot object
	def __ipsPatchListChanged(self, slot):
		self.ipsPatchListChanged.emit(slot)

	def getMapperType(self, slot):
		machineId = self.__machineManager.getCurrentMachineId()
		return self.__mediaSlotsForMachine[machineId][slot].getMapperType()

	def setMapperType(self, slot, mapperType):
		machineId = self.__machineManager.getCurrentMachineId()
		self.__mediaSlotsForMachine[machineId][slot].setMapperType(mapperType)

	# this is basically transmitting the signal from the
	# internally used MediaSlot object
	def __mapperTypeChanged(self, slot):
		self.mapperTypeChanged.emit(slot)

# TODO: properly handle machine id's and thus changes of machines
class CassetteDeckStateModel(QtCore.QObject):

	stateChanged = Signal('QString')
	
	def __init__(self, bridge):
		QtCore.QObject.__init__(self)
		self.__bridge = bridge
		self.__state = ''
		bridge.registerInitial(self.__queryState)
		bridge.registerUpdate('status', self.__updateState)

	def __queryState(self):
		self.__bridge.command('cassetteplayer')(self.__stateReply)

	def __updateState(self, name, machineId, state):
		# TODO: shouldn't we do something with machineId?
		if name == 'cassetteplayer':
			print 'State of cassetteplayer updated to ', state
			self.__state = state
			self.stateChanged.emit(state)
	
	def __stateReply(self, *words):
		self.__updateState('cassetteplayer', 'TODO: machine', words[2])
	
	def getState(self):
		assert self.__state != '', 'Illegal state!'
		return self.__state

	def rewind(self, errorHandler):
		self.__updateState('cassetteplayer', 'TODO: machine', 'rewind')
		self.__bridge.command('cassetteplayer', 'rewind')(
			lambda *dummy: self.__queryState(), errorHandler
			)
	
	def record(self, filename, errorHandler):
		self.__bridge.command('cassetteplayer', 'new', filename)(
			None, errorHandler
			)

	def play(self, errorHandler):
		self.__bridge.command('cassetteplayer', 'play')(
			None, errorHandler
			)
	
	def getTapeLength(self, replyHandler, errorHandler):
		self.__bridge.command('cassetteplayer', 'getlength')(
			replyHandler, errorHandler)

	def getTapePosition(self, replyHandler, errorHandler):
		self.__bridge.command('cassetteplayer', 'getpos')(
			replyHandler, errorHandler)

