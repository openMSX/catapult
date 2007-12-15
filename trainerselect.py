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
		self.__trainerVLayout = None
		self.__scrollArea = None

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
			# layout where we will put the cheats in:
			self.__trainerVLayout = QtGui.QVBoxLayout(ui.emptyContainerWidget)
			self.__trainerVLayout.setObjectName('trainerVLayout')
			self.__trainerVLayout.setSpacing(0)
			self.__trainerVLayout.setMargin(0)
			# scrollarea to make sure everything will fit in the window
			self.__scrollArea = QtGui.QScrollArea(dialog)
			self.__scrollArea.setWidget(ui.emptyContainerWidget)
			self.__scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
			self.__scrollArea.setWidgetResizable(True)
			self.__scrollArea.setFrameStyle(QtGui.QFrame.NoFrame)
			ui.gridlayout.addWidget(self.__scrollArea)
			
			# Connect signals.
			connect(ui.gameSelector, 'activated(QString)', self.__fillCheats)
			connect(ui.enableNoneButton, 'clicked()', self.__enableNone)
			connect(ui.enableAllButton, 'clicked()', self.__enableAll)


		dialog.show()
		dialog.raise_()
		dialog.activateWindow()
		# get cheats
		self.__bridge.command(
			'array', 'names', '::__trainers'
			)(self.__fillGameSelector)
		
	def __fillGameSelector(self, *words):
		words = sorted(words)
		text = self.__ui.gameSelector
		for game in words[ : -1]:
			text.addItem(game)

	def __fillCheats(self):
		self.__selected = self.__ui.gameSelector.currentText()
		self.__bridge.command(
			'trainer',
			str(self.__selected)
			)(self.__output)

	def __output(self, *words):
		line = ' '.join(words)
		trainerArray = line.split('\n')
		
		#remove all items in the trainerVLayout
		child = self.__trainerVLayout.takeAt(0)
		while (child != None):
			if not isinstance(child, QtGui.QSpacerItem):
				child.widget().setParent(None)
				child.widget().deleteLater()
			del child
			child = self.__trainerVLayout.takeAt(0)
	
		self.__checkbox = []
		for trainerLine in trainerArray[ 1 : ]:
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
			connect(checkbox,
				'stateChanged(int)',
				lambda x, trainerIndex = trainerIndex:
					self.__toggle(trainerIndex)
				)
			self.__trainerVLayout.addWidget(checkbox)
		self.__trainerVLayout.addStretch(10)

	def __toggle(self, index):
		print "toggled "+str(self.__selected) +" "+str(index)
		self.__bridge.command('trainer',
			str(self.__selected),
			str(index))()
		#Maybe we need to create an __update so that we
		#read ALL values again and set the checkboxes ?
		#This would catch also all cases of manual (de)selection in 
		#the openMSX console which we do ignore at the moment...
		#self.__bridge.command('trainer', str(self.__selected))(self.__update)

	def __enableNone(self):
		for checkBox in self.__checkbox:
			if checkBox.isChecked():
				checkBox.setChecked(False)

	def __enableAll(self):
		for checkBox in self.__checkbox:
			if not checkBox.isChecked():
				checkBox.setChecked(True)

	
