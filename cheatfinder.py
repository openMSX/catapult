# $Id$

from PyQt4 import QtCore, QtGui
#import os.path

from qt_utils import connect

class Cheatfinder(object):

	def __init__(self, bridge):
		self.__cfDialog = None
		self.__ui = None
		self.__bridge = bridge

	def show(self):
		dialog = self.__cfDialog
		if dialog is None:
			self.__cfDialog = dialog = QtGui.QDialog(
				None, # TODO: find a way to get the real parent
				QtCore.Qt.Dialog
				| QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowSystemMenuHint
				)
			# Setup UI made in Qt Designer.
			from ui_cheatfinder import Ui_cheatFinder
			ui = Ui_cheatFinder()
			ui.setupUi(dialog)
			self.__ui = ui

			# Connect signals.
			connect(ui.FindCheatLess, 'clicked()', self.findCheatLess)
			connect(ui.FindCheatLessEqual, 'clicked()', self.findCheatLessEqual)
			connect(ui.FindCheatEqual, 'clicked()', self.findCheatEqual)
			connect(ui.FindCheatNotEqual, 'clicked()', self.findCheatNotEqual)
			connect(ui.FindCheatMoreEqual, 'clicked()', self.findCheatMoreEqual)
			connect(ui.FindCheatMore, 'clicked()', self.findCheatMore)
			connect(ui.FindCheatRestart, 'clicked()', self.findCheatRestart)
			connect(ui.FindCheatValue, 'clicked()', self.findCheatValue)
			
		dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	def findCheatLess(self):
		self.__bridge.command('findcheat', 'less')(self.__CheatListReply)

	def findCheatLessEqual(self):
		self.__bridge.command('findcheat', 'loe')(self.__CheatListReply)

	def findCheatEqual(self):
		self.__bridge.command('findcheat', 'equal')(self.__CheatListReply)

	def findCheatNotEqual(self):
		self.__bridge.command('findcheat', 'notequal')(self.__CheatListReply)

	def findCheatMoreEqual(self):
		self.__bridge.command('findcheat', 'moe')(self.__CheatListReply)

	def findCheatMore(self):
		self.__bridge.command('findcheat', 'more')(self.__CheatListReply)

	def findCheatRestart(self):
		self.__bridge.command('findcheat', '-start')(self.__CheatListReply)

	def findCheatValue(self):
		cheatValue = self.__ui.cheatVal.text()
		print cheatValue
		self.__bridge.command('findcheat', cheatValue)(self.__CheatListReply)

	def __CheatListReply(self, *lines):
		#todo: format output in the window
		for line in lines:
			text = self.__ui.cheatResults
			text.append(line)
