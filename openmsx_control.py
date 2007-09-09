# $Id$

from PyQt4 import QtCore, QtXml

from preferences import preferences
from openmsx_utils import parseTclValue
from qt_utils import Signal, connect

class PrefixDemux(object):

	def __init__(self):
		self.__mapping = {}

	def __call__(self, name, message):
		handled = False
		for prefix, handler in self.__mapping.iteritems():
			if name.startswith(prefix):
				handler(name, message)
				handled = True
		if not handled:
			print 'ignore update for "%s": %s' % ( name, message )

	def register(self, prefixes, handler):
		mapping = self.__mapping
		for prefix in prefixes:
			assert prefix not in mapping
			mapping[prefix] = handler

class ControlBridge(QtCore.QObject):
	logLine = Signal('QString', 'QString')

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
		connection.connectionClosed.connect(self.connectionClosed)
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
			self.command('exit_process')(callback)

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
		assert updateType not in self.__updateHandlers, updateType
		# TODO: How to deal with connected/not-connected?
		assert self.__connection is None, 'register before connecting!'
		self.__updateHandlers[updateType] = handler

	def registerUpdatePrefix(self, updateType, prefixes, handler):
		demux = self.__updateHandlers.get(updateType)
		if demux is None:
			demux = PrefixDemux()
			self.registerUpdate(updateType, demux)
		demux.register(prefixes, handler)

	def command(self, *words):
		'''Send a Tcl command to openMSX.
		The words that form the command are passed as separate arguments.
		An object representing the command returned; when this object is called,
		the command will be executed. You can pass it a handler that will be
		called with the result of the command, or omit this if you are not
		interested in the result.
		'''
		if len(words) == 0:
			raise TypeError('command must contain at least one word')
		line = u' '.join(
			unicode(word).replace('\\', '\\\\').replace(' ', '\\ ')
			for word in words
			)

		def execute(callback = None, errback = None):
			if callback is None:
				rawCallback = None
			else:
				rawCallback = lambda result: callback(*parseTclValue(result))
			self.sendCommandRaw(line, rawCallback, errback)
		return execute

	def sendCommandRaw(self, command, callback = None, errback = None):
		if self.__connection is None:
			print 'IGNORE command because connection is down:', command
		else:
			print 'send %d: %s' % (self.__sendSerial, command)
			if callback is not None or errback is not None:
				assert self.__sendSerial not in self.__callbacks
				self.__callbacks[self.__sendSerial] = callback, errback
			self.__connection.sendCommand(command)
			self.__sendSerial += 1

	def _update(self, updateType, name, message):
		print 'UPDATE: %s, %s, %s' % (updateType, name, message)
		# TODO: Should updates use Tcl syntax for their message?
		#       Right now, they don't.
		self.__updateHandlers[str(updateType)](str(name), str(message))

	def _log(self, level, message):
		print 'log', str(level).upper() + ':', message
		self.logLine.emit(level, message)

	def _reply(self, ok, result):
		serial = self.__receiveSerial
		self.__receiveSerial += 1
		print 'command %d %s: %s' % ( serial, ('FAILED', 'OK')[ok], result )
		callback, errback = self.__callbacks.pop(serial, ( None, None ))
		if ok:
			if callback is None:
				print 'nobody cares'
			else:
				callback(unicode(result))
		else:
			result = str(result)
			if result.endswith('\n'):
				result = result[ : -1]
			if errback is None:
				self._log('warning', result)
			else:
				errback(result)

class ControlHandler(QtXml.QXmlDefaultHandler):
	def __init__(self, bridge):
		QtXml.QXmlDefaultHandler.__init__(self)
		self.__bridge = bridge
		self.__attrs = None
		self.__message = None

	def fatalError(self, exception):
		print 'XML parse error: %s' % exception.message()
		return False # stop parsing

	def startElement(
		self, namespaceURI, localName, qName, atts
		# pylint: disable-msg=W0613
		# We don't need all the arguments, but Qt defines this interface.
		):
		self.__attrs = atts
		self.__message = ''
		return True

	def endElement(
		self, namespaceURI, localName, qName
		# pylint: disable-msg=W0613
		# We don't need all the arguments, but Qt defines this interface.
		):
		# pylint: disable-msg=W0212
		# We use methods from the ControlBridge which are not public.
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
	connectionClosed = Signal()

	def __init__(self, bridge):
		# pylint: disable-msg=W0212
		# We use methods from the ControlBridge which are not public.
		QtCore.QObject.__init__(self)
		self.__errBuf = ''
		self.__logListener = bridge._log

		# Create a cyclic reference to avoid being garbage collected during
		# signal handling. It will be collected later though.
		self.__cycle = self

		# Create process for openMSX (but don't start it yet).
		self.__process = process = QtCore.QProcess()

		# Attach output handlers.
		self.__handler = handler = ControlHandler(bridge)
		self.__parser = parser = QtXml.QXmlSimpleReader()
		parser.setContentHandler(handler)
		parser.setErrorHandler(handler)

		connect(process, 'error(QProcess::ProcessError)', self.processError)
		connect(
			process, 'stateChanged(QProcess::ProcessState)',
			self.processStateChanged
			)
		connect(process, 'readyReadStandardOutput()', self.processEvent)
		connect(process, 'readyReadStandardError()', self.dumpEvent)

		process.setReadChannel(QtCore.QProcess.StandardOutput)
		self.__inputSource = None

	def start(self):
		process = self.__process

		# Start the openMSX process.
		# TODO: Detect and report errors.
		# TODO: If 'system/executable' is not defined yet, we should handle
		#       that gracefully and try to connect as soon as it is defined.
		process.start(
			preferences['system/executable'] + ' -control stdio',
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

	@QtCore.pyqtSignature('QProcess::ProcessError')
	def processError(self, error):
		print 'process error:', error
		if error == QtCore.QProcess.FailedToStart:
			self.connectionClosed.emit()

	@QtCore.pyqtSignature('QProcess::ProcessState')
	def processStateChanged(self, newState):
		print 'process entered state', newState, 'error', self.__process.error()
		if newState == QtCore.QProcess.NotRunning:
			self.connectionClosed.emit()

	@QtCore.pyqtSignature('')
	def dumpEvent(self):
		data = self.__errBuf + str(self.__process.readAllStandardError())
		lastNewLine = data.rfind('\n')
		if lastNewLine != -1:
			lines = data[ : lastNewLine]
			data = data[lastNewLine + 1 : ]
			print 'reported by openMSX: ', lines
			self.__logListener('warning', lines)
		self.__errBuf = data

	@QtCore.pyqtSignature('')
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
			QtCore.QString(
				'<command>%s</command>\n'
				% command.replace('&', '&amp;')
				  .replace('<', '&lt;').replace('>', '&gt;')
				).toUtf8()
			)
		# TODO: Throw I/O exception instead.
		assert status != -1
		#self.__stream.flush()

