#!/usr/bin/env python
# $Id$

from PyQt4 import QtCore, QtGui
import os.path, sys

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
from media import MediaSwitcher
from openmsx_control import ControlBridge
from player import PlayState
from qt_utils import connect
from settings import SettingsManager
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
		ui.setupUi(self)

		# Resources that are loaded on demand.
		self.__machineDialog = None
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

		self.__connectMenuActions(ui)

		settingsManager = SettingsManager(bridge)
		bridge.logLine.connect(self.logLine)
		settingsManager.connectSetting('scanline', ui.scanlineSlider)
		settingsManager.connectSetting('scanline', ui.scanlineSpinBox)
		settingsManager.connectSetting('blur', ui.blurSlider)
		settingsManager.connectSetting('blur', ui.blurSpinBox)
		settingsManager.connectSetting('glow', ui.glowSlider)
		settingsManager.connectSetting('glow', ui.glowSpinBox)

		self.__playState = PlayState(settingsManager, ui)

		self.__machineManager = machineManager = MachineManager(
			self, ui.machineBox, settingsManager, bridge
			)
		connect(ui.machineButton, 'clicked()', machineManager.chooseMachine)

		self.__mediaSwitcher = MediaSwitcher(ui, bridge)

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
	mainWindow.show()
	sys.exit(app.exec_())
