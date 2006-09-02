# $Id$

from PyQt4 import QtCore

class Setting(QtCore.QObject):
	'''Abstract base class for settings.
	'''

	# TODO: Make these static methods?
	def _getSignature(self):
		'''Returns the Qt type of this value.
		'''
		raise NotImplementedError

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

		# TODO: Perform these initialialisations on the class rather than the
		#       instance?
		signature = self._getSignature()
		self.valueChangedSignal = QtCore.SIGNAL(
			'valueChanged(%s)' % signature
			)
		#decorated = QtCore.pyqtSignature(signature)(self.setValue.im_func)
		#self.setValue = lambda value: decorated(self, value)

	def connectSync(self, obj):
		'''Connect to the specified object in two directions:
		this setting's valueChanged to the object's setValue and
		the object's valueChanged to this setting's setValue.
		'''
		assert obj.connect(self, self.valueChangedSignal, obj.setValue)
		assert self.connect(obj, self.valueChangedSignal, self.setValue)

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
			self.emit(self.valueChangedSignal, value)

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
			self.emit(self.valueChangedSignal, value)
			self.__bridge.command(
				'set', self.__name, self._convertToStr(value)
				)()

class BooleanSetting(Setting):

	def _getSignature(self):
		return 'bool'

	def _convertFromStr(self, valueStr):
		return valueStr in ('on', 'true', 'yes')

	def _convertToStr(self, value):
		if value:
			return 'on'
		else:
			return 'off'

class EnumSetting(Setting):

	def _getSignature(self):
		return 'QString'

	def _convertFromStr(self, valueStr):
		return valueStr

	def _convertToStr(self, value):
		return value

class IntegerSetting(Setting):

	def _getSignature(self):
		return 'int'

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
		# TODO: Move this list elsewhere.
		#       Move it as a list or change to register() method?
		for name, settingClass in (
			( 'scanline', IntegerSetting ),
			( 'blur', IntegerSetting ),
			( 'glow', IntegerSetting ),
			( 'power', BooleanSetting ),
			( 'pause', BooleanSetting ),
			( 'throttle', BooleanSetting ),
			( 'renderer', EnumSetting ),
			):
			assert name not in self.__settings
			self.__settings[name] = settingClass(name, bridge)

	def __getitem__(self, key):
		return self.__settings[key]

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

