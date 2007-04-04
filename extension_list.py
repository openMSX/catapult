# This code was meant to be used for the extension list on the first page of
# the new catapult
# This is placeholder for code later on, at the moment there is no 
# way to get the inserted extension list from openMSX
#

from PyQt4 import QtCore, QtGui
from bisect import bisect
import os.path

from preferences import preferences
from qt_utils import QtSignal, connect

class ExtensionListModel(QtCore.QAbstractListModel):
	dataChanged = QtSignal('QModelIndex', 'QModelIndex')

	def __init__(self, bridge):
		QtCore.QAbstractListModel.__init__(self)
		self.__bridge = bridge
		self.__extensionListSlots = []
		bridge.registerInitial(self.__updateAll)
		bridge.registerUpdate('extension', self.__updateExtension)

	def __updateAll(self):
		# TODO: The idea of the name "updateAll" was to be able to deal with
		#       openMSX crashes. So, we should go back to knowing nothing about
		#       the openMSX state.
		#self.__extensionListSlots = []
		# TODO: how do we ask which extensions are inserted ???
		# at the time of writing openmsx had no update event for this.


	def __extensionListSlotRemoved(self, slot):
		index = bisect(self.__extensionListSlots, ( slot, ))
		if 0 <= index < len(self.__extensionListSlots) \
		and self.__extensionListSlots[index][0] == slot:
			parent = QtCore.QModelIndex() # invalid model index
			self.beginRemoveRows(parent, index, index)
			del self.__extensionListSlots[index]
			self.endRemoveRows()
		else:
			print 'removed slot "%s" did not exist' % slot

	def __setMedium(self, extensionListSlot, path):
		index = 0
		for name, oldPath in self.__extensionListSlots:
			if name == extensionListSlot:
				if oldPath == path:
					return False
				else:
					print 'insert into %s: %s' % (name, path or '<empty>')
					self.__extensionListSlots[index] = name, path
					modelIndex = self.createIndex(index, 0)
					self.dataChanged.emit(modelIndex, modelIndex)
					return True
			index += 1
		else:
			raise KeyError(extensionListSlot)

	def __updateExtension(self, extensionListSlot ):
		# TODO: nothing yet...
		# but we should remove or add this to the extensionList
		# How do we handle cases were some extension can be 
		# inserted twice or more ??

	def rowCount(self, parent):
		# TODO: What does this mean?
		if parent.isValid():
			return 0
		else:
			return len(self.__extensionListSlots)

	def data(self, index, role = QtCore.Qt.DisplayRole):
		if not index.isValid():
			return QtCore.QVariant()

		name, path = self.__extensionListSlots[index.row()]
		if role == QtCore.Qt.DisplayRole:
			#TODO: Are we going to display the shortname or
			# the longer description?
			return QtCore.QVariant(name)
		elif role == QtCore.Qt.UserRole:
			return QtCore.QVariant(name)

		return QtCore.QVariant()

def parseExtensionListSlot(extensionListSlot):
	'''Returns a tuple ( medium, identifier) that corresponds to the given
	extensionList slot.
	'''
	return extensionListSlot[ : -1], extensionListSlot[-1]
