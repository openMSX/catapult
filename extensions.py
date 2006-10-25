# $Id$

from PyQt4 import QtCore

from hardware import HardwareModel

class ExtensionModel(HardwareModel):
	_hardwareType = 'extension'

	def __init__(self, bridge):
		HardwareModel.__init__(self, bridge)

	def _clearItems(self):
		pass

	def _storeItem(self, name, info):
		# TODO: Will we really introduce "title"?
		info.setdefault('title', name)

		print name, info

class ExtensionManager(QtCore.QObject):

	def __init__(self, parent, machineBox, settingsManager, bridge):
		QtCore.QObject.__init__(self)
		self.__parent = parent
		self.__model = model = ExtensionModel(bridge)

	def chooseMachine(self):
		# Fetch extension info.
		self.__model.repopulate()
