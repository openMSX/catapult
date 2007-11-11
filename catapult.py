#!/usr/bin/env python
# $Id$

from PyQt4 import QtCore, QtGui
import os.path, sys

#Is this a version for the openMSX-CD ?
openmsxcd = 1

# Application info must be set before the "preferences" module is imported.
# Since many different modules might import "preferences", we perform the
# setup before any Catapult modules are imported.
app = QtGui.QApplication(sys.argv)
app.setOrganizationName('openMSX Team')
app.setOrganizationDomain('openmsx.org')
app.setApplicationName('openMSX Catapult')

if sys.platform == 'darwin':
	# Determine app folder location.
	appPath = os.path.abspath(sys.argv[0]).split('/')
	while True:
		pathElem = appPath.pop()
		if pathElem == 'Contents':
			break
	appDir = '/'.join(appPath)
	# Change working dir to resource dir, so icons are loaded correctly.
	success = QtCore.QDir.setCurrent(appDir + '/Contents/Resources/')
	assert success

from editconfig import configDialog
from custom import docDir
from machine import MachineManager
from extension import ExtensionManager
from mediamodel import MediaModel
from media import MediaSwitcher
from audio import AudioMixer
from diskmanipulator import Diskmanipulator
from cheatfinder import Cheatfinder
from trainerselect import TrainerSelect
from softwaredb import SoftwareDB
from openmsx_control import ControlBridge
from paletteeditor import PaletteEditor
from player import PlayState
from qt_utils import connect
import settings
from ui_main import Ui_MainWindow

