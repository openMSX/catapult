# $Id$

from PyQt4 import QtCore

from qt_utils import Signal

class HardwareModel(QtCore.QAbstractTableModel):
	'''Base class for machine and extension models.
	'''
	_hardwareType = property() # abstract
	populating = Signal() # repopulation starts
	populated = Signal() # repopulation ends

	def __init__(self, bridge):
		QtCore.QAbstractTableModel.__init__(self)
		self.__bridge = bridge
		self.__repliesLeft = None

	def __listReply(self, *items):
		self.__repliesLeft = len(items)
		for item in items:
			# Note: The request is done in a separate method, so the current
			#       value of "item" is passed rather than this method's context
			#       in which "item" is changing each iteration.
			self.__requestInfo(item)

	def __listFailed(self, message):
		print 'Failed to get list of %ss: %s' % (
			self._hardwareType, message
			)
		self.__allDone()

	def __allDone(self):
		self.__repliesLeft = None
		self.populated.emit()

	def __requestInfo(self, item):
		self.__bridge.command(
			'openmsx_info', self._hardwareType + 's', item
			)(
			lambda *info: self.__infoReply(item, info),
			lambda message: self.__infoFailed(item, message)
			)

	def __infoReply(self, name, info):
		infoDict = dict(info[i : i + 2] for i in xrange(0, len(info), 2))
		self._storeItem(name, infoDict)
		self.__infoDone()

	def __infoFailed(self, name, message):
		print 'Failed to get info about %s %s: %s' % (
			self._hardwareType, name, message
			)
		self.__infoDone()

	def __infoDone(self):
		self.__repliesLeft -= 1
		if self.__repliesLeft == 0:
			self.__allDone()

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
		self._clearItems()
		# Ask openMSX for list of hardware items.
		self.__bridge.command(
			'openmsx_info', self._hardwareType + 's'
			)(self.__listReply, self.__listFailed)

