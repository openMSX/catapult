from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

from settings import BooleanSetting, EnumSetting

class VisibleSetting(QtCore.QObject):
	'''Virtual setting which interacts with the "renderer" setting.
	'''
	valueChanged = pyqtSignal('bool')

	def __init__(self, rendererSetting):
		QtCore.QObject.__init__(self)
		self.__rendererSetting = rendererSetting
		self.__lastRenderer = None
		self.__value = False
		rendererSetting.valueChanged.connect(self.update)

	def getValue(self):
		return self.__value

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
		self.valueChanged.emit(value)

	def update(self, value):
		boolValue = (value != 'none')
		if self.__value == boolValue:
			return
		self.__value = boolValue
		if boolValue:
			self.__lastRenderer = value
		self.valueChanged.emit(boolValue)

class PlayState(QtCore.QObject):
	play = 'play'
	pause = 'pause'
	stop = 'stop'
	forward = 'forward'
	unknown = 'unknown'

	def __init__(self, settingsManager, ui):
		QtCore.QObject.__init__(self)
		self.__state = None

		self.__buttonMap = {
			self.play: ui.playButton,
			self.pause: ui.pauseButton,
			self.stop: ui.stopButton,
			self.forward: ui.forwardButton,
			}

		settingsManager.registerSetting('power', BooleanSetting)
		self.__powerSetting = powerSetting = settingsManager['power']
		settingsManager.registerSetting('pause', BooleanSetting)
		self.__pauseSetting = pauseSetting = settingsManager['pause']
		settingsManager.registerSetting('fastforward', BooleanSetting)
		self.__fastforwardSetting = fastforwardSetting = settingsManager['fastforward']
		settingsManager.registerSetting('renderer', EnumSetting)
		self.__visibleSetting = visibleSetting = VisibleSetting(
			settingsManager['renderer']
			)

		for setting in (
			powerSetting, pauseSetting, fastforwardSetting, visibleSetting
			):
			setting.valueChanged.connect(self.update)

	def getVisibleSetting(self):
		return self.__visibleSetting

	def computeState(self):
		'''Determines the state of the music-player-like control,
		which is a combination of several setting states.
		Some combinations do not map to an actual state, we map this to
		an imaginary state called "unknown".
		'''
		power = self.__powerSetting.getValue()
		pause = self.__pauseSetting.getValue()
		fastforward = self.__fastforwardSetting.getValue()
		visible = self.__visibleSetting.getValue()

		# TODO: Is it possible to do this declarative, such that the same
		#       mapping is used for both directions? (from/to settings)
		if power and visible:
			if pause:
				return self.pause
			if not fastforward:
				return self.play
			return self.forward
		if not power and not visible:
			return self.stop
		return self.unknown

	def update(self):
		self.__state = self.computeState()
		for state, button in self.__buttonMap.items():
			button.setChecked(self.__state == state)

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

	def getState(self):
		return self.__state

	def do_play(self):
		self.__fastforwardSetting.setValue(False)
		self.__pauseSetting.setValue(False)
		self.__powerSetting.setValue(True)
		self.__visibleSetting.setValue(True)

	def do_pause(self):
		self.__fastforwardSetting.setValue(False)
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
		self.__fastforwardSetting.setValue(True)
