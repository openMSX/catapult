# $Id: cheatfinder.py 7020 2007-09-16 06:17:50Z vampier $

from PyQt4 import QtCore, QtGui
from qt_utils import connect
from player import PlayState

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
				print "-------------------------------------------- Hello World"
				from ui_paletteeditor import Ui_paletteEditor
				ui = Ui_paletteEditor()
				ui.setupUi(dialog)
				self.__ui = ui

			dialog.show()
			dialog.raise_()
			dialog.activateWindow()
