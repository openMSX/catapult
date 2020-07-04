#!/usr/bin/env python

import os.path
import sys
from PyQt5 import QtCore, QtWidgets, QtGui
from openmsx_utils import tclEscape, EscapedStr

#Is this a version for the openMSX-CD ?
openmsxcd = False
for i in sys.argv:
	if i == '--cd':
		openmsxcd = True

# Application info must be set before the "preferences" module is imported.
# Since many different modules might import "preferences", we perform the
# setup before any Catapult modules are imported.
app = QtWidgets.QApplication(sys.argv)
app.setOrganizationName('openMSX Team')
app.setOrganizationDomain('openmsx.org')
app.setApplicationName('openMSX Catapult')

if sys.platform == 'darwin':
	# Determine app folder location.
	appPath = os.path.abspath(sys.argv[0]).split('/')
	while appPath:
		pathElem = appPath.pop()
		if pathElem == 'Contents':
			break
	if appPath:
		appDir = '/'.join(appPath)
		# Change working dir to resource dir, so icons are loaded correctly.
		success = QtCore.QDir.setCurrent(appDir + '/Contents/Resources/')
		assert success

from editconfig import configDialog
from custom import docDir
from machine import MachineManager
from extension import ExtensionManager
from mediamodel import MediaModel
from connectormodel import ConnectorModel
from media import MediaSwitcher
from connectors import ConnectorPlugger
from audio import AudioMixer
from diskmanipulator import Diskmanipulator
from cheatfinder import Cheatfinder
from trainerselect import TrainerSelect
from softwaredb import SoftwareDB
from autorun import Autorun
from savestatemanager import SaveStateManager
from openmsx_control import ControlBridge, NotConfiguredException
from paletteeditor import PaletteEditor
from inputtext import InputText
from player import PlayState
import settings
from ui_main import Ui_MainWindow

