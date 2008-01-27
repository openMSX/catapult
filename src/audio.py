# $Id$

from PyQt4 import QtCore, QtGui
from qt_utils import Signal, connect
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
		self.__settingsManager.registerSetting('mute',
			settings.BooleanSetting
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
		self.__settingsManager.registerSetting(
			machineId + '::' + device + '_balance', settings.IntegerSetting
			)
		self.deviceAdded.emit(device, machineId)

	def __removeDevice(self, device, machineId):
		self.__settingsManager.unregisterSetting(
			machineId + '::' + device + '_volume'
			)
		self.__settingsManager.unregisterSetting(
			machineId + '::' + device + '_balance'
			)
#		self.__audioChannels.remove(device)
		self.deviceRemoved.emit(device, machineId)

class BalanceSlider(QtGui.QSlider):

	def __init__(self, parent = None):
		QtGui.QSlider.__init__(self, parent)

	# pylint: disable-msg=W0613
	# We don't need the arguments, but Qt defines this interface.
	def mouseDoubleClickEvent(self, event):
		self.setValue(0)

class AudioMixer(QtCore.QObject):

	def __init__(self, ui, settingsManager, bridge):
		QtCore.QObject.__init__(self)
		self.__audioModel = AudioModel(bridge, settingsManager)
		self.__ui = ui
		self.__settingsManager = settingsManager

		self.__audioControlItemMap = {}

		# remove margins of top level gridlayout (cannot be edited in Designer)
		ui.audioTab.layout().setMargin(0)
		# widget that will be controlled by the scrollarea:
		topLevelWidget = ui.topLevelAudioMixerWidget
		# get the layout of this widget and remove margins
		topLevelLayout = topLevelWidget.parentWidget().layout()
		topLevelLayout.setMargin(0)
		# layout where we will put our channels in:
		self.__audioControlItemBox = QtGui.QVBoxLayout(topLevelWidget)
		self.__audioControlItemBox.setMargin(6)
		self.__audioControlItemBox.setSpacing(0)
		# here we have the scrollarea, to make sure the window does not
		# get bigger when we have loads of channels
		scrollArea = QtGui.QScrollArea(ui.audioTab)
		scrollArea.setWidget(topLevelWidget)
		scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		scrollArea.setWidgetResizable(True)
		scrollArea.setFrameStyle(QtGui.QFrame.NoFrame)
		# add it to the layout of the topLevelWidget.
		topLevelLayout.addWidget(scrollArea)

		self.__audioModel.deviceRemoved.connect(self.__removeChannel)
		self.__audioModel.deviceAdded.connect(self.__addChannel)

		ui.advancedAudioSettingsWidget.setVisible(False)
		ui.advancedAudioSettingsButton.setText('Open Advanced Settings...')
		connect(ui.advancedAudioSettingsButton, 'clicked()', self.__toggleAdvSettings)

		bridge.registerInitial(self.__connectSettings)

	def __connectSettings(self):
		settingsManager = self.__settingsManager
		ui = self.__ui
		settingsManager.registerSetting('samples', settings.IntegerSetting)
		settingsManager.connectSetting('samples', ui.samplesSlider)
		settingsManager.connectSetting('samples', ui.samplesSpinBox)
		connect(ui.samplesResetButton, 'clicked()',
			lambda: settingsManager.restoreToDefault('samples'))
		settingsManager.registerSetting('frequency', settings.IntegerSetting)
		settingsManager.connectSetting('frequency', ui.frequencySlider)
		settingsManager.connectSetting('frequency', ui.frequencySpinBox)
		connect(ui.frequencyResetButton, 'clicked()',
			lambda: settingsManager.restoreToDefault('frequency'))
		settingsManager.registerSetting('sound_driver', settings.EnumSetting)
		settingsManager.connectSetting('sound_driver', ui.soundDriverComboBox)
		settingsManager.registerSetting('resampler', settings.EnumSetting)
		settingsManager.connectSetting('resampler', ui.resamplerComboBox)


	def __addChannel(self, channel, machineId):
		channel = str(channel)
		machineId = str(machineId)
		verLayout = QtGui.QVBoxLayout()

		# remove last item, which is the QSpacerItem providing stretch
		self.__audioControlItemBox.takeAt(self.__audioControlItemBox.count() - 1)

		label = QtGui.QLabel()
		label.setText(channel[0 : 1].upper() + channel[1 :] + ' Volume:')
		verLayout.addWidget(label)
		volSlider = QtGui.QSlider()
		volSlider.setObjectName(channel + '_volSlider')
		volSlider.setOrientation(QtCore.Qt.Horizontal)
		volSlider.setTickPosition(QtGui.QSlider.TicksBelow)
		volSlider.setTickInterval(10)
		volSlider.setToolTip('Volume of ' + channel)
		verLayout.addWidget(volSlider)
		verLayout.setSpacing(0)
		verLayout.setMargin(0)
		verLayout.addStretch()

		itemWidget = QtGui.QWidget()
		itemWidget.setContentsMargins(0, 0, 0, 0)

		horLayout = QtGui.QHBoxLayout(itemWidget)
		horLayout.setSpacing(6)
		horLayout.addLayout(verLayout)
		volSpinbox = QtGui.QSpinBox()
		volSpinbox.setObjectName(channel + '_volSpinbox')
		horLayout.addWidget(volSpinbox)

		if channel != 'master':
			balHorLayout = QtGui.QHBoxLayout()
			balHorLayout.addWidget(QtGui.QLabel('L'))
			#balSlider = QtGui.QSlider()
			balSlider = BalanceSlider()
			balSlider.setObjectName(channel + '_balSlider')
			balSlider.setOrientation(QtCore.Qt.Horizontal)
			balSlider.setTickPosition(QtGui.QSlider.TicksBelow)
			balSlider.setTickInterval(25)
			balSlider.setToolTip('Balance of ' + channel + '\n(double-click to center)')
			balSlider.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
			balHorLayout.addWidget(balSlider)
			balHorLayout.addWidget(QtGui.QLabel('R'))
			balVerLayout = QtGui.QVBoxLayout()
			balVerLayout.addWidget(QtGui.QLabel('Balance:'))
			balVerLayout.addLayout(balHorLayout)
			balVerLayout.setSpacing(0)
			balVerLayout.setMargin(0)
			horLayout.addLayout(balVerLayout)
			volSettingName = machineId + '::' + channel + '_volume'
			balSettingName = machineId + '::' + channel + '_balance'
			self.__settingsManager.connectSetting(balSettingName, balSlider)
		else:
			volSettingName = 'master_volume'
			muteCheckBox = QtGui.QCheckBox('mute')
			self.__settingsManager.connectSetting('mute', muteCheckBox)
			horLayout.addWidget(muteCheckBox)

		self.__settingsManager.connectSetting(volSettingName, volSlider)
		self.__settingsManager.connectSetting(volSettingName, volSpinbox)

		self.__audioControlItemMap[machineId + '::' + channel] = itemWidget
		self.__audioControlItemBox.addWidget(itemWidget)

		# add stretch (QSpacerItem) to make sure all stuff remains at the top
		self.__audioControlItemBox.addStretch(10)

	def __removeChannel(self, channel, machineId):
		channel = str(channel)
		machineId = str(machineId)
		itemWidget = self.__audioControlItemMap[machineId + '::' + channel]
		self.__audioControlItemBox.removeWidget(itemWidget)
		itemWidget.setParent(None)
		itemWidget.deleteLater()

	def __toggleAdvSettings(self):
		if self.__ui.advancedAudioSettingsWidget.isHidden():
			self.__ui.advancedAudioSettingsWidget.setVisible(True)
			self.__ui.advancedAudioSettingsButton.setText('Close Advanced Settings...')
		else:
			self.__ui.advancedAudioSettingsWidget.setVisible(False)
			self.__ui.advancedAudioSettingsButton.setText('Open Advanced Settings...')




