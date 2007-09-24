# $Id$

from PyQt4 import QtCore

from qt_utils import Signal, connect

class Setting(QtCore.QObject):
	'''Abstract base class for settings.
	'''
	# Note: Will be overridden with real signature.
	valueChanged = Signal('?')
	settingChanged = Signal('?','?')

	# TODO: Make these static methods?

	def _convertFromStr(self, valueStr):
		'''Converts a string to a value of the setting's type.
		'''
		raise NotImplementedError

	def _convertToStr(self, value):
		'''Converts a value of the setting's type to a string.
		'''
		raise NotImplementedError

	def __init__(self, name, bridge):
		QtCore.QObject.__init__(self)
		self.__name = name
		self.__value = None
		self.__bridge = bridge

	def connectSync(self, obj):
		'''Connect to the specified object in two directions:
		this setting's valueChanged to the object's setValue and
		the object's valueChanged to this setting's setValue.
		'''
		self.valueChanged.connect(obj.setValue)
		connect(obj, self.valueChanged.signature, self.setValue)

	def disconnectSync(self, obj):
		'''Disconnect from the specified object in two directions:
		this setting's valueChanged from the object's setValue and
		the object's valueChanged from this setting's setValue.
		'''
		self.valueChanged.disconnect(obj.setValue)
		# TODO: disconnect(obj, self.valueChanged.signature, self.setValue)

	def getValue(self):
		'''Returns the current value of this setting.
		'''
		return self.__value

	def updateValue(self, valueStr):
		'''Processes an updated setting value from openMSX.
		Unlike setValue, this method does not tell openMSX about the new value,
		to avoid unnecessary network traffic and oscilliating values (the
		update is asynchronous, so a simple "!=" check is not enough to avoid
		loops).
		'''
		value = self._convertFromStr(valueStr)
		if value != self.__value:
			self.__value = value
			self.valueChanged.emit(value)
			self.settingChanged.emit(self.__name, value)

	def revert(self):
		'''Revert to the default value.
		'''
		# TODO: Store default locally so we can report the new value faster?
		#       Is default constant during a session?
		self.__bridge.command('unset', self.__name)()

	# Slots:

	##dynamically decorated
	def setValue(self, value):
		if value != self.__value:
			self.__value = value
			self.valueChanged.emit(value)
			self.settingChanged.emit(self.__name, value)
			self.__bridge.command(
				'set', self.__name, self._convertToStr(value)
				)()

class BooleanSetting(Setting):
	valueChanged = Signal('bool')
	settingChanged = Signal('QString','bool')

	def _convertFromStr(self, valueStr):
		return valueStr in ('on', 'true', 'yes')

	def _convertToStr(self, value):
		if value:
			return 'on'
		else:
			return 'off'

class EnumSetting(Setting):
	valueChanged = Signal('QString')
	settingChanged = Signal('QString','QString')

	def _convertFromStr(self, valueStr):
		return valueStr

	def _convertToStr(self, value):
		return value

class IntegerSetting(Setting):
	valueChanged = Signal('int')
	settingChanged = Signal('QString','int')

	def _convertFromStr(self, valueStr):
		return int(valueStr)

	def _convertToStr(self, value):
		return str(value)

class SettingsManager(QtCore.QObject):

	def __init__(self, bridge):
		QtCore.QObject.__init__(self)
		self.__bridge = bridge
		bridge.registerInitial(self.sync)
		bridge.registerUpdate('setting', self.update)
		self.__settings = {}

	def __getitem__(self, key):
		return self.__settings[key]

	def registerSetting(self, name, settingClass):
		'''Register the name of the setting once at the bridge.
		If multiple objects want to listen to updates the can still 
		call this method, otherwise one would start depending on
		the order of instantiating
		'''
		if name not in self.__settings: # setting may not be registered twice
			self.__settings[name] = settingClass(name, self.__bridge)
			self.__bridge.command('set', name)(self.__settings[name].updateValue)

	# this method probably needs an unconnectSetting method for robustness
	def unregisterSetting(self, name):
#		print 'unregistering setting %s' % name
		assert name in self.__settings # setting must've been registered
		del self.__settings[name]

	def disconnectSetting(self, name, obj):
		self.__settings[name].disconnectSync(obj)

	def connectSetting(self, name, obj):
		self.__settings[name].connectSync(obj)

	def sync(self):
		'''Retrieves the current values of all registered settings.
		'''
		# TODO: We could probably query the whole lot with one TCL command.
		#       We would have to be careful with escaping, but when the number
		#       of settings becomes large, it may be worth it for performance.
		for name, setting in self.__settings.iteritems():
			self.__bridge.command('set', name)(setting.updateValue)

	def update(self, name, message):
		setting = self.__settings.get(str(name))
		if setting is None:
			print 'setting %s not registered' % name
		else:
			setting.updateValue(message)

