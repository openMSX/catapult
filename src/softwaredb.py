# $Id$

from PyQt4 import QtCore, QtGui
from qt_utils import connect

class SoftwareDB:

	def __init__(self, bridge):
		self.__dmDialog = None
		self.__ui = None
		self.__cursor = None
		self.__bridge = bridge
		self.__selectedgameid = []

	def show(self):
		dialog = self.__dmDialog
		if dialog is None:
			self.__dmDialog = dialog = QtGui.QDialog(
				None, # TODO: find a way to get the real parent
				QtCore.Qt.Dialog
				| QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowSystemMenuHint
				)
			# Setup UI made in Qt Designer.
			from ui_softwaredb import Ui_SoftwareDB
			ui = Ui_SoftwareDB()
			ui.setupUi(dialog)
			self.__ui = ui

			# Connect signals.
			#connect(ui.dirUpButton, 'clicked()', self.updir)

			#fill the components with values
			from pysqlite2 import dbapi2 as sqlite
			cursor = self.__cursor
			if cursor is None:
				connection = sqlite.connect('softdb.db')
				self.__cursor = cursor = connection.cursor()

			#First the Compagny
			ui.compagnyComboBox.addItem(QtCore.QString('Select...'))
			cursor.execute('SELECT DISTINCT Compagny FROM software ORDER BY Compagny')
			for row in cursor:
				ui.compagnyComboBox.addItem(QtCore.QString(row[0]))

			#The Genre
			ui.genreComboBox.addItem(QtCore.QString('Select...'))
			cursor.execute('SELECT DISTINCT Genre FROM software ORDER BY Genre')
			for row in cursor:
				ui.genreComboBox.addItem(QtCore.QString(row[0]))

			#The Machine
			ui.machineComboBox.addItem(QtCore.QString('Select...'))
			cursor.execute('SELECT DISTINCT Machine FROM software ORDER BY Machine')
			for row in cursor:
				ui.machineComboBox.addItem(QtCore.QString(row[0]))

			#The Patched
			ui.patchedComboBox.addItem(QtCore.QString('Select...'))
			cursor.execute('SELECT DISTINCT Patched FROM software ORDER BY Patched')
			for row in cursor:
				ui.patchedComboBox.addItem(QtCore.QString(row[0]))

			#The Type
			ui.typeComboBox.addItem(QtCore.QString('Select...'))
			cursor.execute('SELECT DISTINCT Type FROM software ORDER BY Type')
			for row in cursor:
				ui.typeComboBox.addItem(QtCore.QString(row[0]))

			#The Year
			ui.yearComboBox.addItem(QtCore.QString('Select...'))
			cursor.execute('SELECT DISTINCT Year FROM software ORDER BY Year')
			for row in cursor:
				ui.yearComboBox.addItem(QtCore.QString(row[0]))

			#Connect all dropdown boxes to the update counter method
			for combox in (
				ui.compagnyComboBox,
				ui.genreComboBox,
				ui.machineComboBox,
				ui.patchedComboBox,
				ui.typeComboBox,
				ui.yearComboBox
				):
				connect(
					combox,
					'currentIndexChanged(int)',
					self.findMatches
					)
			# connect regular buttons
			connect(
				ui.nextPushButton,
				'clicked()',
				self.on_nextPushButton_clicked
				)
			connect(
				ui.nextPushButton_2,
				'clicked()',
				self.on_nextPushButton_2_clicked
				)
			connect(
				ui.previousPushButton,
				'clicked()',
				self.on_previousPushButton_clicked
				)
			connect(
				ui.previousPushButton_2,
				'clicked()',
				self.on_previousPushButton_2_clicked
				)
			connect(
				ui.applyPushButton,
				'clicked()',
				self.on_applyPushButton_clicked
				)
			connect(
				ui.gamelistView,
				'cellClicked(int,int)',
				self.gamelistView_cellClicked
				)
		self.__ui.gamelistView.setSortingEnabled(0)
		self.__ui.gamelistView.horizontalHeader().setResizeMode(
			0, QtGui.QHeaderView.Stretch
			)
		self.__ui.gamelistView.horizontalHeader().hide()
		self.__ui.gamelistView.verticalHeader().hide()

		self.__ui.stackedPages.setCurrentIndex(0)
		self.findMatches()
		dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	def findMatches(self):
		query = 'SELECT count(*) ' + self.constructFromPartQuery()
		cursor = self.__cursor
		cursor.execute(query)
		for row in cursor:
			print row
			self.__ui.numbermatchesLabel.setText(str(row[0]))


	def constructFromPartQuery(self):
		ui = self.__ui
		#construct the query
		query = 'FROM software'
		where = []
		for gui, sqlstatement in (
			(ui.compagnyComboBox, 'Compagny'),
			(ui.genreComboBox, 'Genre'),
			(ui.machineComboBox, 'Machine'),
			(ui.patchedComboBox, 'Patched'),
			(ui.typeComboBox, 'Type'),
			(ui.yearComboBox, 'Year')
			):
			if gui.currentIndex() != 0:
				where.append( str(sqlstatement) + " = '" + str(gui.currentText() ) + "'" )


		for gui, sqlstatement in (
			(ui.nameinfoLabel, 'Info'),
			(ui.extentionsinfoLabel, 'HardwareExtension')
			):
			if gui.text() != 'not specified':
				where.append( sqlstatement + " like '%" + str(gui.text()) +"%'")
		if len(where) > 0:
			query += " WHERE "
		query += " AND ".join(where)
		#print query
		return query

	# Slots:

	@QtCore.pyqtSignature("")
	def on_previousPushButton_clicked(self):
		self.__ui.stackedPages.setCurrentIndex(0)

	@QtCore.pyqtSignature("")
	def on_previousPushButton_2_clicked(self):
		self.__ui.stackedPages.setCurrentIndex(1)

	@QtCore.pyqtSignature("")
	def on_nextPushButton_clicked(self):
		self.__ui.stackedPages.setCurrentIndex(1)
		query = 'SELECT * ' + self.constructFromPartQuery() + ' ORDER BY Info'
		cursor = self.__cursor
		cursor.execute(query)
		self.__selectedgameid = []
		index = 0
		for row in cursor:
			print row
			self.__ui.gamelistView.setRowCount(index + 1)
			founditem = QtGui.QTableWidgetItem(QtCore.QString(row[8])) # 'Info'
			founditem.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)
			self.__ui.gamelistView.setItem(index, 0, founditem)
			#item = QtGui.QTableWidgetItem(row[0]) # 'id'
			#item.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)
			#self.__ui.gamelistView.setItem(index, 1, item)

			self.__selectedgameid.append( row[0] )

			index += 1

		self.__ui.gamelistView.setRowCount(index + 1)
		self.showGameinfo( self.__selectedgameid[0] )

	@QtCore.pyqtSignature("")
	def on_nextPushButton_2_clicked(self):
		ui = self.__ui
		ui.stackedPages.setCurrentIndex(2)
		ui.gamenameLabel.setText(ui.label_name.text())
		for gui in (
			ui.diskaLabel ,
			ui.diskbLabel ,
			ui.cartaLabel ,
			ui.cartbLabel ,
			ui.machineLabel ,
			ui.extensionsLabel
			):
			gui.setText('empty')

		for gui in (
			ui.diskaCheckBox ,
			ui.diskbCheckBox ,
			ui.cartaCheckBox ,
			ui.cartbCheckBox ,
			ui.machineCheckBox ,
			ui.extensionsCheckBox
			):
			gui.setEnabled(True)


		query = 'SELECT * FROM software WHERE id=' + \
			str(self.__selectedgameid[ui.gamelistView.currentRow()]) + \
			' ORDER BY Info'
		cursor = self.__cursor
		cursor.execute(query)
		for row in cursor:
			print row
			ui.extensionsLabel.setText(row[5])
			ui.machineLabel.setText(row[6])
			ui.diskaLabel.setText(row[9])


	
	@QtCore.pyqtSignature("")
	def on_applyPushButton_clicked(self):
		ui = self.__ui
		#First of all change machine if needed
		if ui.machineCheckBox.isChecked():
			# Request machine change from openMSX.
			# TODO skip changing if openMSX is running with the correct machine
			self.__bridge.command('machine', ui.machineLabel.text())(
				self.__applyMedia,
				self.__machineChangeErrorHandler
				)

		# Then the needed extension
			#TODO implement this :-)

	def __applyMedia(self):
		# Insert(/eject) the media if requested
		ui = self.__ui
		for check, label, media in (
			( ui.diskaCheckBox, ui.diskaLabel, 'diska'),
			( ui.diskbCheckBox, ui.diskbLabel, 'diskb'),
			( ui.cartaCheckBox, ui.cartaLabel, 'carta'),
			( ui.cartbCheckBox, ui.cartbLabel, 'cartb')
			):
			print "xxxxxxxxxxxxxxxx" + str(media)
			if check.isChecked():
				print "yyyyyyyyyyyyyyyyy CHECKED"
				if label.text() == 'empty':
					self.__bridge.command( media, '-eject' )
					print "zzzzzzzzzzzzzzzzz -eject"
				else:
					self.__bridge.command( media, label.text() )
					print "zzzzzzzzzzzzzzzzz " + str(label.text())
			else:
				print "yyyyyyyyyyyyyyyyy not checked"
		# Do we actually want to close this dialog once a software is chosen ?
		self.__dmDialog.hide()


	def __machineChangeErrorHandler(self, message):
		messageBox =  QtGui.QMessageBox('Problem changing machine:', message,
				QtGui.QMessageBox.Warning, 0, 0, 0,
				self.__dmDialog
				)
		messageBox.show()




	def showGameinfo( self , softid ):
		query = "SELECT * FROM software WHERE id = '" + str(softid) + "'"
		print query
		cursor = self.__cursor
		cursor.execute(query)
		for row in cursor:
			#print row
			#info on page 2
			self.__ui.label_name.setText( QtCore.QString( row[8] ))
			self.__ui.label_compagny.setText( QtCore.QString( row[4] ))
			self.__ui.label_year.setText( QtCore.QString( row[2] ))
			self.__ui.label_machine.setText( QtCore.QString( row[6] ))
			self.__ui.label_genre.setText( QtCore.QString( row[7] ))


	def gamelistView_cellClicked( self, row, dummy ):
		self.showGameinfo( self.__selectedgameid[row] )

	#def __updateAll(self):
		# TODO: The idea of the name "updateAll" was to be able to deal with
		#       openMSX crashes. So, we should go back to knowing nothing about
		#       the openMSX state.
