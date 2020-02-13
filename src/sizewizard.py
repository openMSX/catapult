import sys

from PyQt5 import QtCore, QtWidgets
from qt_utils import connect

class Sizewizardtwo(QtWidgets.QDialog):
	def __init__(self, parent=None):
		QtWidgets.QDialog.__init__(self, parent)

		self.resize(
			QtCore.QSize(
				QtCore.QRect(0, 0, 192, 182).size()
			).expandedTo(self.minimumSizeHint()))

		self.vboxlayout = QtWidgets.QVBoxLayout(self)
		self.hboxlayout = QtWidgets.QHBoxLayout()

		self.label = QtWidgets.QLabel(self)
		self.hboxlayout.addWidget(self.label)

		self.spinBox = QtWidgets.QSpinBox(self)
		self.spinBox.setMinimum(1)
		self.spinBox.setMaximum(32)
		self.spinBox.setProperty("value", QtCore.QVariant(3))
		self.nr_partitions = 3
		self.hboxlayout.addWidget(self.spinBox)
		self.vboxlayout.addLayout(self.hboxlayout)

		self.listWidget = QtWidgets.QListWidget(self)
		self.vboxlayout.addWidget(self.listWidget)

		self.buttonBox = QtWidgets.QDialogButtonBox(self)
		self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
		self.buttonBox.setStandardButtons(
			QtWidgets.QDialogButtonBox.Cancel | \
			QtWidgets.QDialogButtonBox.NoButton | \
			QtWidgets.QDialogButtonBox.Ok
			)
		self.vboxlayout.addWidget(self.buttonBox)

		self.buttonBox.accepted.connect(self.accept)
		self.buttonBox.rejected.connect(self.reject)
		self.spinBox.valueChanged.connect(self.setNrPartitions)

		self.label.setText(QtWidgets.QApplication.translate(
			"Dialog", "Number of partitions", None,
			QtWidgets.QApplication.UnicodeUTF8)
			)
		self.listWidget.clear()

		index = 0
		while index < 32:
			widgetItem = QtWidgets.QListWidgetItem(self.listWidget)
			widgetItem.setFlags(
				QtCore.Qt.ItemIsSelectable | \
				QtCore.Qt.ItemIsEditable | \
				QtCore.Qt.ItemIsEnabled
				)
			widgetItem.setText(
				QtWidgets.QApplication.translate(
					"Dialog", "32M", None,
					QtWidgets.QApplication.UnicodeUTF8
					)
				)
			index += 1
		self.hideItems()

	def getPartitionsList(self):
		partList = []
		index = 0
		while index < self.nr_partitions:
			widgetItem = self.listWidget.item(index)
			partList.append( str(widgetItem.text()) )
			index += 1
		return ' '.join(partList)

	def getNrPartitions(self):
		return 	str(self.nr_partitions)

	def setNrPartitions(self, i):
		self.nr_partitions = i
		self.hideItems()

	def hideItems(self):
		hide = 0
		index = 0
		while index < 32:
			widgetItem = self.listWidget.item(index)
			if index == self.nr_partitions:
				hide = 1
			widgetItem.setHidden(hide)
			index += 1

class Sizewizard(QtWidgets.QDialog):
	def __init__(self, parent=None):
		QtWidgets.QDialog.__init__(self, parent)
		self.__dmDialog = None
		self.__ui = None
		self.__changePartitionsDialog = None
		self.__partitionsList = '32M 32M 32M'

		# Setup UI made in Qt Designer.
		from ui_sizewiz1 import Ui_Dialog
		ui = Ui_Dialog()
		ui.setupUi(self)
		self.__ui = ui
		ui.unpartedButton.toggled.connect(
			self.setWidgetstate
			)
		ui.partedButton.toggled.connect(
			self.setWidgetstate
			)
		ui.changePartitionsButton.clicked.connect(
			self.changePartionSizes
			)
		ui.unpartedSize.valueChanged.connect(
			self.changedDiskSize
			)

	def setWidgetstate(self):
		print('def setWidgetstate():')
		ui = self.__ui
		state = ui.partedButton.isChecked()
		print(state)
		ui.changePartitionsButton.setEnabled(state)
		ui.partedLabel.setEnabled(state)
		state = not state
		ui.unpartedSize.setEnabled(state)
		ui.unpartedLabel.setEnabled(state)

	def changedDiskSize(self, size):
		bold = 1
		if  size > 32767:
			txt = 'Maximum sized FAT12 disk fo IDE extension'
		elif size == 720:
			txt = 'Regular 720KB DD-DS disk '+ \
			'(double density, double sided)'
		elif size == 360:
			txt = 'Regular 360KB DD-SS disk '+ \
			'(double density, single sided)'
		elif size > 720:
			txt = 'big disk for IDE extension' + \
			'with size ' + str(size/1024) + "MB"
			bold = 0
		else:
			txt = "disk with custom size of " + \
			str(size) + "KB"
			bold = 0
		self.__ui.unpartedLabel.setText(txt)
		self.__ui.unpartedLabel.font().setBold(bold)

	def changePartionSizes(self):
		cpd = self.__changePartitionsDialog
		if cpd is None:
			self.__changePartitionsDialog = cpd = Sizewizardtwo()
		cpd.exec_()
		nr = cpd.getNrPartitions()
		partList = cpd.getPartitionsList()
		self.__partitionsList = partList
		self.__ui.partedLabel.setText( nr + " partitions: " + partList )

	def getSizes(self):
		ui = self.__ui
		if ui.partedButton.isChecked():
			sizes = self.__partitionsList
		else:
			sizes = str( self.__ui.unpartedSize.value() ) + 'K'
		print(sizes)
		return sizes

if __name__ == '__main__':
	app = QtWidgets.QApplication(sys.argv)
	item = Sizewizard()
	#item.exec_()
	item.show()
	sys.exit(app.exec_())