class MainWindow(QtWidgets.QMainWindow):
	# Colors used for different types of log messages:
	logStyle = {
		'info': 0x000000,
		'warning': 0xFF0000,
		'command': 0x000080,
		'default': 0x00FFFF, # selected for unknown levels
		}

	def __init__(self, bridge):
		QtWidgets.QMainWindow.__init__(self)
		self.__bridge = bridge
		self.__ui = ui = Ui_MainWindow()
		self.__connectorModel = connectorModel = ConnectorModel(bridge)
		self.openmsxcd = openmsxcd
		ui.setupUi(self)
		# Added stuff that at the moment will be exclusive to
		# the openMSX-CD
		if openmsxcd:
			ui.action_SoftwareDB = QtWidgets.QAction(self)
			ui.action_SoftwareDB.setObjectName("action_SoftwareDB")
			ui.action_SoftwareDB.setText(QtWidgets.QApplication.translate("MainWindow",
				"Software DB", None, QtWidgets.QApplication.UnicodeUTF8))
			ui.menuTools.addAction(ui.action_SoftwareDB)

			ui.action_Autorun = QtWidgets.QAction(self)
			ui.action_Autorun.setObjectName("action_Autorun")
			ui.action_Autorun.setText(QtWidgets.QApplication.translate("MainWindow",
				"Autorun dialog", None, QtWidgets.QApplication.UnicodeUTF8))
			ui.menuTools.addAction(ui.action_Autorun)

		# Resources that are loaded on demand.
		self.__machineDialog = None
		self.__extensionDialog = None
		self.__aboutDialog = None

		self.__logColours = dict(
			(level, QtGui.QColor(
				(color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF))
			for level, color in self.logStyle.items()
			)

		QtWidgets.qApp.lastWindowClosed.connect(self.closeConnection)
		# We have to let openMSX quit gracefully before quitting Catapult.
		QtWidgets.qApp.setQuitOnLastWindowClosed(False)
		# Register Tcl commands to intercept openMSX exit.
		# This should happen before SettingsManager is instantiated, since that
		# will register "unset renderer" and the exit interception should be
		# in place before the output window is opened.
		bridge.registerInitial(self.__interceptExit)

		self.__settingsManager = settingsManager = settings.SettingsManager(bridge)
		self.__extensionManager = extensionManager = ExtensionManager(
			self, ui, bridge
			)
		self.__machineManager = machineManager = MachineManager(
			self, ui, bridge
			)
		self.__mediaModel = mediaModel = MediaModel(bridge, machineManager)

		self.__diskmanipulator = Diskmanipulator(
			self, mediaModel, machineManager, bridge
			)
		self.__cheatfinder = Cheatfinder(bridge)
		self.__trainerselect = TrainerSelect(bridge)
		if openmsxcd:
			self.__softwaredb = SoftwareDB(bridge)
			self.__autorun = Autorun(self, settingsManager, bridge)
		self.__paletteeditor = PaletteEditor(bridge)
		self.__inputtext = InputText(bridge)
		self.__playState = PlayState(settingsManager, ui)
		self.__saveStateManager = SaveStateManager(bridge, self.__playState)
		self.__connectMenuActions(ui)

		bridge.logLine.connect(self.logLine)
		bridge.registerInitial(self.__setUpSettings)

		# full screen is a special setting, because we want to pop up a dialog
		# before letting the change take effect.
		settingsManager.registerSpecialSetting(
			'fullscreen', self.__updateSpecialSettings
			)
		ui.fullscreen.clicked.connect(self.__goFullscreen)

		ui.extensionButton.clicked.connect(
			extensionManager.chooseExtension)

		ui.machineButton.clicked.connect(machineManager.chooseMachine)

		self.__mediaSwitcher = MediaSwitcher(
			ui, mediaModel, settingsManager, machineManager
			)
		self.__connectorPlugger = ConnectorPlugger(ui, connectorModel,
			settingsManager
			)
		self.__audioMixer = AudioMixer(ui, settingsManager, bridge)
		self.__frameRateTimer = QtCore.QTimer()
		self.__frameRateTimer.setInterval(2000)
		self.__frameRateLabel = QtWidgets.QLabel('')
		ui.statusbar.addWidget(self.__frameRateLabel)

	def __updateSpecialSettings(self, name, message):
		if name == 'fullscreen':
			self.__ui.fullscreen.setChecked(message in ('on', 'true', 'yes'))

	def __goFullscreen(self, value):
		if value:
			reply = QtWidgets.QMessageBox.warning(self,
				self.tr("Going fullscreen"),
				self.tr(
				"<p>Do you really want to go fullscreen?</p>"
				"<p>This will hide Catapult, so make sure"
				" that you know how to disable fullscreen"
				" later on!</p>"
				),
				QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.Yes,
				QtWidgets.QMessageBox.Cancel)
			if reply == QtWidgets.QMessageBox.Cancel:
				self.__ui.fullscreen.setChecked(False)
				#TODO find out why we need to activate the
				#checbox twice before we see this dialog again
				#if we respond with 'Cancel'
			else:
				self.__bridge.sendCommandRaw('set fullscreen on')
		else:
			self.__bridge.sendCommandRaw('set fullscreen off')

	def __setUpSettings(self):
		'''Things that should be done after the connection is established
		This is mostly registering and connecting settings.
		'''
		# Some complex settings that need their UI elements to be configured...
		# we need to register and connect them here since we need to
		# have e.g. the sliders set to the correct minimum/maximum by
		# the openmsx_info command first (that's what I mean with
		# configuring the UI elements). Otherwise it is possible that
		# the setting will try to set the slider to a value not yet
		# allowed
		# Triggering an valuechanged signal that sets the openmsx to
		# the wrong value. This was the case when the noise was set to
		# 3.0 and the slider only went up until 0.99 since the
		# slider was not yet configured...
		# The same goes for practically all settings.
		settingsManager = self.__settingsManager
		ui = self.__ui

		# video settings
		settingsManager.registerSetting('gamma', settings.FloatSetting)
		settingsManager.connectSetting('gamma', ui.gammaSlider)
		settingsManager.connectSetting('gamma', ui.gammaSpinBox)
		settingsManager.registerSetting('brightness', settings.FloatSetting)
		settingsManager.connectSetting('brightness', ui.brightnessSlider)
		settingsManager.connectSetting('brightness', ui.brightnessSpinBox)
		settingsManager.registerSetting('contrast', settings.FloatSetting)
		settingsManager.connectSetting('contrast', ui.contrastSlider)
		settingsManager.connectSetting('contrast', ui.contrastSpinBox)
		settingsManager.registerSetting('noise', settings.FloatSetting)
		settingsManager.connectSetting('noise', ui.noiseSlider)
		settingsManager.connectSetting('noise', ui.noiseSpinBox)

		settingsManager.registerSetting('scanline', settings.IntegerSetting)
		settingsManager.connectSetting('scanline', ui.scanlineSlider)
		settingsManager.connectSetting('scanline', ui.scanlineSpinBox)
		settingsManager.registerSetting('blur', settings.IntegerSetting)
		settingsManager.connectSetting('blur', ui.blurSlider)
		settingsManager.connectSetting('blur', ui.blurSpinBox)
		settingsManager.registerSetting('glow', settings.IntegerSetting)
		settingsManager.connectSetting('glow', ui.glowSlider)
		settingsManager.connectSetting('glow', ui.glowSpinBox)

		settingsManager.registerSetting('scale_factor', settings.IntegerSetting)
		settingsManager.connectSetting('scale_factor', ui.scaleFactorSpinBox)
		settingsManager.registerSetting('deinterlace', settings.BooleanSetting)
		settingsManager.connectSetting('deinterlace', ui.deinterlace)
		settingsManager.registerSetting('limitsprites', settings.BooleanSetting)
		settingsManager.connectSetting('limitsprites', ui.limitsprites)
		settingsManager.registerSetting('scale_algorithm', settings.EnumSetting)
		settingsManager.connectSetting('scale_algorithm', ui.scalealgorithmComboBox)
		settingsManager.registerSetting('videosource', settings.EnumSetting)
		settingsManager.connectSetting('videosource', ui.videosourceComboBox)
		settingsManager.registerSetting('vsync', settings.BooleanSetting)
		settingsManager.connectSetting('vsync', ui.vsync)
		settingsManager.registerSetting('renderer', settings.EnumSetting)
		settingsManager.connectSetting('renderer', ui.rendererComboBox)
		settingsManager.registerSetting('display_deform', settings.EnumSetting)
		settingsManager.connectSetting('display_deform', ui.displaydeformComboBox)

		# misc settings
		settingsManager.registerSetting('speed', settings.IntegerSetting)
		settingsManager.connectSetting('speed', ui.speedSlider)
		settingsManager.connectSetting('speed', ui.speedSpinBox)
		ui.normalSpeedButton.clicked.connect(
			lambda: settingsManager.restoreToDefault('speed'))
		settingsManager.registerSetting('fastforward', settings.BooleanSetting)
		settingsManager.connectSetting('fastforward', ui.limitSpeedCheckBox)
		settingsManager.registerSetting('fullspeedwhenloading',
			settings.BooleanSetting)
		settingsManager.connectSetting('fullspeedwhenloading',
			ui.fullSpeedWhenLoadingCheckBox)
		settingsManager.registerSetting('minframeskip', settings.IntegerSetting)
		settingsManager.connectSetting('minframeskip', ui.minFrameSkipSpinBox)
		ui.resetMinFrameSkipButton.clicked.connect(
			lambda: settingsManager.restoreToDefault('minframeskip'))
		settingsManager.registerSetting('maxframeskip', settings.IntegerSetting)
		settingsManager.connectSetting('maxframeskip', ui.maxFrameSkipSpinBox)
		ui.resetMaxFrameSkipButton.clicked.connect(
			lambda: settingsManager.restoreToDefault('maxframeskip'))
		settingsManager.registerSetting('z80_freq', settings.IntegerSetting)
		# TODO: Z80 frequency can change due to MSX software (when it's locked)
		# display the actual frequency when it's locked, not the setting
		# (but may require openMSX changes to notify about frequency change,
		# otherwise we would have to poll for "machine_info z80_freq")
		settingsManager.connectSetting('z80_freq', ui.Z80FrequencySpinBox)
		settingsManager.connectSetting('z80_freq', ui.Z80FrequencySlider)
		settingsManager.registerSetting('z80_freq_locked', settings.BooleanSetting)
		settingsManager.connectSetting('z80_freq_locked', ui.Z80FrequencyLockCheckBox)
		ui.resetZ80FrequencyButton.clicked.connect(
			lambda: settingsManager.restoreToDefault('z80_freq'))
		settingsManager.registerSetting('r800_freq', settings.IntegerSetting)
		settingsManager.connectSetting('r800_freq', ui.R800FrequencySpinBox)
		settingsManager.connectSetting('r800_freq', ui.R800FrequencySlider)
		settingsManager.registerSetting('r800_freq_locked', settings.BooleanSetting)
		settingsManager.connectSetting('r800_freq_locked',
			ui.R800FrequencyLockCheckBox)
		ui.resetR800FrequencyButton.clicked.connect(
			lambda: settingsManager.restoreToDefault('r800_freq'))

		# menu setting(s)
		settingsManager.registerSetting('save_settings_on_exit',
			settings.BooleanSetting)
		settingsManager.connectSetting('save_settings_on_exit',
			ui.action_AutoSaveSettings)

		###### non standard settings

		# monitor type
		# TODO: settings implemented in TCL don't have a way to sync
		# back...
		def monitorTypeListReply(*words):
			combo = self.__ui.monitorTypeComboBox
			for word in sorted(words):
				combo.addItem(word.replace('_', ' '))
			# hardcoding to start on normal, because this setting
			# cannot be saved anyway
			index = combo.findText('normal')
			combo.setCurrentIndex(index)

		self.__bridge.command('monitor_type', '-list')(
			monitorTypeListReply
			)

		def monitorTypeChanged(newType):
			self.__bridge.command(
				'monitor_type', str(newType.replace(' ', '_'))
				)()

		self.__ui.monitorTypeComboBox.activated.connect(lambda index: monitorTypeChanged(self.__ui.monitorTypeComboBox.currentText()))

		###### other stuff
		self.__frameRateTimer.timeout.connect(
			lambda: self.__bridge.command('openmsx_info', 'fps')(
				self.__updateFrameRateLabel, None
				)
			)
		self.__playState.getVisibleSetting().valueChanged.connect(
			self.__visibilityChanged
			)

	def __connectMenuActions(self, ui):
		'''Connect actions to methods.
		For some reason, on_*_triggered methods are called twice unless
		they have an @QtCore.pyqtSignature decoration. Unfortunately,
		we have to support Python 2.3, which does not have decoration.
		'''
		for action, func in (
			# The action is only triggered when Quit is selected from the menu,
			# not when the main application window is closed. Therefore we
			# unify both flows by closing the windows, which will indirectly
			# lead to a quit.
			(ui.action_Quit, QtWidgets.qApp.closeAllWindows),
			(ui.action_SaveSettings, self.__saveSettings),
			(ui.action_SaveSettingsAs, self.__saveSettingsAs),
			(ui.action_LoadSettings, self.__loadSettings),
			(ui.action_QuickLoadState, self.__quickLoadState),
			(ui.action_QuickSaveState, self.__quickSaveState),
			(ui.action_LoadState, self.__loadState),
			(ui.action_SaveState, self.__saveState),
			(ui.action_EditConfiguration, configDialog.show),
			(ui.action_Diskmanipulator, self.__diskmanipulator.show),
			(ui.action_CheatFinder, self.__cheatfinder.show),
			(ui.action_TrainerSelect, self.__trainerselect.show),
			(ui.action_PaletteEditor, self.__paletteeditor.show),
			(ui.action_InputText, self.__inputtext.show),
			(ui.action_HelpSetup, self.showHelpSetup),
			(ui.action_HelpUser, self.showHelpUser),
			(ui.action_AboutCatapult, self.showAboutDialog),
			(ui.action_AboutQt, QtWidgets.qApp.aboutQt),
			):
			action.triggered.connect(func)
		if openmsxcd:
			for action, func in (
				(ui.action_Autorun, self.__autorun.show),
				(ui.action_SoftwareDB, self.__softwaredb.show),
				):
				action.triggered.connect(func)

	def __interceptExit(self):
		'''Redefines the "exit" command so openMSX will stop instead of exit
		when the window is closed or the quit hotkey is used.
		'''
		# TODO: On Mac OS X, if the user selects Quit from the dock menu,
		#       openMSX will be marked as not responding.
		# TODO: If the user quits openMSX with a hotkey, should that just
		#       close the window or quit Catapult as well?
		#       For example on Mac, we might use Cmd-Q to quit openMSX and
		#       Catapult, while Cmd-W only closes the openMSX window.
		self.__bridge.sendCommandRaw('rename exit exit_process')
		self.__bridge.sendCommandRaw(
			'proc exit {} { set ::renderer none ; set ::power off }'
			)

	def __updateFrameRateLabel(self, value):
		self.__frameRateLabel.setText(str(round(float(value), 1)) + " fps")

	def __visibilityChanged(self, value):
		if value:
			self.__frameRateTimer.start()
		#	self.__frameRateTimer.stop() # uncomment to disable fps polling
		else:
			self.__frameRateTimer.stop()
			self.__frameRateLabel.setText('')

	def consoleReply(self, reply):
		if reply.endswith('\n'):
			reply = reply[ : -1]
		self.logLine('command', reply)

	def getPlayState(self):
		return self.__playState

	# Slots:

	def closeEvent(self, event):
		print(" QtWidgets.QMainWindow.closeEvent(self, event)")
		QtWidgets.QMainWindow.closeEvent(self, event)

	def close(self):
		# [Manuel] is the following log line correct??
		print(" QtWidgets.QMainWindow.close(self)")
		QtWidgets.QMainWindow.close(self)

	def on_playButton_clicked(self):
		self.__playState.setState(PlayState.play)

	def on_pauseButton_clicked(self):
		self.__playState.setState(PlayState.pause)

	def on_stopButton_clicked(self):
		self.__playState.setState(PlayState.stop)

	def on_forwardButton_clicked(self):
		self.__playState.setState(PlayState.forward)

	def on_resetButton_clicked(self):
		self.__bridge.command('reset')()

	def on_consoleLineEdit_returnPressed(self):
		line = self.__ui.consoleLineEdit.text()
		self.logLine('command', '> %s' % line)
		self.__ui.consoleLineEdit.clear()
		self.__bridge.sendCommandRaw(line, self.consoleReply)

	def chooseMachine(self):
		dialog = self.__machineDialog
		if dialog is None:
			self.__machineDialog = dialog = QtWidgets.QDialog(
				self, QtCore.Qt.Dialog | QtCore.Qt.WindowTitleHint
				)
			# Setup UI made in Qt Designer.
			from ui_machine import Ui_Dialog
			ui = Ui_Dialog()
			ui.setupUi(dialog)
		dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	def chooseExtension(self):
		dialog = self.__extensionDialog
		if dialog is None:
			self.__extensionDialog = dialog = QtWidgets.QDialog(
				self, QtCore.Qt.Dialog | QtCore.Qt.WindowTitleHint
				)
			# Setup UI made in Qt Designer.
			from ui_extension import Ui_Dialog
			ui = Ui_Dialog()
			ui.setupUi(dialog)
		dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	def logLine(self, level, message):
		text = self.__ui.logText
		text.setTextColor(
			self.__logColours.get(str(level), self.__logColours['default'])
			)
		text.append(message)

	def closeConnection(self):
		# wrap in lambda to avoid setting a builtin func as callback
		# which is not appreciated by the command method of the bridge
		self.__bridge.closeConnection(lambda: QtWidgets.qApp.quit())

	def __saveSettings(self):
		self.__bridge.command('save_settings')()

	def __saveSettingsAs(self):
		settingsFile = QtWidgets.QFileDialog.getSaveFileName(
			self.__ui.centralwidget, 'Select openMSX Settings File',
			QtCore.QDir.homePath(),
			'openMSX Settings Files (*.xml);;All Files (*)',
			None #, 0
			)
		if settingsFile != '':
			self.__bridge.command('save_settings',
					EscapedStr(tclEscape(settingsFile)))(
					None,
					lambda message: self.__generalFailHandler(
						message, 'Problem Saving Settings'
						)
					)

	def __loadSettings(self):
		settingsFile = QtWidgets.QFileDialog.getOpenFileName(
			self.__ui.centralwidget, 'Select openMSX Settings File',
			QtCore.QDir.homePath(),
			'openMSX Settings Files (*.xml);;All Files (*)',
			None #, 0
			)
		if settingsFile != '':
			self.__bridge.command('set', '__tmp', '$renderer;',
				'load_settings',
				EscapedStr(tclEscape(settingsFile)) + ';',
				'set', 'renderer', '$__tmp'
				)(
					None,
					lambda message: self.__generalFailHandler(
						message, 'Problem Loading Settings'
						)
				)

	def __loadSettingsFailedHandler(self, message):
		messageBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
			'Problem Loading Settings', message, QtWidgets.QMessageBox.Ok,
			self.__ui.centralwidget
			)
		messageBox.show()

	def __quickLoadState(self):
		# TODO: when loading fails, while state was STOP,
		# you see a nasty flicker (openMSX window becomes
		# visible for a short amount of time). Fix this!

		# save old play state
		state = self.__playState.getState()
		# set to play *before* loading the state
		self.__playState.setState(PlayState.play)
		self.__bridge.command('loadstate')(
			None,
			lambda message: failHelper(message)
		)
		def failHelper(message):
			# failed, restore play state
			self.__playState.setState(state)
			self.__generalFailHandler(
				message, 'Problem quick-loading state'
			)

	def __quickSaveState(self):
		self.__bridge.command('savestate')(
			None,
			lambda message: self.__generalFailHandler(
				message, 'Problem quick-saving state'
				)
		)

	def __loadState(self):
		self.__saveStateManager.exec_('load')

	def __saveState(self):
		self.__saveStateManager.exec_('save')

	def __generalFailHandler(self, message, title):
		messageBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
			title, message, QtWidgets.QMessageBox.Ok,
			self.__ui.centralwidget
			)
		messageBox.show()

	def showHelpSetup(self):
		print('show Setup Guide')
		# TODO: Get a reliable path (by guessing? from openMSX?).
		QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(docDir + '/manual/setup.html'))

	def showHelpUser(self):
		print('show User\'s Manual')
		# TODO: Get a reliable path (by guessing? from openMSX?).
		QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(docDir + '/manual/setup.html'))

	def showAboutDialog(self):
		dialog = self.__aboutDialog
		if dialog is None:
			# TODO: An about dialog should not have minimize and maximize
			#       buttons. Although I'm not asking Qt to show those, I still
			#       get them. Maybe a misunderstanding between Qt and the
			#       window manager (KWin)?
			self.__aboutDialog = dialog = QtWidgets.QDialog(
				self,
				QtCore.Qt.Dialog
				| QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowSystemMenuHint
				)
			# Do not keep openMSX running just because of the About dialog.
			dialog.setAttribute(QtCore.Qt.WA_QuitOnClose, False)
			# Setup UI made in Qt Designer.
			from ui_about import Ui_Dialog
			ui = Ui_Dialog()
			ui.setupUi(dialog)
		dialog.show()
		dialog.raise_()
		dialog.activateWindow()
		#print('%X' % int(dialog.windowFlags()))


if __name__ == '__main__':
	controlBridge = ControlBridge()
	mainWindow = MainWindow(controlBridge)
	done = False
	while not done:
		try:
			controlBridge.openConnection()
			done = True
		except NotConfiguredException:
			configDialog.show(True) # block

	mainWindow.show()

	sys.exit(app.exec_())
