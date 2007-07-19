# $Id$

from PyQt4 import QtCore, QtGui
from qt_utils import Signal
import settings

# this model keeps track of which audio devices exist
# TODO: make it dynamical (it doesn't keep track of changes in the device list
# yet...)
class AudioModel(QtCore.QAbstractListModel):

	updated = Signal()

	def __init__(self, bridge, settingsManager):
		QtCore.QAbstractListModel.__init__(self)
		self.__bridge = bridge
		self.__settingsManager = settingsManager
		self.__audioChannels = []
		bridge.registerInitial(self.__updateAll)
		#bridge.registerUpdate('audio', self.__updateAudio)

	def __updateAll(self):
		self.__bridge.command('machine_info', 'sounddevice')(
			self.__soundDeviceListReply
			)
	
	def __soundDeviceListReply(self, *devices):
		for device in devices:
			self.__audioChannels.append(device)
			self.__settingsManager.registerSetting(
				device + '_volume', settings.IntegerSetting
				)
		self.updated.emit()

	def getChannels(self):
		return self.__audioChannels


class AudioMixer(QtCore.QObject):

	def __init__(self, ui, settingsManager, bridge):
		QtCore.QObject.__init__(self)
		self.__audioModel = AudioModel(bridge, settingsManager)
		self.__ui = ui
		self.__settingsManager = settingsManager
		self.__audioModel.updated.connect(self.__rebuildUI)
		self.__sliderMap = { }
		self.__labelMap = { }

		self.__sliderGrid = QtGui.QGridLayout(self.__ui)
		self.__sliderBox = QtGui.QVBoxLayout()
		self.__sliderBox.setMargin(6)
		self.__sliderBox.setSpacing(0)
		self.__sliderGrid.addLayout(self.__sliderBox, 0, 0)

	def __rebuildUI(self):
		audioChannels = self.__audioModel.getChannels()
		for channel in audioChannels:
			self.__labelMap[channel] = label = QtGui.QLabel(self.__ui)
			label.setText(channel + ' volume')
			self.__sliderBox.addWidget(label)
			self.__sliderMap[channel] = slider = QtGui.QSlider(self.__ui)
			slider.setObjectName(channel + '_slider')

			slider.setOrientation(QtCore.Qt.Horizontal)
			slider.setTickPosition(QtGui.QSlider.TicksBelow)
			slider.setTickInterval(10)
			slider.setToolTip('Volume of ' + channel)
			self.__sliderBox.addWidget(slider)
			self.__settingsManager.connectSetting(channel + '_volume', slider)

