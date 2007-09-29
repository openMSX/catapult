# $Id: cheatfinder.py 7095 2007-09-28 04:16:11Z vampier $

from PyQt4 import QtCore, QtGui
from qt_utils import connect

class TrainerSelect(object):

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
			from ui_trainerselect import Ui_trainerSelect
			ui = Ui_trainerSelect()
			ui.setupUi(dialog)
			self.__ui = ui

			# Connect signals.
			#connect(ui.FindCheatLess, 'clicked()', self.findCheatLess)
			#connect(ui.FindCheatLessEqual, 'clicked()', self.findCheatLessEqual)
			#connect(ui.FindCheatEqual, 'clicked()', self.findCheatEqual)
			#connect(ui.FindCheatNotEqual, 'clicked()', self.findCheatNotEqual)
			#connect(ui.FindCheatMoreEqual, 'clicked()', self.findCheatMoreEqual)
			#connect(ui.FindCheatMore, 'clicked()', self.findCheatMore)
			#connect(ui.FindCheatRestart, 'clicked()', self.findCheatRestart)
			#connect(ui.FindCheatValue, 'clicked()', self.findCheatValue)
			#connect(ui.EmulationTogglePause, 'clicked()', self.emulationTogglePause)
			#connect(ui.EmulationReset, 'clicked()', self.emulationReset)
			connect(ui.cheatSelector, 'activated(QString)', self.fillCheats)

		dialog.show()
		dialog.raise_()
		dialog.activateWindow()
		self.getCheats()
		self.__ui.TrainerTable.hideColumn(2)
		self.__ui.TrainerTable.horizontalHeader().setStretchLastSection(True)
		self.__ui.TrainerTable.horizontalHeader().hide()
		self.__ui.TrainerTable.verticalHeader().hide()
		self.__ui.TrainerTable.setColumnWidth(0,24)

	def getCheats(self):
		self.__bridge.command('array','names','::__trainers')(self.__fillCheats)
		
	def __fillCheats(self, *words):
		words = sorted(words)
		text = self.__ui.cheatSelector 
		for cheats in words[ : -1]:
			text.addItem(cheats)
		#print 'Selected Index :: ' + text.currentIndex()

	def fillCheats(self):
		selected = self.__ui.cheatSelector.currentText()
		#self.__ui.CheatDisplay.addColumn("item")
		self.__bridge.command('trainer',str(selected))(self.__output)

	def __output(self, *words):

		line = ' '.join(words)
		#text = self.__ui.cheatResults
		#text.append(line)
		#print line
		trainerArray = line.split('\n')
		
		trainerArray = sorted(trainerArray)
		#Create The Table to be filled / Disable sorting and set Gridsize
		self.__ui.TrainerTable.setRowCount( len(trainerArray) - 1 )
		self.__ui.TrainerTable.setSortingEnabled(0)
		self.__ui.TrainerTable.verticalHeader().setResizeMode(
			QtGui.QHeaderView.ResizeToContents 
			)

		row = 0
		for trainerLine in trainerArray[ : -1]:
			trainerIndex 	= trainerLine.rstrip()[:trainerLine.find('[')]
			trainerActive 	= trainerLine.rstrip()[trainerLine.find('['):trainerLine.find(']')+1]
			trainerDesc 	= trainerLine.rstrip()[trainerLine.find(']')+1:]
			
			#oldValItem = QtGui.QTableWidgetItem(cheatVal[1])

			self.__ui.TrainerTable.setItem(row, 2, QtGui.QTableWidgetItem(trainerIndex.title()))
			self.__ui.TrainerTable.setItem(row, 0, QtGui.QTableWidgetItem(trainerActive.title()))
			self.__ui.TrainerTable.setItem(row, 1, QtGui.QTableWidgetItem(trainerDesc.title()))

			row += 1
			print row


		self.__ui.TrainerTable.setSortingEnabled(1)
