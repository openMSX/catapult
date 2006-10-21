# $Id$

from PyQt4 import QtCore

from inspect import getargspec, isbuiltin

class QtSignal(object):
	'''Wraps a slot on a native Qt object to make it easier to connect to it.

	Usage:
	QtSignal(object, 'valueChanged', 'int').connect(slot)
	'''

	argTypes = property(lambda self: self._argTypes)

	def __init__(self, obj, name, *argTypes):
		if not isinstance(obj, QtCore.QObject):
			raise TypeError('Not a subclass of QObject: %s' % type(obj))
		self._object = obj
		self._name = name
		self._argTypes = argTypes
		signature = self._getSignature()
		self._checkSignal(obj, signature)
		self._signature = QtCore.SIGNAL(signature)

	def __str__(self):
		return 'SIGNAL(%s)' % self._getSignature()

	def _getSignature(self):
		return '%s(%s)' % (self._name, ', '.join(self._argTypes))

	def _checkSignal(self, obj, signature):
		if obj.metaObject().indexOfSignal(
			QtCore.QMetaObject.normalizedSignature(signature).data()
			) == -1:
			raise AttributeError('No signal matching signature: %s' % signature)

	def connect(self, slot):
		# Sanity check on slot.
		if not callable(slot):
			raise TypeError('Slot type not callable: %s' % type(slot))
		if not isbuiltin(slot):
			# Slots is implemented in Python; check arguments.
			args, varArgs_, kwArgs_, defaults_ = getargspec(slot)
			numSlotArgs = len(args)
			if len(args) != 0 and args[0] == 'self':
				numSlotArgs -= 1
			numSignalArgs = len(self._argTypes)
			if numSlotArgs > numSignalArgs:
				raise TypeError(
					'Slot requires %d arguments, while signal only supplies %d'
					% ( numSlotArgs, numSignalArgs )
					)
			# Note: It is allowed for a slot to have less arguments than the
			#       signal: the superfluous arguments are ignored.

		# Make connection.
		ok = QtCore.QObject.connect(self._object, self._signature, slot)
		# Note: I have never seen False being returned in practice, even on
		#       failed connections.
		assert ok, 'Failed to connect to "%s"' % self._getSignature()

class _SignalSource(QtSignal):
	'''Used internally by Signal.
	'''

	def _checkSignal(self, obj, signature):
		# Signal is defined in Python, so Qt does not know about it.
		# However, since no-one except the Signal class should be instantiating
		# us, it's safe to assume the signal exists.
		pass

	def emit(self, *args):
		if len(args) != len(self._argTypes):
			raise TypeError(
				'%s emitted with %d arguments'
				% ( self._getSignature(), len(args) )
				)
		self._object.emit(self._signature, *args)

class Signal(object):
	'''Descriptor which makes it easy to declare signals in Python code.

	Usage:
	class X(QtCore.QObject):
		valueChanged = Signal('int')
		def setValue(self, newValue):
			...
			valueChanged.emit(newValue)
		...
	x = X()
	x.valueChanged.connect(slot)
	'''

	def __init__(self, *argTypes):
		self.__argTypes = argTypes
		self.__name = None

	def __getName(self, obj):
		if self.__name is None:
			for clazz in obj.__class__.__mro__:
				for name, member in clazz.__dict__.iteritems():
					if member == self:
						self.__name = name
						return name
			else:
				raise AttributeError('Not a member of given object')
		else:
			return self.__name

	def __get__(self, obj, objType = None): # pylint: disable-msg=W0613
		return _SignalSource(obj, self.__getName(obj), *self.__argTypes)

	def __set__(self, obj, value):
		raise AttributeError('Cannot write signals')

	def __delete__(self, obj):
		raise AttributeError('Cannot delete signals')

