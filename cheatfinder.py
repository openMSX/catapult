# $Id$

from PyQt4 import QtCore, QtGui
#from PyQt4.QtGui import *
from qt_utils import connect
from player import PlayState

#import os.path

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
			connect(ui.EmulationTogglePause, 'clicked()', self.emulationTogglePause)
			connect(ui.EmulationReset, 'clicked()', self.emulationReset)
			
		dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	def emulationTogglePause(self):
		self.__bridge.command('toggle', 'pause')(self.__CheatListReply)

	def emulationReset(self):
		self.__bridge.command('reset')(self.__CheatListReply)

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
		self.__bridge.command('findcheat', cheatValue)(self.__CheatListReply)

	def __CheatListReply(self, *words):
		line = ' '.join(words)
		text = self.__ui.cheatResults
		
		palette = self.palette()
		col = QColor()
		col.setRgb( 0xaa, 0xbe, 0xff )
		#self.__ui.label.setPalette( QPalette( col ) )
		
		#Check if no results are found (clear table and display message)
		if line.find('results')>1:
			self.__ui.CheatTable.setRowCount(0)
			text.append(line)

		#Check if results are found
		if line.find('results')<1:
			#Format output to be put into an array
			line = line.replace('->',' ')
			line = line.replace(':',' ')
			line = line.replace('  ',' ')
			line = line.replace(' ',';')
			line = line.replace(';;',';')
			#Put resultset into array
			cheatArray = line.split('\n')

			#Create The Table to be filled / Disable sorting and set Gridsize
			self.__ui.CheatTable.setRowCount( len(cheatArray) - 1 )
			self.__ui.CheatTable.setSortingEnabled(0)
			self.__ui.CheatTable.verticalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents )

			row = 0
			for cheatLine in cheatArray[ : -1]:
				#Create Sub Array
				cheatVal = cheatLine.split(';')

				#Fill Address Value Item
				addrItem = QtGui.QTableWidgetItem(cheatVal[0])
				addrItem.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)
				self.__ui.CheatTable.setItem(row, 0, addrItem)

				#Fill Old Value Item (dec)
				oldValItem = QtGui.QTableWidgetItem(cheatVal[1])
				oldValItem.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)
				self.__ui.CheatTable.setItem(row, 1, oldValItem)

				#Fill New Value Item (dec)
				newValItem = QtGui.QTableWidgetItem(cheatVal[2])
				newValItem.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)
				self.__ui.CheatTable.setItem(row, 2, newValItem)

				row += 1
				#text.append(row+" Results found: Displayed")

			#Enable Sorting
			self.__ui.CheatTable.setSortingEnabled(1)