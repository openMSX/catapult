# $Id$

from PyQt4 import QtCore, QtGui
from qt_utils import connect

class ConnectorPlugger(QtCore.QObject):

	def __init__(self, ui, connectorModel):
		QtCore.QObject.__init__(self)
		self.__connectorModel = connectorModel 
		self.__ui = ui
		self.__connector = None
		self.__handlers = []
		# Connect to connector model and view:
		ui.connectorList.setModel(connectorModel)
		connectorModel.dataChanged.connect(self.connectorPluggableChanged)
		connect(
			ui.connectorList.selectionModel(),
			'currentChanged(QModelIndex, QModelIndex)',
			self.updateConnector
			)

		connectorModel.initialized.connect(self.__initHandlers)

		# Connect signals of connector panels:

	def __initHandlers(self):
		# It is essential to keep the references, otherwise the classes are
		# garbage collected even though they have signal-slot connections
		# attached to them.
		self.__handlers = [
			handler(self.__ui, self)
			for handler in ( AudioInHandler, CassettePortHandler,
				JoyPortHandler, PrinterPortHandler, SerialHandler,
				AudioKbdPortHandler, MIDIinHandler, MIDIoutHandler
				)
			]

	def __updateConnectorPage(self, connector):
		connectorClass = self.__connectorModel.getClass(connector)
		# Initialise the UI page for this connector.
		for handler in self.__handlers:
			if handler.connectorClass == connectorClass:
				handler.updatePage(connector)
				page = handler.getPage()
				break
		else:
			print 'no handler found for connectorClass "%s"' % connectorClass
		return page

	@QtCore.pyqtSignature('QModelIndex')
	def updateConnector(self, index):
		# Find out which connector entry has become active.
		connector = str(index.data(QtCore.Qt.UserRole).toString())
		if self.__connector == connector:
			return
		self.__connector = connector
		page = self.__updateConnectorPage(connector)
		# Switch page.
		self.__ui.connectorStack.setCurrentWidget(page)

	@QtCore.pyqtSignature('QModelIndex, QModelIndex')
	def connectorPluggableChanged(
		self, topLeft, bottomRight
		# pylint: disable-msg=W0613
		# TODO: We use the fact that we know ConnectorModel will only mark
		# one item changed at a time. This is not correct in general.
		):
		index = topLeft
		connector = str(index.data(QtCore.Qt.UserRole).toString())
		if self.__connector == connector:
			self.__updateConnectorPage(connector)

	def setPluggable(self, pluggable):
		'''Sets a new pluggable for the currently selected connector.
		'''
		self.__connectorModel.setInserted(self.__connector, pluggable,
			lambda message: self.__connectorChangeErrorHandler(
				self.__connector, message
				)
			)

	def __connectorChangeErrorHandler(self, connector, message):
		messageBox = QtGui.QMessageBox('Plugging problem', message,
			QtGui.QMessageBox.Warning, 0, 0, 0,
			self.__ui.centralwidget
			)
		messageBox.show()
		self.__connectorModel.queryConnector(connector)

	def getModel(self):
		return self.__connectorModel

class ConnectorHandler(QtCore.QObject):
	connector = None

	def __init__(self, ui, plugger):
		QtCore.QObject.__init__(self)
		self._ui = ui
		self._plugger = plugger

		# Look up UI elements.
		self._unplugButton = getattr(ui, self.connector + 'UnplugButton')
		self._pluggableBox = getattr(ui, self.connector + 'PluggableBox')
		self._pluggableLabel = getattr(ui, self.connector + 'Label')
		self._pluggableDescLabel = getattr(ui, self.connector + 'DescLabel')

		self._pluggableBox.clear()
		self._pluggableBox.addItem('--empty--')
		self._pluggableBox.addItems(
			plugger.getModel().getPluggables(self.connectorClass)
			)

		# Connect signals.
		connect(self._unplugButton, 'clicked()', self.unplug)
		connect(self._pluggableBox, 'activated(QString)', self.selectionChanged)

	def unplug(self):
		'''Removes the currently inserted pluggable.
		'''
		self._plugger.setPluggable('')
	
	def selectionChanged(self, newSelection):
		self._plugger.setPluggable(newSelection)

	def updatePage(self, connector):
		pluggable = self._plugger.getModel().getInserted(connector)

		# set combobox to the current value
		self._pluggableBox.setCurrentIndex(self._pluggableBox.findText(pluggable))

		# set description of pluggable
		description = self._plugger.getModel().getPluggableDescription(pluggable)
		self._pluggableDescLabel.setText(description)

		# set description (readable name) of connector
		self._pluggableLabel.setText(
			self._plugger.getModel().getConnectorDescription(connector)
			)
	
	def getPage(self):
		return getattr(self._ui, self.connector + 'Page')

class AudioInHandler(ConnectorHandler):
	connector = 'audioIn'
	connectorClass = 'Audio Input Port'

class CassettePortHandler(ConnectorHandler):
	connector = 'casPort'
	connectorClass = 'Cassette Port'

class JoyPortHandler(ConnectorHandler):
	connector = 'joyPort'
	connectorClass = 'Joystick Port'

class PrinterPortHandler(ConnectorHandler):
	connector = 'printerPort'
	connectorClass = 'Printer Port'

class SerialHandler(ConnectorHandler):
	connector = 'RS232'
	connectorClass = 'RS232'

class AudioKbdPortHandler(ConnectorHandler):
	connector = 'Y8950KbdPort'
	connectorClass = 'Y8950 Keyboard Port'

class MIDIinHandler(ConnectorHandler):
	connector = 'MIDIin'
	connectorClass = 'midi in'

class MIDIoutHandler(ConnectorHandler):
	connector = 'MIDIout'
	connectorClass = 'midi out'
