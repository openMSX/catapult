# $Id$

from PyQt4 import QtCore, QtGui

from qt_utils import Signal, connect

class Setting(QtCore.QObject):
	'''Abstract base class for settings.
	'''
	# Note: Will be overridden with real signature.
	valueChanged = Signal('?')

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
		#print 'Going to connectSync a %s with myself %s' % (obj, self)
		self.valueChanged.connect(
			lambda value, obj = obj: self.setUiObjValue(obj, value)
			)
		# initialize value of object:
		self.setUiObjValue(obj, self.__value)

		# TODO: Make this more beautiful... (if possible)
		if isinstance(obj, QtGui.QCheckBox):
			connect(obj, 'stateChanged(int)', self.setValue)
		elif isinstance(obj, QtGui.QAction):
			connect(obj, 'triggered(bool)', self.setValue)
		elif isinstance(obj, QtGui.QComboBox):
			connect(obj, 'activated(QString)', self.setValue)
		elif isinstance(obj, QtGui.QSlider):
			connect(obj, 'valueChanged(int)', self.setValue)
		else:
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
			self.__bridge.command(
				'set', self.__name, self._convertToStr(value)
				)()

	# default implementation works for many objects (but not all)
	def setUiObjValue(self, obj, value):
		obj.setValue(value)

class BooleanSetting(Setting):
	valueChanged = Signal('int')

	def _convertFromStr(self, valueStr):
		return valueStr in ('on', 'true', 'yes')

	def _convertToStr(self, value):
		if value:
			return 'on'
		else:
			return 'off'

	def setUiObjValue(self, obj, value):
		if isinstance(obj, QtGui.QCheckBox):
			state = QtCore.Qt.Unchecked
			if value:
				state = QtCore.Qt.Checked
			obj.setCheckState(state)
		elif isinstance(obj, QtGui.QAction):
			assert obj.isCheckable()
			obj.setChecked(value)
		else:
			assert False, 'Unsupported boolean control'

	def setValue(self, value):
		if isinstance(value, bool):
			realVal = value
		else:
			realVal = False
			if value == QtCore.Qt.Unchecked:
				realVal = False
			elif value == QtCore.Qt.Checked:
				realVal = True
			else:
				assert False, 'CheckState unsupported'
		# call superclass
		Setting.setValue(self, realVal)

class EnumSetting(Setting):
	valueChanged = Signal('QString')

	def _convertFromStr(self, valueStr):
		return valueStr

	def _convertToStr(self, value):
		return value

	def setUiObjValue(self, obj, value):
		index = obj.findText(value)
		if index == -1:
			obj.addItem(value)
		else:
			obj.setCurrentIndex(index)

class IntegerSetting(Setting):
	valueChanged = Signal('int')

	def _convertFromStr(self, valueStr):
		return int(valueStr)

	def _convertToStr(self, value):
		return str(value)

class FloatSetting(Setting):
	valueChanged = Signal('double')

	def _convertFromStr(self, valueStr):
		return float(valueStr)

	def _convertToStr(self, value):
		return str(value)

	def setUiObjValue(self, obj, value):
		val = float(value)
		if isinstance(obj, QtGui.QSlider):
			obj.setValue(round(val*100))
		else:
			obj.setValue(val)

	def setValue(self, value):
		if isinstance(value, int):
			realVal = float(value)/100
		else:
			realVal = value
		# call superclass
		Setting.setValue(self, realVal)

class SettingsManager(QtCore.QObject):

	def __init__(self, bridge):
		QtCore.QObject.__init__(self)
		self.__bridge = bridge
		bridge.registerInitial(self.sync)
		bridge.registerUpdate('setting', self.update)
		self.__settings = {}
		self.__specialSettings = {}

	def __getitem__(self, key):
		return self.__settings[key]

	def registerSetting(self, name, settingClass):
		'''Register the name of the setting once at the bridge.
		If multiple objects want to listen to updates the can still
		call this method, otherwise one would start depending on
		the order of instantiating
		'''
		if name not in self.__settings: # setting may not be registered twice
			#print 'registering setting %s' % name
			self.__settings[name] = settingClass(name, self.__bridge)
			self.__bridge.command('set', name)(self.__settings[name].updateValue)

	# this method probably needs an unconnectSetting method for robustness
	def unregisterSetting(self, name):
		#print 'unregistering setting %s' % name
		assert name in self.__settings # setting must've been registered
		del self.__settings[name]

	def registerSpecialSetting(self, name, callback):
		'''Register the name of a setting we do not want to treat
		regularly. Instead register a callback for these, so that
		they can be handled individually.
		Example: fullscreen setting.'''
		assert name not in self.__specialSettings, 'Only register once'
		self.__specialSettings[name] = callback

	def disconnectSetting(self, name, obj):
		self.__settings[name].disconnectSync(obj)

	def connectSetting(self, name, obj):
		self.__bridge.command('openmsx_info', 'setting', name
				)( lambda *items: self.__configUIElem(name, obj, *items), None)

	def __configUIElem(self, name, obj, *items):
		#print 'Configuring UI element %s for setting %s' % (obj, name)
		if items[0] == 'float':
			mini, maxi = items[2].split(' ')
			if isinstance(obj, QtGui.QSlider):
				obj.setMinimum(round(float(mini)*100))
				obj.setMaximum(round(float(maxi)*100))
			else:
				obj.setMinimum(float(mini))
				obj.setMaximum(float(maxi))
			self.__addRestoreAction(name, obj)
		elif items[0] == 'integer':
			mini, maxi = items[2].split(' ')
			obj.setMinimum(int(mini))
			obj.setMaximum(int(maxi))
			self.__addRestoreAction(name, obj)
		elif items[0] == 'enumeration' and isinstance(obj, QtGui.QComboBox):
			obj.clear()
			for item in items[2].split(' '):
				obj.addItem(QtCore.QString(item))
			self.__addRestoreAction(name, obj)
		else:
			print 'No need to configure UI element of type %s'\
				'and setting type %s' % (type(obj), items[0])
		self.__settings[name].connectSync(obj)

	def __addRestoreAction(self, name, obj):
		obj.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
		action = QtGui.QAction('Restore to default value', obj)
		connect(action, 'triggered()',
			lambda name_ = name: self.restoreToDefault(name_)
			)
		obj.addAction(action)

	def sync(self):
		'''Retrieves the current values of all registered settings.
		'''
		# TODO: We could probably query the whole lot with one TCL command.
		#       We would have to be careful with escaping, but when the number
		#       of settings becomes large, it may be worth it for performance.
		for name, setting in self.__settings.iteritems():
			self.__bridge.command('set', name)(setting.updateValue)

	def update(self, name, machineId, message):
		name = str(name)
		setting = self.__settings.get(name)
		# temporary hack: TODO: make settings machine aware
		if setting is None:
			setting = self.__settings.get(
				str(machineId) + '::' + name)
		if setting is None:
			if name in self.__specialSettings:
				callback = self.__specialSettings[name]
				callback(name, str(message))
			else:
				print 'setting %s not registered' % name
		else:
			setting.updateValue(message)

	def set(self, name, message):
		setting = self.__settings.get(str(name))
		if setting is None:
			print 'setting %s not registered' % name
		else:
			setting.setValue(message)

	def restoreToDefault(self, name):
		'''Tells openMSX to set the setting to its default value.
		   Will trigger an update, so that we will know about the
		   new value as well.
		'''
		self.__bridge.command('unset', name)()

