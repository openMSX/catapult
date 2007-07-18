# $Id$

from PyQt4 import QtCore, QtGui
from qt_utils import Signal, connect
from settings import *

# this model keeps track of which audio devices exist
# TODO: make it dynamical (it doesn't keep track of changes in the device list yet...)
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
			self.__settingsManager.registerSetting(device + '_volume', IntegerSetting)
		self.updated.emit()

	def getChannels(self):
		return self.__audioChannels


class AudioMixer(QtCore.QObject):

	def __init__(self, ui, settingsManager, bridge):
		QtCore.QObject.__init__(self)
		self.__audioModel = audioModel = AudioModel(bridge, settingsManager)
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
			self.__labelMap[channel] = QtGui.QLabel(self.__ui)
			self.__labelMap[channel].setText(channel + ' volume')
			self.__sliderBox.addWidget(self.__labelMap[channel])
			self.__sliderMap[channel] = QtGui.QSlider(self.__ui)
			self.__sliderMap[channel].setObjectName(channel + '_slider')

			self.__sliderMap[channel].setOrientation(QtCore.Qt.Horizontal)
			self.__sliderMap[channel].setTickPosition(QtGui.QSlider.TicksBelow)
			self.__sliderMap[channel].setTickInterval(10)
			self.__sliderMap[channel].setToolTip('Volume of ' + channel)
			self.__sliderBox.addWidget(self.__sliderMap[channel])
			self.__settingsManager.connectSetting(channel + '_volume', self.__sliderMap[channel])

