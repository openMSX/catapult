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
		self.wdgtspacing = 0
		self.wdgtmargin = 9

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
			self.__ui.emptywidget = QtGui.QWidget()
			self.__ui.somewidget = QtGui.QScrollArea(self.__ui.containeremptywidget)
			sizePolicy1 = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
			self.__ui.emptywidget.setSizePolicy(sizePolicy1)
			sizePolicy2 = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
			self.__ui.somewidget.setSizePolicy(sizePolicy2)
			self.__ui.somewidget.setWidget(self.__ui.emptywidget)
			#self.__ui.somewidget.setWidgetResizable(1)
			self.__ui.vboxlayout = QtGui.QVBoxLayout(self.__ui.emptywidget)
			self.__ui.vboxlayout.setObjectName("vboxlayout")
			self.__ui.vboxlayout.setSpacing( self.wdgtspacing )
			self.__ui.vboxlayout.setMargin( self.wdgtmargin  )

			# Connect signals.
			connect(ui.cheatSelector, 'activated(QString)', self.fillCheats)


		dialog.show()
		dialog.raise_()
		dialog.activateWindow()
		self.getCheats()
		#the dialog.show() is resizing everything?
		#and then I fiddle with the new values...
		w = self.__ui.containeremptywidget.width()
		h = self.__ui.containeremptywidget.height()
		self.__ui.somewidget.resize(w,h)

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

	def fillCheats(self):
		self.__selected = self.__ui.cheatSelector.currentText()
		self.__bridge.command(
			'trainer',
			str(self.__selected)
			)(self.__output)

	def __output(self, *words):
		line = ' '.join(words)
		trainerArray = line.split('\n')
		
		trainerArray = sorted(trainerArray)
		#remove all items in the vboxlayout
		for widget in self.__checkbox[:]:
			self.__ui.vboxlayout.removeWidget(widget)
			#TODO: find out if this close() also
			#deletes/free the objects
			widget.close()
		self.__checkbox = []

		i = w = 0
		h = 2 * self.wdgtmargin 
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
			size = checkbox.sizeHint()
			h = h + self.wdgtspacing + size.height()
			if w < size.width():
				w = size.width()
			#checkbox.height()
			self.__checkbox.append( checkbox )
			connect(self.__checkbox[i],
				'stateChanged(int)',
				lambda x , trainerIndex=trainerIndex:
					self.__toggle(trainerIndex)
				)
			self.__ui.vboxlayout.addWidget(checkbox)
			i = i + 1
		w = w + 2 * self.wdgtmargin 
		self.__ui.emptywidget.resize(w,h)

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
