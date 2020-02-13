from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

class HardwareModel(QtCore.QAbstractTableModel):
	'''Base class for machine and extension models.
	'''
	_hardwareType = property() # abstract
	populating = pyqtSignal() # repopulation starts
	populated = pyqtSignal() # repopulation ends

	def __init__(self, bridge):
		QtCore.QAbstractTableModel.__init__(self)
		self._bridge = bridge
		self.__repliesLeft = None
		self._tempInfoDict = {} # for testing hardware
		self.__itemIter = None

	def __listReply(self, *items):
		self.__repliesLeft = len(items)
		self.__itemIter = iter(items)
		# start requesting info for all these hardware items
		self.__requestInfo()

	def __listFailed(self, message):
		print('Failed to get list of %ss: %s' % (
			self._hardwareType, message
			))
		self.__allDone()

	def __allDone(self):
		self.__repliesLeft = None
		self.populated.emit()

	def __requestInfo(self):
		'''Requests information about the current machine.
		   Current depends on the value of __itemIter
		'''
		item = next(self.__itemIter)
		self._bridge.command(
			'openmsx_info', self._hardwareType + 's', item
			)(
			lambda *info: self.__infoReply(item, info),
			lambda message: self.__infoFailed(item, message)
			)

	def __machineIdReply(self, machineId, name):
		self._bridge.addMachineToIgnore(machineId)
		self._startHardwareTest(machineId, name)

	def _startHardwareTest(self, machineId, name):
		'''Implements the hardware specific test to check if it is working.
		'''
		raise NotImplementedError

	def __infoReply(self, name, info):
		infoDict = dict(info[i : i + 2] for i in range(0, len(info), 2))
		self._tempInfoDict = infoDict
		if self._testable:
			self._bridge.command('create_machine')(
				lambda machineId, name_ = name: self.__machineIdReply(machineId, name_),
				None
				)
		else:
			self.__testEnd(name)

	def __infoFailed(self, name, message):
		print('Failed to get info about %s %s: %s' % (
			self._hardwareType, name, message
			))
		self.__infoDone()

	def _testDone(self, name, machineId, message, successful):
		# this is automatically done after the machine is deleted
		# in openMSX, see openmsx_control.py:
		#self._bridge.removeMachineToIgnore(machineId)
		print('Test for: %s successful: %s' % (name, successful))
		if successful:
			self._tempInfoDict['working'] = 'Yes'
		else:
			self._tempInfoDict['working'] = 'No'
			self._tempInfoDict['brokenreason'] = message
			print('Broken hardware found: %s %s: %s' % (
				self._hardwareType, name, message
				))
		self.__testEnd(name)

	def __testEnd(self, name):
		self._storeItem(name, self._tempInfoDict)
		self.__infoDone()

	def __infoDone(self):
		self.__repliesLeft -= 1
		if self.__repliesLeft == 0:
			self.__allDone()
		else:
			# process the next one!
			self.__requestInfo()

	def _clearItems(self):
		'''Clears the items stored in the model.
		Called at the start of repopulation.
		'''
		raise NotImplementedError

	def _storeItem(self, name, info):
		'''Stores the info about one particular hardware item.
		Called for each item when repopulating.
		'''
		raise NotImplementedError

	def repopulate(self):
		'''(Re)populate the model by querying openMSX.
		'''
		self.populating.emit()
		self.beginResetModel()
		self._clearItems()
		self.endResetModel()
		# Ask openMSX for list of hardware items.
		self._bridge.command(
			'openmsx_info', self._hardwareType + 's'
			)(self.__listReply, self.__listFailed)

