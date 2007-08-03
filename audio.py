# $Id$

from PyQt4 import QtCore, QtGui
from qt_utils import Signal, connect
import settings
#import gc

# this model keeps track of which audio devices exist
class AudioModel(QtCore.QAbstractListModel):

	updated = Signal()

	__firstTime = True

	def __init__(self, bridge, settingsManager, machineManager, extensionManager):
		QtCore.QAbstractListModel.__init__(self)
		self.__bridge = bridge
		self.__settingsManager = settingsManager
		self.__audioChannels = []
		bridge.registerInitial(self.__updateAll)
		# update the list of channels when extensions or machines changed
		connect(machineManager, 'machineChanged()', self.__updateAll)
		connect(extensionManager, 'extensionChanged()', self.__updateAll)
		
		#bridge.registerUpdate('audio', self.__updateAudio)

	def __updateAll(self):
		self.__bridge.command('machine_info', 'sounddevice')(
			self.__soundDeviceListReply
			)
	
	def __soundDeviceListReply(self, *devices):
		# first unregister possible existing audio channels.
		if not self.__firstTime:
			self.__firstTime = False
			self.__settingsManager.unregisterSetting('master_volume')
		for device in self.__audioChannels:
			self.__settingsManager.unregisterSetting(device + '_volume')
		self.__audioChannels = []
		# then register the new devices
		self.__audioChannels.append('master')
		self.__settingsManager.registerSetting('master_volume', 
			settings.IntegerSetting
			)
		for device in devices:
			self.__audioChannels.append(device)
			self.__settingsManager.registerSetting(
				device + '_volume', settings.IntegerSetting
				)
		self.updated.emit()

	def getChannels(self):
		return self.__audioChannels

# TODO: introduce a scrollarea to prevent the window from resizing with large
# amounts of channels
class AudioMixer(QtCore.QObject):

	def __init__(self, ui, settingsManager, machineManager, extensionManager,
			bridge
			):
		QtCore.QObject.__init__(self)
		self.__audioModel = AudioModel(bridge, settingsManager, machineManager, 
			extensionManager
			)
		self.__ui = ui
		self.__settingsManager = settingsManager
		self.__audioModel.updated.connect(self.__rebuildUI)
		self.__sliderBox = None
		self.__sliderGrid = QtGui.QGridLayout(self.__ui)
		self.__rootWidget = None

	def __rebuildUI(self):
		if self.__rootWidget is not None:
			self.__rootWidget.setParent(None)
			self.__rootWidget.deleteLater()
		self.__rootWidget = QtGui.QWidget()
		self.__sliderGrid.addWidget(self.__rootWidget)
		self.__sliderBox = QtGui.QVBoxLayout(self.__rootWidget)
		self.__sliderBox.setMargin(6)
		self.__sliderBox.setSpacing(0)
		audioChannels = self.__audioModel.getChannels()
		for channel in audioChannels:
			verLayout = QtGui.QVBoxLayout()

			label = QtGui.QLabel()
			label.setText(channel[0 : 1].upper() + channel[1 :] + ' Volume:')
			verLayout.addWidget(label)
			slider = QtGui.QSlider()
			slider.setObjectName(channel + '_slider')
			slider.setOrientation(QtCore.Qt.Horizontal)
			slider.setTickPosition(QtGui.QSlider.TicksBelow)
			slider.setTickInterval(10)
			slider.setToolTip('Volume of ' + channel)
			verLayout.addWidget(slider)
			verLayout.setSpacing(0)
			verLayout.setMargin(6)
			verLayout.addStretch()
			
			horLayout = QtGui.QHBoxLayout()
			horLayout.setSpacing(6)
			horLayout.addLayout(verLayout)
			spinbox = QtGui.QSpinBox()
			spinbox.setObjectName(channel + '_spinbox')
			horLayout.addWidget(spinbox)
			
			self.__settingsManager.connectSetting(channel + '_volume', slider)
			self.__settingsManager.connectSetting(channel + '_volume', spinbox)

			self.__sliderBox.addLayout(horLayout)
		self.__sliderBox.addStretch(1)

