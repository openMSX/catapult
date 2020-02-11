# $Id$

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QColor, QPalette

class PaletteEditor(object):

	def __init__(self, bridge):
		self.__cfDialog = None
		self.__ui = None
		self.__bridge = bridge
		self.__colorWidgets = []

	def show(self):
		dialog = self.__cfDialog
		if dialog is None:
			self.__cfDialog = dialog = QtWidgets.QDialog(
				None, # TODO: find a way to get the real parent
				QtCore.Qt.Dialog
				| QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowSystemMenuHint
				)
			# Setup UI made in Qt Designer.
			from ui_paletteeditor import Ui_paletteEditor
			ui = Ui_paletteEditor()
			ui.setupUi(dialog)
			self.__ui = ui
			self.__colorWidgets = [
				getattr(ui, 'Col%d' % index) for index in range(16)
				]

			# Connect signals.
			ui.GetMSXColors.clicked.connect(self.__getMSXColors)

			for index in range(16):
				self.__colorWidgets[index].clicked.connect(
					lambda dummy, index = index: self.__clickedColor(index))

			ui.RVal.valueChanged.connect(self.__changeR)
			ui.GVal.valueChanged.connect(self.__changeG)
			ui.BVal.valueChanged.connect(self.__changeB)

			ui.SavePalette.clicked.connect(self.__savePalette)
			ui.LoadPalette.clicked.connect(self.__loadPalette)

		dialog.show()
		dialog.raise_()
		dialog.activateWindow()
		self.__getMSXColors()

	# Palette Save/Load dialog and functions:

	def __savePalette(self):
		browseTitle = 'Save Palette File'
		imageSpec = 'Palette Files (*.pal);;All Files (*)'
		path = QtWidgets.QFileDialog.getSaveFileName(
			None,
			browseTitle,
			QtCore.QDir.currentPath(),
			imageSpec
			)
		if not path:
			return
		self.__savePalFile(path)

	def __loadPalette(self):
		browseTitle = 'Load Palette File'
		imageSpec = 'Palette Files (*.pal);;All Files (*)'
		path = QtWidgets.QFileDialog.getOpenFileName(
			None,
			browseTitle,
			QtCore.QDir.currentPath(),
			imageSpec
			)
		if not path:
			return
		self.__loadPalFile(path)

	def __savePalFile(self, palFileName):
		palfile = open(palFileName, 'w')
		for index in range(16):
			red = self.__colorWidgets[index].red
			green = self.__colorWidgets[index].green
			blue = self.__colorWidgets[index].blue
			palfile.write (('%d%d%d' % (red, green, blue))+'\n')
		palfile.write('Catapult Palette File')
		palfile.close()

	def __loadPalFile(self, palFileName):
		palfile = open(palFileName, 'r')
		for index in range(16):
			rgb = palfile.readline().strip()
			self.__bridge.command('setcolor', index, rgb)()
			self.__parseColors(index, rgb)
		palfile.close()

	# Color handling:

	def __getMSXColors(self):
		for index in range(16):
			self.__bridge.command('getcolor', index)(
				lambda rgb, index = index:
				self.__parseColors(index, rgb)
				)

	def __changeR(self):
		self.__ui.lineEditRed.setText(str(self.__ui.RVal.value()))
		self.__setColor()

	def __changeG(self):
		self.__ui.lineEditGreen.setText(str(self.__ui.GVal.value()))
		self.__setColor()

	def __changeB(self):
		self.__ui.lineEditBlue.setText(str(self.__ui.BVal.value()))
		self.__setColor()

	# Color change handling:

	def __setColor(self):
		index = self.__ui.ColorPickerLabel.value
		red = self.__ui.RVal.value()
		green = self.__ui.GVal.value()
		blue = self.__ui.BVal.value()
		self.__parseColors(index, '%d%d%d' % (red, green, blue))
		self.__bridge.command(
			'setcolor', index, '%d%d%d' % (red, green, blue)
			)()

	# Button handling:

	def __clickedColor(self, index):
		self.__ui.ColorPickerLabel.setText(str(index))
		self.__bridge.command('getcolor', index)(lambda rgb, index = index:
			self.__parseColors(index, rgb))

	# Color change handling:

	def __parseColors(self, index, col):

		self.__ui.ColorPickerLabel.setText(str(index))

		red, green, blue = ( int(ch) for ch in col )

		self.__ui.ColorPickerLabel.value = index

		# Set buttons enables after 1st search.
		self.__ui.RVal.setEnabled(True)
		self.__ui.GVal.setEnabled(True)
		self.__ui.BVal.setEnabled(True)
		self.__ui.SavePalette.setEnabled(True)

		# Set sliders.
		self.__ui.RVal.setValue(red)
		self.__ui.GVal.setValue(green)
		self.__ui.BVal.setValue(blue)
		
		# Set text boxes.
		self.__ui.lineEditRed.setText(str(red))
		self.__ui.lineEditGreen.setText(str(green))
		self.__ui.lineEditBlue.setText(str(blue))

		# Set label color.
		color = QColor()
		color.setRgb((red * 255) / 7, (green * 255) / 7, (blue * 255) / 7)
		self.__ui.ColorPickerLabel.setPalette(QPalette(color))

		# Set button color.
		self.__colorWidgets[index].setPalette(QPalette(color))
		self.__colorWidgets[index].red = red
		self.__colorWidgets[index].green = green
		self.__colorWidgets[index].blue = blue
