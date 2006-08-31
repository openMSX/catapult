# $Id$

from PyQt4 import QtCore, QtXml

from custom import executable
from openmsx_utils import parseTclValue

def escapeTcl(value):
	return value.replace('\\', '\\\\').replace(' ', '\\ ')

class ControlBridge(QtCore.QObject):
	# Signals:
	logLineSignal = QtCore.SIGNAL('logLine(QString, QString)')

	def __init__(self):
		QtCore.QObject.__init__(self)
		self.__connection = None
		self.__initialHandlers = []
		self.__updateHandlers = {}
		# Command reply handling:
		self.__sendSerial = 0
		self.__receiveSerial = 0
		self.__callbacks = {}

	def openConnection(self):
		self.__connection = connection = ControlConnection(self)
		self.connect(
			connection, ControlConnection.connectionClosedSignal,
			self.connectionClosed
			)
		connection.start()
		for updateType in self.__updateHandlers.iterkeys():
			self.sendCommandRaw('update enable %s' % updateType)
		for handler in self.__initialHandlers:
			handler()

	def closeConnection(self, callback):
		if self.__connection is None:
			# Connection is already closed.
			callback()
		else:
			# TODO: Have a fallback in case openMSX does not respond.
			# TODO: Is waiting for the quit command to be confirmed good enough,
			#       or should we wait for the control connection end tag?
			# TODO: I remember Wouter saying that "quit" is just an alias for
			#       something that we should actually use.
			# TODO: Make sure closing the openMSX window does not actually quit
			#       openMSX if it was started from a control connection.
			self.command('quit')(callback)

	def connectionClosed(self):
		print 'connection with openMSX was closed'
		self.__connection = None
		# TODO: How to handle this? Attempt a reconnect?

	def registerInitial(self, handler):
		'''Registers a handler to be called after a new connection is
		established.
		You can use this mechanism to synchronize the initial state.
		'''
		assert self.__connection is None, 'register before connecting!'
		self.__initialHandlers.append(handler)

	def registerUpdate(self, updateType, handler):
		'''Registers a handler for a specific update type.
		The handler should be a callable that accepts two parameters:
		name (name attribute of XML tag) and message (contents of XML tag).
		Only one handler per type is supported.
		'''
		# TODO: Along the way, we will probably need these updates:
		#       'led', 'setting', 'plug', 'unplug', 'media', 'status'
		assert updateType not in self.__updateHandlers
		# TODO: How to deal with connected/not-connected?
		assert self.__connection is None, 'register before connecting!'
		self.__updateHandlers[updateType] = handler

	def command(self, *words):
		if len(words) == 0:
			raise TypeError('command must contain at least one word')
		line = u' '.join([
			unicode(word).replace('\\', '\\\\').replace(' ', '\\ ')
			for word in words
			])

		def execute(callback = None):
			if callback is None:
				rawCallback = None
			else:
				rawCallback = lambda result: callback(*parseTclValue(result))
			self.sendCommandRaw(line, rawCallback)
		return execute

	def sendCommandRaw(self, command, callback = None):
		if self.__connection is None:
			print 'IGNORE command because connection is down:', command
		else:
			print 'send %d: %s' % (self.__sendSerial, command)
			if callback is not None:
				assert self.__sendSerial not in self.__callbacks
				self.__callbacks[self.__sendSerial] = callback
			self.__connection.sendCommand(command)
			self.__sendSerial += 1

	def _update(self, updateType, name, message):
		print 'UPDATE: %s, %s, %s' % (updateType, name, message)
		# TODO: Should updates use Tcl syntax for their message?
		#       Right now, they don't.
		self.__updateHandlers[str(updateType)](str(name), str(message))

	def _log(self, level, message):
		print 'log', str(level).upper() + ':', message
		self.emit(self.logLineSignal, level, message)

	def _reply(self, ok, result):
		serial = self.__receiveSerial
		self.__receiveSerial += 1
		print 'command %d %s: %s' % ( serial, ('FAILED', 'OK')[ok], result )
		if ok:
			callback = self.__callbacks.pop(serial, None)
			if callback is None:
				print 'nobody cares'
			else:
				callback(unicode(result))
		else:
			result = str(result)
			if result.endswith('\n'):
				result = result[ : -1]
			self._log('warning', result)

