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

			# Connect signals.
			connect(ui.GetMSXColors, 'clicked()', self.__getMSXColors)
			connect(ui.Col0, 'clicked()', self.__clickedColor0)
			connect(ui.Col1, 'clicked()', self.__clickedColor1)
			connect(ui.Col2, 'clicked()', self.__clickedColor2)
			connect(ui.Col3, 'clicked()', self.__clickedColor3)
			connect(ui.Col4, 'clicked()', self.__clickedColor4)
			connect(ui.Col5, 'clicked()', self.__clickedColor5)
			connect(ui.Col6, 'clicked()', self.__clickedColor6)
			connect(ui.Col7, 'clicked()', self.__clickedColor7)
			connect(ui.Col8, 'clicked()', self.__clickedColor8)
			connect(ui.Col9, 'clicked()', self.__clickedColor9)
			connect(ui.Col10, 'clicked()', self.__clickedColor10)
			connect(ui.Col11, 'clicked()', self.__clickedColor11)
			connect(ui.Col12, 'clicked()', self.__clickedColor12)
			connect(ui.Col13, 'clicked()', self.__clickedColor13)
			connect(ui.Col14, 'clicked()', self.__clickedColor14)
			connect(ui.Col15, 'clicked()', self.__clickedColor15)
			
			connect(ui.RVal, 'valueChanged(int)', self.__changeR)
			connect(ui.GVal, 'valueChanged(int)', self.__changeG)
			connect(ui.BVal, 'valueChanged(int)', self.__changeB)
																								
			#connect(ui.SavePalette, 'clicked()', self.savePalette)
			#connect(ui.LoadPalette, 'clicked()', self.loadPalette)

		dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	def __getMSXColors(self):
		for index in range(16):
			self.__bridge.command('getcolor', index)(
				lambda rgb, index = index: 
				self.__parseColors(index, rgb)
				)

	def __changeR(self):
		self.__ui.lineEditRed.setText(str(self.__ui.RVal.value()))
		index = self.__ui.ColorPickerLabel.value
		rgbCol = 'setcolor ' + str(index) + ' ' + str(self.__ui.RVal.value()
			) + str(self.__ui.GVal.value()) + str(self.__ui.BVal.value())
		self.__bridge.sendCommandRaw(rgbCol)
		#self.__bridge.command(rgbCol)()

	def __changeG(self):
		self.__ui.lineEditGreen.setText(str(self.__ui.GVal.value()))
		index = self.__ui.ColorPickerLabel.value
		rgbCol = 'setcolor ' + str(index) + ' ' + str(self.__ui.RVal.value()
			) + str(self.__ui.GVal.value()) + str(self.__ui.BVal.value())
		self.__bridge.sendCommandRaw(rgbCol)

	def __changeB(self):
		self.__ui.lineEditBlue.setText(str(self.__ui.BVal.value()))
		index = self.__ui.ColorPickerLabel.value
		rgbCol = 'setcolor ' + str(index) + ' ' + str(self.__ui.RVal.value()
			) + str(self.__ui.GVal.value()) + str(self.__ui.BVal.value())
		self.__bridge.sendCommandRaw(rgbCol)

	def setColor(self):
		print 'HelloWorld'
		return 'done'


	def __clickedColor0(self):
		index = 0
		self.__bridge.command('getcolor', index)(lambda rgb, index = index: 
			self.__parseColors(index, rgb))

	def __clickedColor1(self):
		index = 1
		self.__bridge.command('getcolor', index)(lambda rgb, index = index:
			self.__parseColors(index, rgb))

	def __clickedColor2(self):
		index = 2
		self.__bridge.command('getcolor', index)(lambda rgb, index = index:
			self.__parseColors(index, rgb))

	def __clickedColor3(self):
		index = 3
		self.__bridge.command('getcolor', index)(lambda rgb, index = index:
			self.__parseColors(index, rgb))

	def __clickedColor4(self):
		index = 4
		self.__bridge.command('getcolor', index)(lambda rgb, index = index:
			self.__parseColors(index, rgb))

	def __clickedColor5(self):
		index = 5
		self.__bridge.command('getcolor', index)(lambda rgb, index = index:
			self.__parseColors(index, rgb))

	def __clickedColor6(self):
		index = 6
		self.__bridge.command('getcolor', index)(lambda rgb, index = index:
			self.__parseColors(index, rgb))

	def __clickedColor7(self):
		index = 7
		self.__bridge.command('getcolor', index)(lambda rgb, index = index:
			self.__parseColors(index, rgb))

	def __clickedColor8(self):
		index = 8
		self.__bridge.command('getcolor', index)(lambda rgb, index = index:
			self.__parseColors(index, rgb))

	def __clickedColor9(self):
		index = 9
		self.__bridge.command('getcolor', index)(lambda rgb, index = index: 
			self.__parseColors(index, rgb))

	def __clickedColor10(self):
		index = 10
		self.__bridge.command('getcolor', index)(lambda rgb, index = index:
			self.__parseColors(index, rgb))

	def __clickedColor11(self):
		index = 11
		self.__bridge.command('getcolor', index)(lambda rgb, index = index:
			self.__parseColors(index, rgb))

	def __clickedColor12(self):
		index = 12
		self.__bridge.command('getcolor', index)(lambda rgb, index = index:
			self.__parseColors(index, rgb))

	def __clickedColor13(self):
		index = 13
		self.__bridge.command('getcolor', index)(lambda rgb, index = index:
			self.__parseColors(index, rgb))

	def __clickedColor14(self):
		index = 14
		self.__bridge.command('getcolor', index)(lambda rgb, index = index:
			self.__parseColors(index, rgb))

	def __clickedColor15(self):
		index = 15
		self.__bridge.command('getcolor', index)(lambda rgb, index = index:
			self.__parseColors(index, rgb))

	def __parseColors(self, index, col):

		red, green, blue = [int(ch) for ch in col]

		#self.__ui.RVal.setValue(red)
		#self.__ui.GVal.setValue(green)
		#self.__ui.BVal.setValue(blue)

		self.__ui.lineEditRed.setText(str(red))
		self.__ui.lineEditGreen.setText(str(green))
		self.__ui.lineEditBlue.setText(str(blue))

		self.__ui.ColorPickerLabel.value = index

		self.__ui.ColorPickerLabel.setAutoFillBackground(True)
		color = QColor()
		color.setRgb( (red*255)/7, (green*255)/7, (blue*255)/7 )
		self.__ui.ColorPickerLabel.setPalette( QPalette( color ) )

		if index == 0:
			self.__ui.Col0.setAutoFillBackground(True)
			self.__ui.Col0.setPalette( QPalette( color ) )
		if index == 1:
			self.__ui.Col1.setAutoFillBackground(True)
			self.__ui.Col1.setPalette( QPalette( color ) )
		if index == 2:
			self.__ui.Col2.setAutoFillBackground(True)
			self.__ui.Col2.setPalette( QPalette( color ) )
		if index == 3:
			self.__ui.Col3.setAutoFillBackground(True)
			self.__ui.Col3.setPalette( QPalette( color ) )
		if index == 4:
			self.__ui.Col4.setAutoFillBackground(True)
			self.__ui.Col4.setPalette( QPalette( color ) )
		if index == 5:
			self.__ui.Col5.setAutoFillBackground(True)
			self.__ui.Col5.setPalette( QPalette( color ) )
		if index == 6:
			self.__ui.Col6.setAutoFillBackground(True)
			self.__ui.Col6.setPalette( QPalette( color ) )
		if index == 7:
			self.__ui.Col7.setAutoFillBackground(True)
			self.__ui.Col7.setPalette( QPalette( color ) )
		if index == 8:
			self.__ui.Col8.setAutoFillBackground(True)
			self.__ui.Col8.setPalette( QPalette( color ) )
		if index == 9:
			self.__ui.Col9.setAutoFillBackground(True)
			self.__ui.Col9.setPalette( QPalette( color ) )
		if index == 10:
			self.__ui.Col10.setAutoFillBackground(True)
			self.__ui.Col10.setPalette( QPalette( color ) )
		if index == 11:
			self.__ui.Col11.setAutoFillBackground(True)
			self.__ui.Col11.setPalette( QPalette( color ) )
		if index == 12:
			self.__ui.Col12.setAutoFillBackground(True)
			self.__ui.Col12.setPalette( QPalette( color ) )
		if index == 13:
			self.__ui.Col13.setAutoFillBackground(True)
			self.__ui.Col13.setPalette( QPalette( color ) )
		if index == 14:
			self.__ui.Col14.setAutoFillBackground(True)
			self.__ui.Col14.setPalette( QPalette( color ) )
		if index == 15:
			self.__ui.Col15.setAutoFillBackground(True)
			self.__ui.Col15.setPalette( QPalette( color ) )

