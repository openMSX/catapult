# $Id$

from PyQt4 import QtCore, QtGui
from qt_utils import connect

class SoftwareDB(object):

	def __init__(self, bridge):
		self.__dmDialog = None
		self.__ui = None
		self.__cursor = None
		self.__bridge = bridge
		self.__selectedgameid = []
		self.__currentshell = ''
		self.__commandshell = ''
		self.__destroyshell = False

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

			# Fill the components with values.
			# Since Python 2.5 SQLite is part of the standard library;
			# in case of python 2.4 we try to fall back to the external pysqlite2 module
			try:
				import sqlite3 as sqlite
			except:
				from pysqlite2 import dbapi2 as sqlite
			cursor = self.__cursor
			if cursor is None:
				connection = sqlite.connect('softdb.db')
				self.__cursor = cursor = connection.cursor()

			# First the Company
			ui.companyComboBox.addItem(QtCore.QString('Select...'))
			cursor.execute(
				'SELECT DISTINCT Company FROM software ORDER BY Company'
				)
			for row in cursor:
				ui.companyComboBox.addItem(QtCore.QString(row[0]))

			# The Genre
			ui.genreComboBox.addItem(QtCore.QString('Select...'))
			cursor.execute('SELECT DISTINCT Genre FROM software ORDER BY Genre')
			for row in cursor:
				ui.genreComboBox.addItem(QtCore.QString(row[0]))

			# The Machine
			ui.machineComboBox.addItem(QtCore.QString('Select...'))
			cursor.execute(
				'SELECT DISTINCT Machine FROM software ORDER BY Machine'
				)
			for row in cursor:
				ui.machineComboBox.addItem(QtCore.QString(row[0]))

			# The Patched
			ui.patchedComboBox.addItem(QtCore.QString('Select...'))
			cursor.execute(
				'SELECT DISTINCT Patched FROM software ORDER BY Patched'
				)
			for row in cursor:
				ui.patchedComboBox.addItem(QtCore.QString(row[0]))

			# The Type
			ui.typeComboBox.addItem(QtCore.QString('Select...'))
			cursor.execute('SELECT DISTINCT Type FROM software ORDER BY Type')
			for row in cursor:
				ui.typeComboBox.addItem(QtCore.QString(row[0]))

			# The Year
			ui.yearComboBox.addItem(QtCore.QString('Select...'))
			cursor.execute('SELECT DISTINCT Year FROM software ORDER BY Year')
			for row in cursor:
				ui.yearComboBox.addItem(QtCore.QString(row[0]))

			# Connect all dropdown boxes to the update counter method.
			for combox in (
				ui.companyComboBox,
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
			(ui.companyComboBox, 'Company'),
			(ui.genreComboBox, 'Genre'),
			(ui.machineComboBox, 'Machine'),
			(ui.patchedComboBox, 'Patched'),
			(ui.typeComboBox, 'Type'),
			(ui.yearComboBox, 'Year')
			):
			if gui.currentIndex() != 0:
				where.append( str(sqlstatement) + " = '"
					+ str(gui.currentText() ) + "'" )

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

	@QtCore.pyqtSignature('')
	def on_previousPushButton_clicked(self):
		self.__ui.stackedPages.setCurrentIndex(0)

	@QtCore.pyqtSignature('')
	def on_previousPushButton_2_clicked(self):
		self.__ui.stackedPages.setCurrentIndex(1)

	@QtCore.pyqtSignature('')
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
			founditem.setFlags(
				QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
				)
			self.__ui.gamelistView.setItem(index, 0, founditem)
			#item = QtGui.QTableWidgetItem(row[0]) # 'id'
			#item.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)
			#self.__ui.gamelistView.setItem(index, 1, item)

			self.__selectedgameid.append( row[0] )

			index += 1

		self.__ui.gamelistView.setRowCount(index + 1)
		self.showGameinfo( self.__selectedgameid[0] )

	@QtCore.pyqtSignature('')
	def on_nextPushButton_2_clicked(self):
		ui = self.__ui
		ui.stackedPages.setCurrentIndex(2)
		ui.gamenameLabel.setText(ui.label_name.text())
		for gui in (
			ui.diskaLabel,
			ui.diskbLabel,
			ui.cartaLabel,
			ui.cartbLabel,
			ui.machineLabel,
			ui.extensionsLabel
			):
			gui.setText('empty')

		for gui in (
			ui.diskaCheckBox,
			ui.diskbCheckBox,
			ui.cartaCheckBox,
			ui.cartbCheckBox,
			ui.machineCheckBox,
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

	@QtCore.pyqtSignature('')
	def on_applyPushButton_clicked(self):
		ui = self.__ui
		# First of all change machine if needed.
		#
		# The code originally used the 'machine' command and in the
		# callback fucntions the 'diska' commands were launched
		#
		# Unfortunately these disks were then still inserted in the old
		# msx shell which was about to be destroyed after the switch
		# was made.
		#
		# The 'Ok'-reply from the machine command seems to mean:
		# "machine command accept and will start in the near future"
		# and not "machine is switched"
		# 
		# Now we will create the msx shell ourself and delete the
		# current shell afterwards
		#
		self.__bridge.command('machine')(
			self.__setCurrentshell,
			self.__machineChangeErrorHandler
			)
		if ui.machineCheckBox.isChecked():
			# Request machine change from openMSX.
			# TODO: Skip change if openMSX is running with the correct machine.
			self.__destroyshell = True
			self.__bridge.command('create_machine')(
				self.__setCommandshell,
				self.__machineChangeErrorHandler
				)
		else:
			self.__destroyshell = False
			self.__bridge.command('machine', ui.machineLabel.text())(
				self.__setCommandshell,
				self.__machineChangeErrorHandler
				)

	def __setCurrentshell(self, message):
		self.__currentshell = message

	def __setCommandshell(self, message):
		self.__commandshell = message
		if self.__destroyshell:
			#load the new config for the new machine
			self.__bridge.command(str(self.__commandshell) + '::load_machine', self.__ui.machineLabel.text())(
				self.__applyExtensions,
				self.__machineChangeErrorHandler
			)
		else:
			#in correct machine config so resume with extensions
			self.__applyExtensions(message)

	def __applyExtensions(self, message):
		# Then the needed extension.
		# TODO: Implement this :-)
		# For now directly apply the needed media
		self.__applyMedia(message)

	def __applyMedia(self, message):
		# Insert(/eject) the media if requested
		ui = self.__ui
		for check, label, media in (
			( ui.diskaCheckBox, ui.diskaLabel, '::diska' ),
			( ui.diskbCheckBox, ui.diskbLabel, '::diskb' ),
			( ui.cartaCheckBox, ui.cartaLabel, '::carta' ),
			( ui.cartbCheckBox, ui.cartbLabel, '::cartb' )
			):
			setmedia = str(self.__commandshell) + str(media)
			if check.isChecked():
				if label.text() == 'empty':
					self.__bridge.command( setmedia, 'eject' )()
					print setmedia + " eject"
				else:
					self.__bridge.command( setmedia, label.text() )()
					print setmedia + " " + str(label.text())
			else:
				print "yyyyyyyyyyyyyyyyy not checked"
		#
		# Switch machine if needed
		#
		if self.__destroyshell:
			#TODO: find out in openMSX itself why this doesn't work
			#if you first activate the new one and then delte the
			#current one, aka switch the two lines
			self.__bridge.command( 'delete_machine' , self.__currentshell )()
			self.__bridge.command( 'activate_machine' , self.__commandshell )()
		# TODO: Do we actually want to close this dialog once a software is
		#       chosen?
		self.__dmDialog.hide()

	def __machineChangeErrorHandler(self, message):
		messageBox = QtGui.QMessageBox(
			'Problem changing machine:', message,
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
			self.__ui.label_name.setText(QtCore.QString(row[8]))
			self.__ui.label_company.setText(QtCore.QString(row[4]))
			self.__ui.label_year.setText(QtCore.QString(row[2]))
			self.__ui.label_machine.setText(QtCore.QString(row[6]))
			self.__ui.label_genre.setText(QtCore.QString(row[7]))

	def gamelistView_cellClicked(self, row, column): # pylint: disable-msg=W0613
		self.showGameinfo(self.__selectedgameid[row])

	#def __updateAll(self):
		# TODO: The idea of the name "updateAll" was to be able to deal with
		#       openMSX crashes. So, we should go back to knowing nothing about
		#       the openMSX state.