class ControlHandler(QtXml.QXmlDefaultHandler):
	def __init__(self, bridge):
		QtXml.QXmlDefaultHandler.__init__(self)
		self.__bridge = bridge

	def fatalError(self, exception):
		print 'XML parse error: %s' %exception.message()
		return False # stop parsing

	def startElement(self, namespaceURI, localName, qName, atts):
		self.__attrs = atts
		self.__message = ''
		return True

	def endElement(self, namespaceURI, localName, qName):
		if qName == 'openmsx-output':
			pass
		elif qName == 'reply':
			self.__bridge._reply(
				self.__attrs.value('result') == 'ok',
				self.__message
				)
		elif qName == 'log':
			self.__bridge._log(
				self.__attrs.value('level'),
				self.__message
				)
		elif qName == 'update':
			self.__bridge._update(
				self.__attrs.value('type'),
				self.__attrs.value('name'),
				self.__message
				)
		else:
			# TODO: Is it OK to ignore unknown tags?
			#       Formulate a compatiblity strategy in the CliComm design.
			print 'unkown XML tag: %s' % qName
		return True

	def characters(self, content):
		self.__message += content
		return True

class ControlConnection(QtCore.QObject):
	# Signals:
	connectionClosedSignal = QtCore.SIGNAL('connectionClosed()')

	def __init__(self, bridge):
		QtCore.QObject.__init__(self)
		self.__errBuf = ''
		self.__logListener = bridge._log

		# Create process for openMSX (but don't start it yet).
		self.__process = process = QtCore.QProcess()

		# Attach output handlers.
		self.__handler = handler = ControlHandler(bridge)
		self.__parser = parser = QtXml.QXmlSimpleReader()
		parser.setContentHandler(handler)
		parser.setErrorHandler(handler)

		assert self.connect(
			process, QtCore.SIGNAL('stateChanged(QProcess::ProcessState)'),
			self.processStateChanged
			)
		assert self.connect(
			process, QtCore.SIGNAL('readyReadStandardOutput()'),
			self.processEvent
			)
		assert self.connect(
			process, QtCore.SIGNAL('readyReadStandardError()'),
			self.dumpEvent
			)

		process.setReadChannel(QtCore.QProcess.StandardOutput)
		self.__inputSource = None

	def start(self):
		process = self.__process

		# Start the openMSX process.
		# TODO: Detect and report errors.
		process.start(
			executable + ' -control stdio',
		#	'gdb'
		#	' --quiet'
		#	' --command=script.gdb'
		#	' ~/openmsx/derived/openmsx'
			QtCore.QIODevice.ReadWrite |
			QtCore.QIODevice.Text |
			QtCore.QIODevice.Unbuffered
			)

		status = process.write('<openmsx-control>\n')
		# TODO: Throw I/O exception instead.
		assert status != -1

	#@QtCore.pyqtSignature('QProcess::ProcessState')
	def processStateChanged(self, newState):
		print 'process entered state', newState, 'error', self.__process.error()
		if newState == QtCore.QProcess.NotRunning:
			self.emit(self.connectionClosedSignal)

	#@QtCore.pyqtSignature('')
	def dumpEvent(self):
		data = self.__errBuf + str(self.__process.readAllStandardError())
		lastNewLine = data.rfind('\n')
		if lastNewLine != -1:
			lines = data[ : lastNewLine]
			data = data[lastNewLine + 1 : ]
			print 'reported by openMSX: ', lines
			self.__logListener('warning', lines)
		self.__errBuf = data

	#@QtCore.pyqtSignature('')
	def processEvent(self):
		inputSource = self.__inputSource
		first = inputSource is None
		if first:
			self.__inputSource = inputSource = QtXml.QXmlInputSource()
		inputSource.setData(self.__process.readAllStandardOutput())
		if first:
			ok = self.__parser.parse(self.__inputSource, True)
		else:
			ok = self.__parser.parseContinue()
		assert ok

	def sendCommand(self, command):
		status = self.__process.write(
			QtCore.QString('<command>%s</command>\n' % command).toUtf8()
			)
		# TODO: Throw I/O exception instead.
		assert status != -1
		#self.__stream.flush()

