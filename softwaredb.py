# $Id:$

from PyQt4 import QtCore, QtGui

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
				connection = sqlite.connect('test.db')
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
				connect(combox, 'currentIndexChanged(int)', self.findMatches)
			# connect regular buttons
			connect(ui.nextPushButton, 'clicked()', self.on_nextPushButton_clicked)
			connect(ui.nextPushButton, 'clicked()', self.on_nextPushButton_clicked)
			connect(ui.previousPushButton, 'clicked()', self.on_previousPushButton_clicked)
			connect(ui.gamelistView, 'cellClicked(int,int)', self.gamelistView_cellClicked)
		self.__ui.gamelistView.setSortingEnabled(0)
		self.__ui.gamelistView.horizontalHeader().setResizeMode( 0, QtGui.QHeaderView.Stretch)
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
		print query
		return query

	# Slots:

	@QtCore.pyqtSignature("")
	def on_previousPushButton_clicked(self):
		self.__ui.stackedPages.setCurrentIndex(0)

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

	def showGameinfo( self , id ):
		query = "SELECT * FROM software WHERE id = '" + str(id) + "'"
		print query
		cursor = self.__cursor
		cursor.execute(query)
		for row in cursor:
			print row
			self.__ui.label_name.setText( QtCore.QString( row[8] ))
			self.__ui.label_compagny.setText( QtCore.QString( row[4] ))
			self.__ui.label_year.setText( QtCore.QString( row[2] ))
			self.__ui.label_machine.setText( QtCore.QString( row[6] ))
			self.__ui.label_genre.setText( QtCore.QString( row[7] ))
		

	def gamelistView_cellClicked( self , row , column ):
		self.showGameinfo( self.__selectedgameid[row] )


	#def __updateAll(self):
		# TODO: The idea of the name "updateAll" was to be able to deal with
		#       openMSX crashes. So, we should go back to knowing nothing about
		#       the openMSX state.
