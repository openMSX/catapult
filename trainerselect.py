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
		# tmp to debug checkbox
		#self.__debugvalue = 0

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
			sizePolicyA = QtGui.QSizePolicy(
				QtGui.QSizePolicy.Expanding,
				QtGui.QSizePolicy.Expanding
				)
			self.__ui.emptywidget.setSizePolicy(sizePolicyA)
			sizePolicyB = QtGui.QSizePolicy(
				QtGui.QSizePolicy.Expanding,
				QtGui.QSizePolicy.Expanding
				)
			self.__ui.somewidget.setSizePolicy(sizePolicyB)
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
		newWidth = self.__ui.containeremptywidget.width()
		newHeight = self.__ui.containeremptywidget.height()
		self.__ui.somewidget.resize(newWidth, newHeight)

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
		
		#remove all items in the vboxlayout
		#print "checkboxes to remove... " + str(len(self.__checkbox))
		#let the 
		self.__ui.vboxlayout = None
		self.__ui.emptywidget = None
		#-------------------- ------------------------------------
		# Old code temporaly kept for later reference
		#
		#		for widget in self.__checkbox[:]:
		#			self.__ui.vboxlayout.removeWidget(widget)
		#			#self.__ui.emptywidget.removeChild(widget)
		#			##p = widget.parent()
		#			##p.removeChild(widget)
		#			widget.close()
		#			#a close() doesn't deletes/free the python objects
		#			del widget
		#---------------------------------------------------------
		#
		# this new code simply throws away the emptywidget, boxlayout etc etc
		# and lets python/pyqt garbage collector take care of it all
		#
		self.__ui.emptywidget = QtGui.QWidget()
		sizePolicyA = QtGui.QSizePolicy(
			QtGui.QSizePolicy.Expanding,
			QtGui.QSizePolicy.Expanding
			)
		self.__ui.emptywidget.setSizePolicy(sizePolicyA)
		self.__ui.somewidget.setWidget(self.__ui.emptywidget)
		self.__ui.vboxlayout = QtGui.QVBoxLayout(self.__ui.emptywidget)
		self.__ui.vboxlayout.setObjectName("vboxlayout")
		self.__ui.vboxlayout.setSpacing( self.wdgtspacing )
		self.__ui.vboxlayout.setMargin( self.wdgtmargin  )
		newWidth = self.__ui.containeremptywidget.width()
		newHeight = self.__ui.containeremptywidget.height()
		self.__ui.somewidget.resize(newWidth, newHeight)

		self.__checkbox = []

		#-----------------------------------------------------------------------
		# if the old code was used then this debug prints showed that emptywidget
		# still kept all the previously instantiated checkboxes as children
		# so the number kept going up with every trainer selected!!
		#
		#lijstje = self.__ui.emptywidget.findChildren(QtGui.QCheckBox)
		#print "found children: " +  str(len(lijstje))


		i = newwidth = 0
		newheight = 2 * self.wdgtmargin 
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
			size = checkbox.sizeHint()
			newheight = newheight + self.wdgtspacing + size.height()
			if newwidth < size.width():
				newwidth = size.width()
			self.__checkbox.append( checkbox )
			connect(self.__checkbox[i],
				'stateChanged(int)',
				lambda x , trainerIndex=trainerIndex:
					self.__toggle(trainerIndex)
				)
			self.__ui.vboxlayout.addWidget(checkbox)
			i = i + 1
		newwidth = newwidth + 2 * self.wdgtmargin 

		self.__ui.emptywidget.resize(newwidth, newheight)
		#print "checkboxes added... " + str(len(self.__checkbox))
		#if len(self.__checkbox) - self.__debugvalue != 0 :
		#	print "--------------------------------------------" 
		#self.__debugvalue = len(self.__checkbox)

	def __toggle(self, index ):
		print "toggled "+str(self.__selected) +" "+str(index)
		self.__bridge.command('trainer',
			str(self.__selected),
			str(index))()
		#Maybe we need to create an __update so that we
		#read ALL values again and set the checkboxes ?
		#This would catch also all cases of manual (de)selection in 
		#the openMSX console which we do ignore at the moment...
		#self.__bridge.command('trainer', str(self.__selected))(self.__update)
