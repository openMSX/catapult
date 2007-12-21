from PyQt4 import QtCore
from bisect import bisect

from qt_utils import QtSignal, Signal

# This is a utility class that can be used to emit a signal
# when the internal counter reaches zero. Use it to track
# if the last callback has been received
# Maybe it should be moved to openmsx_utils.py or so.
class ReadyCounter(object):
	
	def __init__(self, signal):
		self.__counter = 0
		self.__signal = signal

	def incr(self):
		self.__counter = self.__counter + 1

	def decr(self):
		self.__counter = self.__counter - 1
		assert self.__counter >= 0
		if (self.__counter == 0):
			self.__signal.emit()

class ConnectorModel(QtCore.QAbstractListModel):
	dataChanged = QtSignal('QModelIndex', 'QModelIndex')
	initialized = Signal()

	def __init__(self, bridge):
		QtCore.QAbstractListModel.__init__(self)
		self.__bridge = bridge
		self.__connectors = []
		self.__connectorClasses = {}
		self.__connectorDescriptions = {}
		self.__pluggableClasses = {}
		self.__pluggableDescriptions = {'--empty--': 'Unplugged'}
		bridge.registerInitial(self.__updateAll)
		bridge.registerUpdate('plug', self.__connectorPlugged)
		bridge.registerUpdate('unplug', self.__connectorUnplugged)
		bridge.registerUpdate('connector', self.__updateConnectorList)

		self.__readyCounter = ReadyCounter(self.initialized)

	def __updateAll(self):
		# TODO: The idea of the name "updateAll" was to be able to deal with
		#       openMSX crashes. So, we should go back to knowing nothing about
		#       the openMSX state.
		#self.__connectors = []
		# Query connectors.
		self.__bridge.command('machine_info', 'connector')(
			self.__connectorListReply
			)
		self.__bridge.command('machine_info', 'pluggable')(
			self.__pluggableListReply
			)

	def __connectorListReply(self, *connectors):
		'''Callback to list the initial connectors of a particular type.
		'''
		if len(connectors) == 0:
			return
		for connector in connectors:
			self.__connectorAdded(connector)
			self.__readyCounter.incr()
			self.__bridge.command('machine_info', 'connectionclass', connector)(
				lambda connectorClass, connector = connector:
					self.__connectorClassReply(connector, connectorClass)
				)

	def __pluggableListReply(self, *pluggables):
		'''Callback to list the initial pluggables of a particular type.
		'''
		if len(pluggables) == 0:
			return

		for pluggable in pluggables:
			self.__bridge.command('machine_info', 'pluggable', pluggable)(
				lambda description, pluggable = pluggable:
					self.__pluggableDescriptionReply(pluggable, description)
				)
			self.__readyCounter.incr()
		for pluggable in pluggables:
			self.__bridge.command('machine_info', 'connectionclass', pluggable)(
				lambda pluggableClass, pluggable = pluggable:
					self.__pluggableClassReply(pluggable, pluggableClass)
				)
			self.__readyCounter.incr()

	def __pluggableDescriptionReply(self, pluggable, description):
		self.__readyCounter.decr()
		self.__pluggableDescriptions[pluggable] = description

	def __connectorDescriptionReply(self, connector, description):
		self.__readyCounter.decr()
		if connector.startswith('joyport'):
			realDescription = 'Joystick Port %s' % connector[-1].upper()
		elif connector.startswith('joytap_port'):
			realDescription = 'Joy Tap Port %s' % connector[-1]
		elif connector.startswith('ninjatap'):
			realDescription = 'Ninja Tap Port %s' % connector[-1]
		else:
			realDescription = description
		self.__connectorDescriptions[connector] = realDescription.rstrip('.')

	def __connectorClassReply(self, connector, connectorClass):
		self.__readyCounter.decr()
		self.__connectorClasses[connector] = connectorClass

	def __pluggableClassReply(self, connector, pluggableClass):
		self.__readyCounter.decr()
		self.__pluggableClasses[connector] = pluggableClass
	
	def getPluggables(self, connectorClass):
		retval = []
		for pluggable in self.__pluggableClasses:
			if self.__pluggableClasses[pluggable] == connectorClass:
				retval.append(pluggable)
		return retval

	def getPluggableDescription(self, pluggable):
		try:
			desc = self.__pluggableDescriptions[pluggable]
		except KeyError:
			desc = ''
			print 'No description available yet for pluggable %s, '\
				'fix race conditions!' % pluggable
		return desc

	def getConnectorDescription(self, connector):
		try:
			desc = self.__connectorDescriptions[connector]
		except KeyError:
			desc = ''
			print 'No description available yet for connector %s, '\
				'fix race conditions!' % connector
		return desc

	def getClass(self, connector):
		return self.__connectorClasses[connector]

	def __connectorPlugged(self, connector, machineId, pluggable):
		print 'Connector %s got plugged with a %s on machine %s' % (connector, \
			pluggable, machineId)
		# TODO: shouldn't we do something with the machineId?
		self.__setConnector(connector, pluggable)

	def __connectorUnplugged(self, connector, machineId, dummy):
		print 'Connector %s got unplugged on machine %s' % (connector, machineId)
		# TODO: shouldn't we do something with the machineId?
		self.__setConnector(connector, '')

	def queryConnector(self, connector):
		'''Queries the connector info of the specified connector'''
		self.__bridge.command('plug', connector)(self.__connectorReply)

	def __connectorAdded(self, connector):
		# First update the list of connector descriptions, if necessary
		if connector not in self.__connectorClasses.keys():
			self.__bridge.command('machine_info', 'connectionclass', connector)(
				lambda connectorClass, connector = connector:
					self.__connectorClassReply(connector, connectorClass)
				)
			self.__readyCounter.incr()
		if connector not in self.__connectorDescriptions.keys():
			self.__bridge.command('machine_info', 'connector',
				connector)(lambda description, connector = connector:
				self.__connectorDescriptionReply(connector, description))
			self.__readyCounter.incr()
		newEntry = ( connector, None )
		index = bisect(self.__connectors, newEntry)
		parent = QtCore.QModelIndex() # invalid model index
		self.beginInsertRows(parent, index, index)
		self.__connectors.insert(index, newEntry)
		self.endInsertRows()
		self.queryConnector(connector)

	def __connectorRemoved(self, connector):
		index = bisect(self.__connectors, ( connector, ))
		if 0 <= index < len(self.__connectors) \
		and self.__connectors[index][0] == connector:
			parent = QtCore.QModelIndex() # invalid model index
			self.beginRemoveRows(parent, index, index)
			del self.__connectors[index]
			self.endRemoveRows()
		else:
			print 'removed connector "%s" did not exist' % connector

	def __setConnector(self, connector, pluggable):
		index = 0
		for name, oldPluggable in self.__connectors:
			if name == connector:
				if oldPluggable == pluggable:
					return False
				else:
					if pluggable == '':
						pluggable = '--empty--'
						print 'unplug %s' % name
					else:
						print 'plug into %s: %s' % (name, pluggable or '<empty>')
					self.__connectors[index] = name, str(pluggable)
					modelIndex = self.createIndex(index, 0)
					self.dataChanged.emit(modelIndex, modelIndex)
					return True
			index += 1
		else:
			raise KeyError(connector)

	def __updateConnector(self, connector, pluggable):
		try:
			self.__setConnector(connector, pluggable)
		except KeyError:
			# This can happen if we don't monitor the creation of new
			# connectors.
			# TODO: Is that a temporary situation?
			print 'received update for non-existing connector "%s"' % connector

	def __updateConnectorList(self, connector, machineId, action):
		# TODO: shouldn't we do something with the machineId?
		if action == 'add':
			self.__connectorAdded(connector)
		elif action == 'remove':
			self.__connectorRemoved(connector)
		else:
			print 'received update for unsupported action "%s" for ' \
				'connector "%s" and machine "%s".'\
				% ( action, connector, machineId )

	def __connectorReply(self, connector, pluggable, flags = ''):
		print 'connector update %s to "%s" flags "%s"'\
			% ( connector, pluggable, flags )
		if connector[-1] == ':':
			connector = connector[ : -1]
		else:
			print 'connector query reply does not start with "<connector>:", '\
				'but with "%s"' % connector
			return
		# TODO: Do something with the flags.
		self.__updateConnector(connector, pluggable)

	def getInserted(self, connector):
		'''Returns the pluggable which is currently plugged in the
		given connector.
		If the pluggable is not yet known, None is returned.
		Raises KeyError if no connector exists by the given name.
		'''
		for name, pluggable in self.__connectors:
			if name == connector:
				return pluggable
		else:
			raise KeyError(connector)

	def setInserted(self, connector, pluggable, errorHandler):
		'''Sets the pluggable of the given connector.
		Raises KeyError if no connector exists by the given name.
		'''
		changed = self.__setConnector(connector, pluggable)
		if changed:
			if pluggable == '--empty--' or pluggable == '':
				self.__bridge.command('unplug', connector)(
					None, errorHandler
					)
			else:
				self.__bridge.command('plug', connector,
					pluggable)(None, errorHandler)

	def rowCount(self, parent):
		# TODO: What does this mean?
		if parent.isValid():
			return 0
		else:
			return len(self.__connectors)

	def data(self, index, role = QtCore.Qt.DisplayRole):
		if not index.isValid():
			return QtCore.QVariant()
		name, pluggable = self.__connectors[index.row()]
		if role == QtCore.Qt.DisplayRole:
			description = self.getConnectorDescription(name)
			return QtCore.QVariant(
				'%s: %s' % ( description, pluggable )
				)
		elif role == QtCore.Qt.UserRole:
			return QtCore.QVariant(name)

		return QtCore.QVariant()
