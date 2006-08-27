from PyQt4 import QtCore

class VisibleSetting(QtCore.QObject):
	'''Virtual setting which interacts with the "renderer" setting.
	'''
	valueChangedSignal = QtCore.SIGNAL('valueChanged(bool)')

	def __init__(self, rendererSetting):
		QtCore.QObject.__init__(self)
		self.__rendererSetting = rendererSetting
		self.__lastRenderer = None
		self.__value = False
		assert self.connect(
			rendererSetting, rendererSetting.valueChangedSignal,
			self.update
			)

	def getValue(self):
		return self.__value

	#@QtCore.pyqtSignature('QString')
	def setValue(self, value):
		if self.__value == value:
			return
		self.__value = value
		if value:
			if self.__lastRenderer is None:
				self.__rendererSetting.revert()
			else:
				self.__rendererSetting.setValue(self.__lastRenderer)
		else:
			self.__rendererSetting.setValue('none')
		self.emit(self.valueChangedSignal, value)

	#@QtCore.pyqtSignature('QString')
	def update(self, value):
		boolValue = (value != 'none')
		if self.__value == boolValue:
			return
		self.__value = boolValue
		if boolValue:
			self.__lastRenderer = value
		self.emit(self.valueChangedSignal, boolValue)

class PlayState(QtCore.QObject):
	play = 'play'
	pause = 'pause'
	stop = 'stop'
	forward = 'forward'
	unknown = 'unknown'

	def __init__(self, settingsManager, ui):
		QtCore.QObject.__init__(self)

		self.__buttonMap = {
			self.play: ui.playButton,
			self.pause: ui.pauseButton,
			self.stop: ui.stopButton,
			self.forward: ui.forwardButton,
			}

		self.__powerSetting = powerSetting = settingsManager['power']
		self.__pauseSetting = pauseSetting = settingsManager['pause']
		self.__throttleSetting = throttleSetting = settingsManager['throttle']
		self.__visibleSetting = visibleSetting = VisibleSetting(
			settingsManager['renderer']
			)

		for setting in (
			powerSetting, pauseSetting, throttleSetting, visibleSetting
			):
			assert self.connect(
				setting, setting.valueChangedSignal,
				self.update
				)

	def computeState(self):
		'''Determines the state of the music-player-like control,
		which is a combination of several setting states.
		Some combinations do not map to an actual state, we map this to
		an imaginary state called "unknown".
		'''
		power = self.__powerSetting.getValue()
		pause = self.__pauseSetting.getValue()
		throttle = self.__throttleSetting.getValue()
		visible = self.__visibleSetting.getValue()

		# TODO: Is it possible to do this declarative, such that the same
		#       mapping is used for both directions? (from/to settings)
		if power and visible:
			if pause:
				return self.pause
			else:
				if throttle:
					return self.play
				else:
					return self.forward
		elif not power and not visible:
			return self.stop
		else:
			return self.unknown

	#@QtCore.pyqtSignature('')
	def update(self):
		newState = self.computeState()
		for state, button in self.__buttonMap.iteritems():
			button.setChecked(newState == state)

	def setState(self, newState):
		# TODO: Disable button update while settings are being changed by
		#       this object itself.
		{
			self.play: self.do_play,
			self.pause: self.do_pause,
			self.stop: self.do_stop,
			self.forward: self.do_forward,
		}[newState]()
		self.update()

	def do_play(self):
		self.__throttleSetting.setValue(True)
		self.__pauseSetting.setValue(False)
		self.__powerSetting.setValue(True)
		self.__visibleSetting.setValue(True)

	def do_pause(self):
		self.__throttleSetting.setValue(True)
		self.__pauseSetting.setValue(True)
		self.__powerSetting.setValue(True)
		self.__visibleSetting.setValue(True)

	def do_stop(self):
		self.__visibleSetting.setValue(False)
		self.__powerSetting.setValue(False)

	def do_forward(self):
		self.__pauseSetting.setValue(False)
		self.__powerSetting.setValue(True)
		self.__visibleSetting.setValue(True)
		self.__throttleSetting.setValue(False)

