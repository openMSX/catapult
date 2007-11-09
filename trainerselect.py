# $Id: cheatfinder.py 7095 2007-09-28 04:16:11Z vampier $

from PyQt4 import QtCore, QtGui
from qt_utils import connect

class TrainerSelect(object):

	def __init__(self, bridge):
		self.__cfDialog = None
		self.__ui = None
		self.__bridge = bridge
		self.__selected = ""
		self.__checkbox = []
		self.__spacerItem = None

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

			self.__ui.vboxlayout = QtGui.QVBoxLayout(self.__ui.emptywidget)
			self.__ui.vboxlayout.setObjectName("vboxlayout")

			spacerItem = QtGui.QSpacerItem(20, 40,
				QtGui.QSizePolicy.Minimum,
				QtGui.QSizePolicy.Expanding
				)
			self.__spacerItem = spacerItem
			self.__ui.vboxlayout.addItem(self.__spacerItem)

		dialog.show()
		dialog.raise_()
		dialog.activateWindow()
		self.getCheats()

	def getCheats(self):
		self.__bridge.command(
			'array',
			'names',
			'::__trainers'
			)(self.__fillCheats)
		
	def __fillCheats(self, *words):
		words = sorted(words)
		text = self.__ui.cheatSelector 
		for cheats in words[ : -1]:
			text.addItem(cheats)
		#print 'Selected Index :: ' + text.currentIndex()

	def fillCheats(self):
		self.__selected = self.__ui.cheatSelector.currentText()
		#self.__ui.CheatDisplay.addColumn("item")
		self.__bridge.command(
			'trainer',
			str(self.__selected)
			)(self.__output)

	def __output(self, *words):
		line = ' '.join(words)
		#text = self.__ui.cheatResults
		#text.append(line)
		#print line
		trainerArray = line.split('\n')
		
		trainerArray = sorted(trainerArray)
		#remove all items in the vboxlayout
		for widget in self.__checkbox[:]:
			self.__ui.vboxlayout.removeWidget(widget)
			#TODO: find out if this close() also
			#deletes/free the objects
			widget.close()
		self.__ui.vboxlayout.removeItem(self.__spacerItem)
		self.__checkbox = []

		i = 0
		for trainerLine in trainerArray[ : -1]:
			trainerIndex = trainerLine.rstrip()\
			[:trainerLine.find('[')]

			trainerIndex = trainerIndex.rstrip()

			trainerActive = trainerLine.rstrip()\
			[trainerLine.find('['):trainerLine.find(']')+1]

			trainerDesc = trainerLine.rstrip()\
			[trainerLine.find(']')+1:]

			checkbox = QtGui.QCheckBox()
			checkbox.setText(trainerDesc)
			checkbox.setChecked( trainerActive == '[x]')
			checkbox.setObjectName( trainerIndex )
			self.__checkbox.append( checkbox )
			connect(self.__checkbox[i],
				'stateChanged(int)',
				lambda x , trainerIndex=trainerIndex:
					self.__toggle(trainerIndex)
				)
			self.__ui.vboxlayout.addWidget(checkbox)
			i = i + 1

		self.__ui.vboxlayout.addItem(self.__spacerItem)

	def __toggle(self, index ):
		print "toggled "+str(self.__selected) +" "+str(index)
		self.__bridge.command('trainer',
			str(self.__selected),
			str(index))()
		#Maybe we need to create an __update so that we
		#read ALL vlues again and set the checkboxes ?
		#This would catch also all cases of manual (de)selection in 
		#the openMSX console which we do ignore at the moment...
		#self.__bridge.command('trainer',str(self.__selected))(self.__update)
