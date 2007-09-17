import sys

from PyQt4 import QtCore, QtGui
from qt_utils import QtSignal, connect

class sizewizard2(QtGui.QDialog):
	def __init__(self, parent=None):
		QtGui.QDialog.__init__(self, parent)
		Dialog=self

	        self.resize(QtCore.QSize(QtCore.QRect(0,0,192,182).size()).expandedTo(self.minimumSizeHint()))

        	self.vboxlayout = QtGui.QVBoxLayout(self)
	        self.hboxlayout = QtGui.QHBoxLayout()

        	self.label = QtGui.QLabel(self)
        	self.hboxlayout.addWidget(self.label)

	        self.spinBox = QtGui.QSpinBox(self)
        	self.spinBox.setMinimum(1)
	        self.spinBox.setMaximum(32)
        	self.spinBox.setProperty("value",QtCore.QVariant(3))
		self.nr_partitions = 3
        	self.hboxlayout.addWidget(self.spinBox)
	        self.vboxlayout.addLayout(self.hboxlayout)

	        self.listWidget = QtGui.QListWidget(self)
	        self.vboxlayout.addWidget(self.listWidget)

        	self.buttonBox = QtGui.QDialogButtonBox(self)
	        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        	self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.NoButton|QtGui.QDialogButtonBox.Ok)
        	self.vboxlayout.addWidget(self.buttonBox)

	        connect(self.buttonBox,"accepted()",self.accept)
        	connect(self.buttonBox,"rejected()",self.reject)
        	connect(self.spinBox,"valueChanged(int)",self.setNrPartitions)

        	self.label.setText(QtGui.QApplication.translate("Dialog", "Number of partitions", None, QtGui.QApplication.UnicodeUTF8))
	        self.listWidget.clear()
	
		hide = 0
		index = 0
		while index < 32:
	        	item = QtGui.QListWidgetItem(self.listWidget)
	        	item.setFlags(
				QtCore.Qt.ItemIsSelectable | \
				QtCore.Qt.ItemIsEditable | \
				QtCore.Qt.ItemIsEnabled
				)
		        item.setText(
				QtGui.QApplication.translate(
					"Dialog", "32M", None, 
					QtGui.QApplication.UnicodeUTF8
					)
				)
			index += 1
		self.hideItems()

	def getPartitionsList(self):
		list = []
		index = 0
		while index < self.nr_partitions:
			item = self.listWidget.item(index)
			list.append( str(item.text()) )
			index += 1
		return ' '.join(list)

	def getNrPartitions(self):
		return 	str(self.nr_partitions)

	def setNrPartitions(self,i):
		self.nr_partitions= i
		self.hideItems()

	def hideItems(self):
		hide = 0
		index = 0
		while index < 32:
			item = self.listWidget.item(index)
			if index == self.nr_partitions:
				hide = 1
			item.setHidden(hide)
			index += 1

	
class sizewizard(QtGui.QDialog):
	def __init__(self, parent=None):
		QtGui.QDialog.__init__(self, parent)
		self.__dmDialog = None
		self.__ui = None
		self.__changePartitionsDialog = None
		self.__partitionsList = '32M 32M 32M'

		# Setup UI made in Qt Designer.
		from ui_sizewiz1 import Ui_Dialog
		ui = Ui_Dialog()
		ui.setupUi(self)
		self.__ui = ui
		connect(
			ui.unpartedButton,
			'toggled(bool)',
			self.setWidgetstate
			)
		connect(
			ui.partedButton,
			'toggled(bool)',
			self.setWidgetstate
			)
		connect(
			ui.changePartitionsButton,
			'clicked()',
			self.changePartionSizes
			)
	
	def setWidgetstate(self):
		print 'def setWidgetstate():'
		ui = self.__ui
		state = ui.partedButton.isChecked()
		print state
		ui.changePartitionsButton.setEnabled(state)
		ui.partedLabel.setEnabled(state)
		state = not state
		ui.unpartedSize.setEnabled(state)
		ui.unpartedLabel.setEnabled(state)

	def changePartionSizes(self):
		cpd = self.__changePartitionsDialog
		if cpd is None:
			self.__changePartitionsDialog = cpd = sizewizard2()
		cpd.exec_()
		nr = cpd.getNrPartitions()
		list = cpd.getPartitionsList()
		self.__partitionsList = list
		self.__ui.partedLabel.setText( nr + " partitions: " + list )

	def getSizes(self):
		ui = self.__ui
		if ui.partedButton.isChecked():
			sizes = self.__partitionsList
		else:
			sizes = str( self.__ui.unpartedSize.value() ) + 'K'
		print sizes
		return sizes

if __name__ == '__main__':
	app = QtGui.QApplication(sys.argv)
	item= sizewizard()
	#item.exec_()
	item.show()
	sys.exit(app.exec_())


