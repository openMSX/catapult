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
		self.__sliderMap = {}
		self.__labelMap = {}

		self.__sliderGrid = QtGui.QGridLayout(self.__ui)
		self.__sliderBox = QtGui.QVBoxLayout()
		self.__sliderBox.setMargin(6)
		self.__sliderBox.setSpacing(0)
		self.__sliderGrid.addLayout(self.__sliderBox, 0, 0)

	def __rebuildUI(self):
		for channel in self.__sliderMap:
			slider = self.__sliderMap[channel]
			self.__sliderBox.removeWidget(slider)
			slider.setParent(None) # try to remove references
			slider.deleteLater()
			# TODO: find out if this is causing a memory leak
			#print 'REFERRERS for channel: %s %s' % (channel, gc.get_referrers(slider))
		self.__sliderMap = {}
		for label in self.__labelMap.itervalues():
			self.__sliderBox.removeWidget(label)
			label.setParent(None) # try to remove references
			label.deleteLater()
		self.__labelMap = {}
		audioChannels = self.__audioModel.getChannels()
		for channel in audioChannels:
			self.__labelMap[channel] = label = QtGui.QLabel()
			label.setText(channel + ' volume')
			self.__sliderBox.addWidget(label)
			self.__sliderMap[channel] = slider = QtGui.QSlider()
			slider.setObjectName(channel + '_slider')

			slider.setOrientation(QtCore.Qt.Horizontal)
			slider.setTickPosition(QtGui.QSlider.TicksBelow)
			slider.setTickInterval(10)
			slider.setToolTip('Volume of ' + channel)
			self.__sliderBox.addWidget(slider)
			self.__settingsManager.connectSetting(channel + '_volume', slider)

