# $Id: cheatfinder.py 7020 2007-09-16 06:17:50Z vampier $

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qt_utils import connect

#import os.path

class paletteEditor(object):

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
			connect(ui.GetMSXColors, 'clicked()', self.getMSXColors)
			connect(ui.Col0, 'clicked()', self.clickedColor0)
			connect(ui.Col1, 'clicked()', self.clickedColor1)
			connect(ui.Col2, 'clicked()', self.clickedColor2)
			connect(ui.Col3, 'clicked()', self.clickedColor3)
			connect(ui.Col4, 'clicked()', self.clickedColor4)
			connect(ui.Col5, 'clicked()', self.clickedColor5)
			connect(ui.Col6, 'clicked()', self.clickedColor6)
			connect(ui.Col7, 'clicked()', self.clickedColor7)
			connect(ui.Col8, 'clicked()', self.clickedColor8)
			connect(ui.Col9, 'clicked()', self.clickedColor9)
			connect(ui.Col10, 'clicked()', self.clickedColor10)
			connect(ui.Col11, 'clicked()', self.clickedColor11)
			connect(ui.Col12, 'clicked()', self.clickedColor12)
			connect(ui.Col13, 'clicked()', self.clickedColor13)
			connect(ui.Col14, 'clicked()', self.clickedColor14)
			connect(ui.Col15, 'clicked()', self.clickedColor15)
			
			connect(ui.RVal, 'valueChanged(int)', self.ChangeR)
			connect(ui.GVal, 'valueChanged(int)', self.ChangeG)
			connect(ui.BVal, 'valueChanged(int)', self.ChangeB)
																								
			#connect(ui.SavePalette, 'clicked()', self.savePalette)
			#connect(ui.LoadPalette, 'clicked()', self.loadPalette)

		dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	def getMSXColors(self):
		for index in range(16):
			self.__bridge.command('getcolor', index)(lambda rgb, index = index: self.__ParseColors(index, rgb))

	def ChangeR(self):
		self.__ui.lineEditRed.setText(str(self.__ui.RVal.value()))
		index=self.__ui.ColorPickerLabel.value
		rgbCol='setcolor '+str(index)+' '+str(self.__ui.RVal.value())+str(self.__ui.GVal.value())+str(self.__ui.BVal.value())
		self.__bridge.sendCommandRaw(rgbCol)
		#self.__bridge.command(rgbCol)()

	def ChangeG(self):
		self.__ui.lineEditGreen.setText(str(self.__ui.GVal.value()))
		index=self.__ui.ColorPickerLabel.value
		rgbCol='setcolor '+str(index)+' '+str(self.__ui.RVal.value())+str(self.__ui.GVal.value())+str(self.__ui.BVal.value())
		self.__bridge.sendCommandRaw(rgbCol)

	def ChangeB(self):
		self.__ui.lineEditBlue.setText(str(self.__ui.BVal.value()))
		index=self.__ui.ColorPickerLabel.value
		rgbCol='setcolor '+str(index)+' '+str(self.__ui.RVal.value())+str(self.__ui.GVal.value())+str(self.__ui.BVal.value())
		self.__bridge.sendCommandRaw(rgbCol)

	def setColor(self):
		print 'HelloWorld'
		return 'done'


	def clickedColor0(self):
		index=0
		self.__bridge.command('getcolor', index)(lambda rgb, index = index: self.__ParseColors(index, rgb))

	def clickedColor1(self):
		index=1
		self.__bridge.command('getcolor', index)(lambda rgb, index = index: self.__ParseColors(index, rgb))

	def clickedColor2(self):
		index=2
		self.__bridge.command('getcolor', index)(lambda rgb, index = index: self.__ParseColors(index, rgb))

	def clickedColor3(self):
		index=3
		self.__bridge.command('getcolor', index)(lambda rgb, index = index: self.__ParseColors(index, rgb))

	def clickedColor4(self):
		index=4
		self.__bridge.command('getcolor', index)(lambda rgb, index = index: self.__ParseColors(index, rgb))

	def clickedColor5(self):
		index=5
		self.__bridge.command('getcolor', index)(lambda rgb, index = index: self.__ParseColors(index, rgb))

	def clickedColor6(self):
		index=6
		self.__bridge.command('getcolor', index)(lambda rgb, index = index: self.__ParseColors(index, rgb))

	def clickedColor7(self):
		index=7
		self.__bridge.command('getcolor', index)(lambda rgb, index = index: self.__ParseColors(index, rgb))

	def clickedColor8(self):
		index=8
		self.__bridge.command('getcolor', index)(lambda rgb, index = index: self.__ParseColors(index, rgb))

	def clickedColor9(self):
		index=9
		self.__bridge.command('getcolor', index)(lambda rgb, index = index: self.__ParseColors(index, rgb))

	def clickedColor10(self):
		index=10
		self.__bridge.command('getcolor', index)(lambda rgb, index = index: self.__ParseColors(index, rgb))

	def clickedColor11(self):
		index=11
		self.__bridge.command('getcolor', index)(lambda rgb, index = index: self.__ParseColors(index, rgb))

	def clickedColor12(self):
		index=12
		self.__bridge.command('getcolor', index)(lambda rgb, index = index: self.__ParseColors(index, rgb))

	def clickedColor13(self):
		index=13
		self.__bridge.command('getcolor', index)(lambda rgb, index = index: self.__ParseColors(index, rgb))

	def clickedColor14(self):
		index=14
		self.__bridge.command('getcolor', index)(lambda rgb, index = index: self.__ParseColors(index, rgb))

	def clickedColor15(self):
		index=15
		self.__bridge.command('getcolor', index)(lambda rgb, index = index: self.__ParseColors(index, rgb))

	def __ParseColors(self, index, col):

		r, g, b = [int(ch) for ch in col]

		#self.__ui.RVal.setValue(r)
		#self.__ui.GVal.setValue(g)
		#self.__ui.BVal.setValue(b)

		self.__ui.lineEditRed.setText(str(r))
		self.__ui.lineEditGreen.setText(str(g))
		self.__ui.lineEditBlue.setText(str(b))

		self.__ui.ColorPickerLabel.value=index

		self.__ui.ColorPickerLabel.setAutoFillBackground(True)
		color = QColor()
		color.setRgb( (r*255)/7, (g*255)/7, (b*255)/7 )
		self.__ui.ColorPickerLabel.setPalette( QPalette( color ) )

		if index==0:
			self.__ui.Col0.setAutoFillBackground(True)
			self.__ui.Col0.setPalette( QPalette( color ) )
		if index==1:
			self.__ui.Col1.setAutoFillBackground(True)
			self.__ui.Col1.setPalette( QPalette( color ) )
		if index==2:
			self.__ui.Col2.setAutoFillBackground(True)
			self.__ui.Col2.setPalette( QPalette( color ) )
		if index==3:
			self.__ui.Col3.setAutoFillBackground(True)
			self.__ui.Col3.setPalette( QPalette( color ) )
		if index==4:
			self.__ui.Col4.setAutoFillBackground(True)
			self.__ui.Col4.setPalette( QPalette( color ) )
		if index==5:
			self.__ui.Col5.setAutoFillBackground(True)
			self.__ui.Col5.setPalette( QPalette( color ) )
		if index==6:
			self.__ui.Col6.setAutoFillBackground(True)
			self.__ui.Col6.setPalette( QPalette( color ) )
		if index==7:
			self.__ui.Col7.setAutoFillBackground(True)
			self.__ui.Col7.setPalette( QPalette( color ) )
		if index==8:
			self.__ui.Col8.setAutoFillBackground(True)
			self.__ui.Col8.setPalette( QPalette( color ) )
		if index==9:
			self.__ui.Col9.setAutoFillBackground(True)
			self.__ui.Col9.setPalette( QPalette( color ) )
		if index==10:
			self.__ui.Col10.setAutoFillBackground(True)
			self.__ui.Col10.setPalette( QPalette( color ) )
		if index==11:
			self.__ui.Col11.setAutoFillBackground(True)
			self.__ui.Col11.setPalette( QPalette( color ) )
		if index==12:
			self.__ui.Col12.setAutoFillBackground(True)
			self.__ui.Col12.setPalette( QPalette( color ) )
		if index==13:
			self.__ui.Col13.setAutoFillBackground(True)
			self.__ui.Col13.setPalette( QPalette( color ) )
		if index==14:
			self.__ui.Col14.setAutoFillBackground(True)
			self.__ui.Col14.setPalette( QPalette( color ) )
		if index==15:
			self.__ui.Col15.setAutoFillBackground(True)
			self.__ui.Col15.setPalette( QPalette( color ) )

