# $Id$

from PyQt4 import QtCore, QtGui
#import os.path

from qt_utils import QtSignal, connect

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

			# TODOzz
		dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	def findCheatLess(self):
			print 'Hello world'
			self.__bridge.command('findcheat', 'less')(self.__CheatListReply)
			
	def __CheatListReply(self, *lines):
		for line in lines:
			text = ui.cheatResults
			text.append(line)
			print line
			