# $Id$

'''Provides a nice interface to Qt's infrastructure.
In this case "nice" means a Pythonic style and additional error checking.
'''

from PyQt4 import QtCore

from inspect import getargspec, isbuiltin
from re import compile as regex

class _SignalWrapper(object):
	'''Wraps a Qt signal in a Python object to make it easier to connect to.
	'''

	signature = property(lambda self: self.__signature)

	def __init__(self, obj, signature, numArgs):
		self.__object = obj
		self.__signature = signature
		self.__numArgs = numArgs
		self.__macroSignature = QtCore.SIGNAL(signature)

	def __str__(self):
		return 'SIGNAL(%s)' % self.__signature

	def connect(self, slot):
		# Sanity check on slot.
		if not callable(slot):
			raise TypeError('Slot type not callable: %s' % type(slot))
		if not isbuiltin(slot):
			# Slot is implemented in Python; check arguments.
			args = getargspec(slot)[0]
			numSlotArgs = len(args)
			if numSlotArgs != 0 and args[0] == 'self':
				numSlotArgs -= 1
			if numSlotArgs > self.__numArgs:
				raise TypeError(
					'Slot requires %d arguments, while signal only supplies %d'
					% ( numSlotArgs, self.__numArgs )
					)
			# Note: It is allowed for a slot to have less arguments than the
			#       signal: the superfluous arguments are ignored.

		# Make connection.
		ok = QtCore.QObject.connect(self.__object, self.__macroSignature, slot)
		# Note: I have never seen False being returned in practice, even on
		#       failed connections.
		assert ok, 'Failed to connect to "%s"' % self.__signature

	def emit(self, *args):
		if len(args) != self.__numArgs:
			raise TypeError(
				'%s emitted with %d arguments'
				% ( self.__signature, len(args) )
				)
		self.__object.emit(self.__macroSignature, *args)

class _SignalDescriptor(object):
	'''Base class for signal declaration descriptors.
	'''
	_native = property() # abstract

	def __init__(self, *argTypes):
		self.__argTypes = argTypes
		self.__name = None
		self.__signature = None

	def __getName(self, obj):
		for clazz in obj.__class__.__mro__:
			for name, member in clazz.__dict__.iteritems():
				if member == self:
					return name
		else:
			raise AttributeError('Not a member of given object')

	def __get__(self, obj, objType = None): # pylint: disable-msg=W0613
		try:
			# Optimize for the common case.
			return obj.__dict__[self.__name]
		except KeyError:
			# Either self.__name is None or the object has no wrapper stored.
			storageName = self.__name
			if storageName is None:
				name = self.__getName(obj)
				self.__name = storageName = 'signal$' + name
				self.__signature = signature = '%s(%s)' % (
					name, ', '.join(self.__argTypes)
					)

				# Sanity checks on signal.
				if not isinstance(obj, QtCore.QObject):
					raise TypeError('Not a subclass of QObject: %s' % type(obj))
				if self._native and obj.metaObject().indexOfSignal(
					QtCore.QMetaObject.normalizedSignature(signature).data()
					) == -1:
					raise AttributeError(
						'No signal matching signature: %s' % signature
						)
				# If signal is defined in Python, Qt does not know about it.
				# However, since no-one except the Signal class should be
				# instantiating us, it's safe to assume the signal exists.

			signal = _SignalWrapper(obj, self.__signature, len(self.__argTypes))
			obj.__dict__[storageName] = signal
			return signal

	def __set__(self, obj, value):
		raise AttributeError('Cannot write signals')

	def __delete__(self, obj):
		raise AttributeError('Cannot delete signals')

class QtSignal(_SignalDescriptor):
	'''Descriptor which makes it easy to access inherited Qt signals.

	Usage:
	class X(QtGui.QSomeWidget):
		valueChanged = QtSignal('int')
		def setValue(self, newValue):
			...
			valueChanged.emit(newValue)
		...
	x = X()
	x.valueChanged.connect(slot)
	'''
	_native = True

class Signal(_SignalDescriptor):
	'''Descriptor which makes it easy to create signals in Python.

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
	_native = False

_reSignature = regex(r'(\w+)\s*\(\s*((?:[\w:]+(?:\s*,\s*[\w:]+)*)?)\s*\)')

def connect(obj, signature, slot):
	'''Connects a Qt native signal to a slot.
	'''
	match = _reSignature.match(signature)
	argTypes = match.group(2)
	if argTypes:
		numSignalArgs = argTypes.count(',') + 1
	else:
		numSignalArgs = 0
	_SignalWrapper(obj, signature, numSignalArgs).connect(slot)

