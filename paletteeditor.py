# $Id: cheatfinder.py 7020 2007-09-16 06:17:50Z vampier $

from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QColor, QPalette
from qt_utils import connect

#import os.path

class PaletteEditor(object):

	def __init__(self, bridge):
		self.__cfDialog = None
		self.__ui = None
		self.__bridge = bridge
		self.__colorWidgets = []

	def show(self):
		dialog = self.__cfDialog
		if dialog is None:
			self.__cfDialog = dialog = QtGui.QDialog(
				None, # TODO: find a way to get the real parent
				QtCore.Qt.Dialog
				| QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowSystemMenuHint
				)
			# Setup UI made in Qt Designer.
			from ui_paletteeditor import Ui_paletteEditor
			ui = Ui_paletteEditor()
			ui.setupUi(dialog)
			self.__ui = ui
			self.__colorWidgets = [ getattr(ui, 'Col%d' % index) for index in range(16) ]

			# Connect signals.
			connect(ui.GetMSXColors, 'clicked()', self.__getMSXColors)
			
			for index in range(16):
				connect(self.__colorWidgets[index], 'clicked()',
					lambda index = index: self.__clickedColor(index))

			connect(ui.RVal, 'valueChanged(int)', self.__changeR)
			connect(ui.GVal, 'valueChanged(int)', self.__changeG)
			connect(ui.BVal, 'valueChanged(int)', self.__changeB)

			#connect(ui.SavePalette, 'clicked()', self.savePalette)
			#connect(ui.LoadPalette, 'clicked()', self.loadPalette)

		dialog.show()
		dialog.raise_()
		dialog.activateWindow()
		self.__getMSXColors()

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

# Color Change handeling
# TODO: Kill redundant code
	def __setColor(self):
		index = self.__ui.ColorPickerLabel.value

		red = self.__ui.RVal.value()
		green = self.__ui.GVal.value()
		blue = self.__ui.BVal.value()

		rgbCol = 'setcolor ' + str(index) + ' ' + str(red) + str(green) + str(blue)

		self.__ui.ColorPickerLabel.setAutoFillBackground(True)
		color = QColor()
		color.setRgb( (red*255)/7, (green*255)/7, (blue*255)/7 )
		self.__ui.ColorPickerLabel.setPalette(QPalette(color))

		self.__colorWidgets[index].setPalette(QPalette(color))

		self.__bridge.sendCommandRaw(rgbCol)

# Button handeling
	def __clickedColor(self, index):
		self.__bridge.command('getcolor', index)(lambda rgb, index = index:
			self.__parseColors(index, rgb))

# Color Change handeling
	def __parseColors(self, index, col):

		red, green, blue = [int(ch) for ch in col]

		self.__ui.ColorPickerLabel.value = index

		#TODO: Find a way to refresh form upon Palette Editor Window Creation
		self.__ui.RVal.setEnabled(True)
		self.__ui.GVal.setEnabled(True)
		self.__ui.BVal.setEnabled(True)
		self.__ui.SavePalette.setEnabled(True)

		self.__ui.RVal.setValue(red)
		self.__ui.GVal.setValue(green)
		self.__ui.BVal.setValue(blue)

		self.__ui.lineEditRed.setText(str(red))
		self.__ui.lineEditGreen.setText(str(green))
		self.__ui.lineEditBlue.setText(str(blue))

		color = QColor()
		color.setRgb( (red*255)/7, (green*255)/7, (blue*255)/7 )
		self.__ui.ColorPickerLabel.setPalette(QPalette(color))

		self.__colorWidgets[index].setPalette(QPalette(color))