class MainWindow(QtGui.QMainWindow):
	# Colors used for different types of log messages:
	logStyle = {
		'info': 0x000000,
		'warning': 0xFF0000,
		'command': 0x000080,
		'default': 0x00FFFF, # selected for unknown levels
		}

	def __init__(self, bridge):
		QtGui.QMainWindow.__init__(self)
		self.__bridge = bridge
		self.__ui = ui = Ui_MainWindow()
		self.__afterConList = []
		self.__mediaModel = mediaModel = MediaModel(bridge)
		ui.setupUi(self)
		# Added stuff that at the moment will be exclusive to
		# the openMSX-CD
		if openmsxcd:
			ui.action_SoftwareDB = QtGui.QAction(self)
			ui.action_SoftwareDB.setObjectName("action_SoftwareDB")
			ui.action_SoftwareDB.setText(QtGui.QApplication.translate("MainWindow",
				"Software DB", None, QtGui.QApplication.UnicodeUTF8))
			ui.menuTools.addAction(ui.action_SoftwareDB)

		# Resources that are loaded on demand.
		self.__machineDialog = None
		self.__extensionDialog = None
		self.__aboutDialog = None
		self.__assistentClient = None

		self.__logColours = dict(
			( level, QtGui.QColor(
				(color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF ) )
			for level, color in self.logStyle.iteritems()
			)

		connect(QtGui.qApp, 'lastWindowClosed()', self.closeConnection)
		# We have to let openMSX quit gracefully before quitting Catapult.
		QtGui.qApp.setQuitOnLastWindowClosed(False)
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
			self, ui.machineBox, bridge
			)

		self.__diskmanipulator = Diskmanipulator(mediaModel, bridge)
		self.__cheatfinder = Cheatfinder(bridge)
		self.__trainerselect = TrainerSelect(bridge)
		self.__softwaredb = SoftwareDB(bridge)
		self.__paletteeditor = PaletteEditor(bridge)
		self.__connectMenuActions(ui)

		bridge.logLine.connect(self.logLine)
		#

		settingsManager.registerSetting('scanline', settings.IntegerSetting)
		settingsManager.connectSetting('scanline', ui.scanlineSlider)
		settingsManager.connectSetting('scanline', ui.scanlineSpinBox)
		settingsManager.registerSetting('blur', settings.IntegerSetting)
		settingsManager.connectSetting('blur', ui.blurSlider)
		settingsManager.connectSetting('blur', ui.blurSpinBox)
		settingsManager.registerSetting('glow', settings.IntegerSetting)
		settingsManager.connectSetting('glow', ui.glowSlider)
		settingsManager.connectSetting('glow', ui.glowSpinBox)

		settingsManager.registerSetting('fullscreen', settings.BooleanSetting)
		settingsManager.registerForUpdates('fullscreen', self)
		ui = self.__ui
		connect(ui.fullscreen, 'stateChanged(int)', self.__goFullscreen)

		# Some enum settings
		for setting, widget in (
				('videosource', ui.videosourceComboBox),
				('scale_algorithm', ui.scalealgorithmComboBox),
				('display_deform', ui.displaydeformComboBox),
				('renderer', ui.rendererComboBox)
				):
			settingsManager.registerSetting(setting,
				settings.EnumSetting)
			settingsManager.registerForUpdates(setting, self)
			connect(widget, 'currentIndexChanged(QString)',
				lambda x, setting = setting: self.__dispatchCombo(setting,x) )


		self.__playState = PlayState(settingsManager, ui)

		connect(ui.extensionButton, 'clicked()',
			extensionManager.chooseExtension)

		connect(ui.machineButton, 'clicked()', machineManager.chooseMachine)

		connect(ui.sendButton, 'clicked()', self.__typeInputText)
		connect(ui.clearButton, 'clicked()', self.__clearInputText)

		self.__mediaSwitcher = MediaSwitcher(ui, mediaModel)
		self.__audioMixer = AudioMixer(ui.audioTab, settingsManager, bridge)
		# the following property is missing in Designer somehow
		ui.inputText.setWordWrapMode(QtGui.QTextOption.WrapAnywhere)

	def __dispatchFloatSpinBox(self, name, value):
		print "spinbox initiated command: set " + str(name) + "  " + str(value)
		self.__settingsManager.set(name, float(value))

	def __dispatchFloatSlider(self, name, value):
		print "slider initiated command: set " + str(name) + "  " + str(float(value)/100)
		self.__settingsManager.set(name, float(value)/100)

	def __dispatchCombo(self, name, value):
		print "combox initiated command: set " + name + "  " + value
		self.__bridge.command('set',
			name, value
			)()

	def updatedBoolean(self, name, value):
		print "Boolean setting changed :" + str(name) +" = " + str(value)
		if str(name) == 'fullscreen':
			state = QtCore.Qt.Unchecked
			if value:
				state = QtCore.Qt.Checked
			self.__ui.fullscreen.setCheckState(state)

	def updatedEnum(self, name, value):
		print "Enum setting changed :" + name +" = " + value
		uimap = {'renderer': self.__ui.rendererComboBox,
			'scale_algorithm': self.__ui.scalealgorithmComboBox,
			'display_deform': self.__ui.displaydeformComboBox,
			'videosource': self.__ui.videosourceComboBox
			}
		widget = uimap[str(name)]
		index = widget.findText(value)
		if index == -1:
			widget.addItem(value)
		else:
			widget.setCurrentIndex(index)

	def updatedInt(self, name, value):
		print "Int setting changed :" + str(name) + " = " + str(value)

	def updatedFloat(self, name, value):
		print "Float setting changed :" + str(name) + " = " + str(value)
		ui = self.__ui
		uimap = {
			'gamma': ( ui.gammaSlider, ui.gammaSpinBox),
			'brightness': ( ui.brightnessSlider, ui.brightnessSpinBox),
			'contrast': ( ui.contrastSlider, ui.contrastSpinBox),
			'noise': ( ui.noiseSlider, ui.noiseSpinBox)
			}
		slider, spinner = uimap[str(name)]
		val = float(value)
		spinner.setValue(val)
		slider.setValue(int(val*100))


	def __goFullscreen(self,value):
		if self.__ui.fullscreen.isChecked():
			reply = QtGui.QMessageBox.warning(self,
				self.tr("Going fullscreen"),
				self.tr(
				"<p>Do you really want to go fullscreen?</p>"
				"<p>This will hide catapult, so make sure"
				" that you know how to disable fullscreen"
				" later on</p>"
				),
				self.tr("&Cancel"),
				self.tr("Continue"))
			if reply == 0:
				self.__ui.fullscreen.setChecked(False)
				#TODO find out why we need to activate the
				#checbox twice before we see this dialog again
				#if we respond with 'Cancel'
			else:
				self.__bridge.sendCommandRaw('set fullscreen on')

	def afterConnectionMade(self):
		self.__afterConList = []
		#eunmsettings for comboboxes
		for item in ('renderer', 'display_deform',
			'videosource', 'scale_algorithm'):
			self.__afterConList.append(item)
			self.__bridge.command('openmsx_info',
				'setting', item
				)(
				self.__fillComboBox,
				self.__infofailed
				)
		#floatsettings for sliders+spinboxes
		for item in ('gamma', 'brightness', 'contrast', 'noise'): 
			self.__afterConList.append(item)
			self.__bridge.command('openmsx_info',
				'setting', item
				)(
				self.__configSliders,
				self.__infofailed
				)
		# Some float settings
		# we need to register them here since we need to have the
		# sliders set to the correct minimum/maximum by the
		# openmsx_info command first. Otherwise it is possible that the
		# setting will try to set the slider to a value not yet allowed
		# triggerring an valuechanged signal that sets the openmsx to
		# the wrong value. This was the case when the noise was set to
		# 3.0 and the slider only went up until 0.99 since the
		# openmsx_info was not yet used...
		ui = self.__ui
		for setting, slider, spinner in (
			('gamma', ui.gammaSlider, ui.gammaSpinBox),
			('brightness', ui.brightnessSlider, ui.brightnessSpinBox),
			('contrast', ui.contrastSlider, ui.contrastSpinBox),
			('noise', ui.noiseSlider, ui.noiseSpinBox)
			):
			self.__settingsManager.registerSetting(setting,
                                settings.FloatSetting)
			self.__settingsManager.registerForUpdates(setting, self)
			connect(slider, 'valueChanged(int)',
				lambda x, setting = setting:
					self.__dispatchFloatSlider(setting,x) )
			connect(spinner, 'valueChanged(double)',
				lambda x, setting = setting:
					self.__dispatchFloatSpinBox(setting,x) )
		

	def __infofailed(self, name, message):
		print 'Failed to get info about %s : %s' % (
			name, message
			)

	def __fillComboBox(self, *items):
		element = self.__afterConList.pop(0)
		uimap = {
			'renderer': self.__ui.rendererComboBox,
			'display_deform': self.__ui.displaydeformComboBox,
			'scale_algorithm': self.__ui.scalealgorithmComboBox,
			'videosource': self.__ui.videosourceComboBox
			}
		uiElement = uimap[ element ]
		for item in items[2].split(' '):
			#combo = self.__ui.rendererComboBox
			qitem = QtCore.QString(item)
			#maybe element is already in combobox due
			#to settingchanged signal
			if uiElement.findText(qitem) == -1:
				uiElement.addItem(qitem)

	def __configSliders(self, *items):
		element = self.__afterConList.pop(0)
		print '------------------------------------'
		print element
		print items
		print '------------------------------------'
		uimap = {
			'gamma': (self.__ui.gammaSlider,
				self.__ui.gammaSpinBox ),
			'brightness': (self.__ui.brightnessSlider,
				self.__ui.brightnessSpinBox ),
			'contrast': (self.__ui.contrastSlider,
				self.__ui.contrastSpinBox ),
			'noise': (self.__ui.noiseSlider,
				self.__ui.noiseSpinBox )
			}
		uiSlider, uiSpinner = uimap[ element ]
		mini, maxi = items[2].split(' ')
		curval = float(items[1])
		uiSlider.setMinimum( int(float(mini)*100) )
		uiSlider.setMaximum( int(float(maxi)*100) )
		uiSlider.setValue( int(curval*100) )
		uiSpinner.setMinimum( float(mini) )
		uiSpinner.setMaximum( float(maxi) )
		uiSpinner.setMaximum( float(maxi) )
		uiSpinner.setSingleStep( 0.01 )
		uiSpinner.setValue( curval )


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
			( ui.action_Quit, QtGui.qApp.closeAllWindows ),
			( ui.action_EditConfiguration, configDialog.show ),
			( ui.action_Diskmanipulator, self.__diskmanipulator.show ),
			( ui.action_CheatFinder, self.__cheatfinder.show ),
			( ui.action_TrainerSelect, self.__trainerselect.show ),			
			( ui.action_PaletteEditor, self.__paletteeditor.show ),
			( ui.action_SoftwareDB, self.__softwaredb.show ),
			( ui.action_HelpSetup, self.showHelpSetup ),
			( ui.action_HelpUser, self.showHelpUser ),
			( ui.action_AboutCatapult, self.showAboutDialog ),
			( ui.action_AboutQt, QtGui.qApp.aboutQt ),
			):
			connect(action, 'triggered(bool)', func)

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

	def __typeInputText(self):
		#TODO: Capture Regular expressions chars like { [ at the beginning of a line
		strText = self.__ui.inputText.toPlainText()
		strText.replace('\\', '\\\\')
		strText.replace('\n', '\\r').replace('$', '\$')
		strText.replace('"', '\\"').replace('\'', '\\\'')
		self.__bridge.sendCommandRaw('type "%s"' % strText)

	def __clearInputText(self):
		self.__ui.inputText.clear()

	def consoleReply(self, reply):
		if reply.endswith('\n'):
			reply = reply[ : -1]
		self.logLine('command', reply)

	# Slots:

	@QtCore.pyqtSignature('')
	def on_playButton_clicked(self):
		self.__playState.setState(PlayState.play)

	@QtCore.pyqtSignature('')
	def on_pauseButton_clicked(self):
		self.__playState.setState(PlayState.pause)

	@QtCore.pyqtSignature('')
	def on_stopButton_clicked(self):
		self.__playState.setState(PlayState.stop)

	@QtCore.pyqtSignature('')
	def on_forwardButton_clicked(self):
		self.__playState.setState(PlayState.forward)

	@QtCore.pyqtSignature('')
	def on_resetButton_clicked(self):
		self.__bridge.command('reset')()

	@QtCore.pyqtSignature('')
	def on_consoleLineEdit_returnPressed(self):
		line = self.__ui.consoleLineEdit.text()
		self.logLine('command', '> %s' % line)
		self.__ui.consoleLineEdit.clear()
		self.__bridge.sendCommandRaw(line, self.consoleReply)

	def chooseMachine(self):
		dialog = self.__machineDialog
		if dialog is None:
			self.__machineDialog = dialog = QtGui.QDialog(
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
			self.__extensionDialog = dialog = QtGui.QDialog(
				self, QtCore.Qt.Dialog | QtCore.Qt.WindowTitleHint
				)
			# Setup UI made in Qt Designer.
			from ui_extension import Ui_Dialog
			ui = Ui_Dialog()
			ui.setupUi(dialog)
		dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	@QtCore.pyqtSignature('QString, QString')
	def logLine(self, level, message):
		text = self.__ui.logText
		text.setTextColor(
			self.__logColours.get(str(level), self.__logColours['default'])
			)
		text.append(message)

	@QtCore.pyqtSignature('')
	def closeConnection(self):
		self.__bridge.closeConnection(QtGui.qApp.quit)

	def __getAssistentClient(self):
		if self.__assistentClient is None:
			from PyQt4.QtAssistant import QAssistantClient
			# Note: The string parameter is the path to look for the
			#       Qt Assistent executable.
			#       Empty string means use OS search path.
			# TODO: Is it safe to assume Qt Assistent is always in the path?
			#       What happens if it is not?
			self.__assistentClient = QAssistantClient('')
		return self.__assistentClient

	@QtCore.pyqtSignature('')
	def showHelpSetup(self):
		print 'show Setup Guide'
		client = self.__getAssistentClient()
		# TODO: Make metadata documents to customize Qt Assistant for openMSX.
		# TODO: Get a reliable path (by guessing? from openMSX?).
		client.showPage(docDir + '/manual/setup.html')

	@QtCore.pyqtSignature('')
	def showHelpUser(self):
		print 'show User\'s Manual'
		client = self.__getAssistentClient()
		# TODO: Get a reliable path (by guessing? from openMSX?).
		client.showPage(docDir + '/manual/user.html')

	@QtCore.pyqtSignature('')
	def showAboutDialog(self):
		dialog = self.__aboutDialog
		if dialog is None:
			# TODO: An about dialog should not have minimize and maximize
			#       buttons. Although I'm not asking Qt to show those, I still
			#       get them. Maybe a misunderstanding between Qt and the
			#       window manager (KWin)?
			self.__aboutDialog = dialog = QtGui.QDialog(
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
		#print '%X' % int(dialog.windowFlags())


if __name__ == '__main__':
	controlBridge = ControlBridge()
	mainWindow = MainWindow(controlBridge)
	controlBridge.openConnection()
	#quick hack TODO: get this is in beter place!
	#Question: if we open the connection before we
	# create the mainwindow, will this work?
	# I think I need to look into this beacuse of
	# the exit/Tcl remark at line 86
	mainWindow.afterConnectionMade()
	mainWindow.show()

	sys.exit(app.exec_())
