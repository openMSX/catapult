# $Id$

from PyQt4 import QtCore, QtGui
from qt_utils import Signal
import settings

# this model keeps track of which audio devices exist
# (for now it doesn't even need to know which exist, only to pass changes...)
class AudioModel(QtCore.QAbstractListModel):

	deviceRemoved = Signal('QString', 'QString')
	deviceAdded = Signal('QString', 'QString')

	def __init__(self, bridge, settingsManager):
		QtCore.QAbstractListModel.__init__(self)
		self.__bridge = bridge
		self.__settingsManager = settingsManager
#		self.__audioChannels = []
		bridge.registerInitial(self.__initialUpdate)
		bridge.registerUpdate('sounddevice', self.__updateSounddevice)


	def __initialUpdate(self):
		self.__bridge.command('machine_info', 'sounddevice')(
			self.__initialUpdateReply
			)

	def __updateSounddevice(self, device, machineId, updateType):
		if updateType == 'add':
			self.__addDevice(device, machineId)
		elif updateType == 'remove':
			self.__removeDevice(device, machineId)
		else: 
			assert False, 'Unexpected update type'
	
	def __initialUpdateReply(self, *devices):
#		self.__audioChannels.append('master')
		self.__settingsManager.registerSetting('master_volume', 
			settings.IntegerSetting
			)
		self.deviceAdded.emit('master', '')
		# TODO: is 'machine1' a valid assumption??
		for device in devices:
			self.__addDevice(device, 'machine1')

	def __addDevice(self, device, machineId):
#		self.__audioChannels.append(device)
		self.__settingsManager.registerSetting(
			machineId + '::' + device + '_volume', settings.IntegerSetting
			)
		self.deviceAdded.emit(device, machineId)

	def __removeDevice(self, device, machineId):
		self.__settingsManager.unregisterSetting(
			machineId + '::' + device + '_volume'
			)
#		self.__audioChannels.remove(device)
		self.deviceRemoved.emit(device, machineId)

# TODO: introduce a scrollarea to prevent the window from resizing with large
# amounts of channels
# TODO: add stretch, in case of very short lists of channels.
class AudioMixer(QtCore.QObject):

	def __init__(self, ui, settingsManager, bridge):
		QtCore.QObject.__init__(self)
		self.__audioModel = AudioModel(bridge, settingsManager)
		self.__ui = ui
		self.__settingsManager = settingsManager

		self.__sliderItemMap = {}

		self.__sliderBox = QtGui.QVBoxLayout(self.__ui)
		self.__sliderBox.setMargin(6)
		self.__sliderBox.setSpacing(0)
		
		self.__audioModel.deviceRemoved.connect(self.__removeChannel)
		self.__audioModel.deviceAdded.connect(self.__addChannel)

	def __addChannel(self, channel, machineId):
		channel = str(channel)
		machineId = str(machineId)
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
		verLayout.setMargin(0)
		verLayout.addStretch()
			
		itemWidget = QtGui.QWidget()
		itemWidget.setContentsMargins(0, 0, 0, 0)
		
		horLayout = QtGui.QHBoxLayout(itemWidget)
		horLayout.setSpacing(6)
		horLayout.addLayout(verLayout)
		spinbox = QtGui.QSpinBox()
		spinbox.setObjectName(channel + '_spinbox')
		horLayout.addWidget(spinbox)

		if channel == 'master':
			settingName = 'master_volume'
		else:
			settingName = machineId + '::' + channel + '_volume'
		
		self.__settingsManager.connectSetting(settingName, slider)
		self.__settingsManager.connectSetting(settingName, spinbox)

		self.__sliderItemMap[machineId + '::' + channel] = itemWidget
		self.__sliderBox.addWidget(itemWidget)

	def __removeChannel(self, channel, machineId):
		channel = str(channel)
		machineId = str(machineId)
		itemWidget = self.__sliderItemMap[machineId + '::' + channel]
		self.__sliderBox.removeWidget(itemWidget)
		itemWidget.setParent(None)		
		itemWidget.deleteLater()
