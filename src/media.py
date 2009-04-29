# $Id$

from PyQt4 import QtCore, QtGui

from preferences import preferences
from qt_utils import connect
import settings
from ipsselector import ipsDialog
from mediamodel import Medium

def parseMediaSlot(mediaSlot):
	'''Returns a tuple ( mediumType, identifier) that corresponds to the given
	media slot.
	'''
	assert mediaSlot is not None, 'Invalid media slot! (None)'
	assert mediaSlot != '', 'Invalid media slot! (emtpy)'
	if mediaSlot == 'cassetteplayer':
		return 'cassette', None
	else:
		return mediaSlot[ : -1], mediaSlot[-1]

class MediaSwitcher(QtCore.QObject):

	def __init__(self, ui, mediaModel, settingsManager, machineManager):
		QtCore.QObject.__init__(self)
		self.__mediaModel = mediaModel
		self.__settingsManager = settingsManager
		self.__machineManager = machineManager
		self.__ui = ui
		self.__mediaSlot = None
		self.__cartPageInited = False
		# Connect to media model:
		ui.mediaList.setModel(mediaModel)
		mediaModel.dataChanged.connect(self.mediaPathChanged)
		mediaModel.mediaSlotRemoved.connect(self.setInfoPage)
		mediaModel.connected.connect(self.__connectSettings)
		# Connect view:
		connect(
			ui.mediaList.selectionModel(),
			'currentChanged(QModelIndex, QModelIndex)',
			self.updateMedia
			)
		connect(
			ui.mediaList, 'doubleClicked(QModelIndex)',
			self.browseMedia
			)
		connect(
			ui.mediaList, 'entered(QModelIndex)',
			self.showMediaToolTip
			)

		# Connect signals of media panels:
		# It is essential to keep the references, otherwise the classes are
		# garbage collected even though they have signal-slot connections
		# attached to them.
		self.__handlers = [
			handler(ui, self)
			for handler in ( DiskHandler, CartHandler,
				CassetteHandler, HarddiskHandler, CDROMHandler )
			]

	def __connectSettings(self):
		settingsManager = self.__settingsManager
		ui = self.__ui
		settingsManager.registerSetting('autoruncassettes', settings.BooleanSetting)
		settingsManager.connectSetting('autoruncassettes',
			ui.autoRunCassettesCheckBox)

	def __getHandlerByMediumType(self, mediumType):
		for handler in self.__handlers:
			if handler.mediumType == mediumType:
				return handler
		assert False, 'No handler found for mediumType "%s"' % mediumType

	def __getPageBySlot(self, mediaSlot):
		mediumType, identifier_ = parseMediaSlot(mediaSlot.getName())
		# Look up page widget for this mediumType.
		return getattr(self.__ui, mediumType + 'Page')

	def __getHandlerBySlot(self, mediaSlot):
		mediumType, identifier_ = parseMediaSlot(mediaSlot.getName())
		return self.__getHandlerByMediumType(mediumType)

	def __updateMediaPage(self, mediaSlot):
		mediumType, identifier = parseMediaSlot(mediaSlot.getName())
		handler = self.__getHandlerByMediumType(mediumType)
		# Initialise the UI page for this mediumType.
		handler.updatePage(identifier)

	@QtCore.pyqtSignature('QModelIndex')
	def updateMedia(self, index):
		oldMediaSlot = self.__mediaSlot
		# Find out which media entry has become active.
		mediaSlotName = str(index.data(QtCore.Qt.UserRole).toString())
		# prevent problems due to race conditions when removing slots:
		if mediaSlotName == '':
			return
		slot = self.__mediaModel.getMediaSlotByName(
				mediaSlotName, self.__machineManager.getCurrentMachineId()
				)
		#print '***********'
		#print 'mediaslot has currently become active: ', slot
		if oldMediaSlot is not None and oldMediaSlot.getName() == slot.getName():
			return
		if oldMediaSlot is not None:
			self.__getHandlerBySlot(oldMediaSlot).signalSetInvisible()
		self.__mediaSlot = slot
		self.__updateMediaPage(slot)
		# Switch page.
		self.__ui.mediaStack.setCurrentWidget(self.__getPageBySlot(slot))
		self.__getHandlerBySlot(slot).signalSetVisible()

	@QtCore.pyqtSignature('QModelIndex')
	def showMediaToolTip(self, index):
		# Find out which media entry has become active.
		mediaSlotName = str(index.data(QtCore.Qt.UserRole).toString())
		text = ''
		if mediaSlotName != '':
			slot = self.__mediaModel.getMediaSlotByName(
				mediaSlotName, self.__machineManager.getCurrentMachineId()
				)
			if slot.getMedium() != None:
				text = slot.getMedium().getPath()
		self.__ui.mediaList.setToolTip(text)

	@QtCore.pyqtSignature('QModelIndex')
	def browseMedia(self, index):
		# Find out which media entry has become active.
		mediaSlotName = str(index.data(QtCore.Qt.UserRole).toString())
		mediumType, identifier_ = parseMediaSlot(mediaSlotName)
		handler = self.__getHandlerByMediumType(mediumType)
		handler.browseImage()

	@QtCore.pyqtSignature('QModelIndex, QModelIndex')
	def mediaPathChanged(
		self, topLeft, bottomRight
		# pylint: disable-msg=W0613
		# TODO: We use the fact that we know MediaModel will only mark
		# one item changed at a time. This is not correct in general.
		):
		index = topLeft
		mediaSlotName = str(index.data(QtCore.Qt.UserRole).toString())
		if self.__mediaSlot is not None and \
			self.__mediaSlot.getName() == mediaSlotName and \
				mediaSlotName != '':
			self.__updateMediaPage(self.__mediaSlot)

	def setInfoPage(self):
		# TODO: this is called for each media hardware that is added or removed,
		# since switching machines will sent this event for each and
		# every drive/hd/cd/... this will be called several times in a row
		# do we need to handle this in a better way?
		if self.__mediaSlot is not None:
			self.__getHandlerBySlot(self.__mediaSlot).signalSetInvisible()
		self.__ui.mediaStack.setCurrentWidget(self.__ui.infoPage)
		self.__ui.mediaList.selectionModel().clear()
		self.__mediaSlot = None

	def insertMedium(self, medium):
		'''Sets a new medium for the currently selected slot.
		'''
		self.__mediaSlot.setMedium(medium,
			self.__mediaChangeErrorHandler
			)

	def __mediaChangeErrorHandler(self, message):
		messageBox = QtGui.QMessageBox('Problem changing media', message,
			QtGui.QMessageBox.Warning, 0, 0, 0,
			self.__ui.centralwidget
			)
		messageBox.show()

	def getMedium(self):
		return self.__mediaSlot.getMedium()

	def getSlot(self):
		return self.__mediaSlot

	def getRomTypes(self):
		return self.__mediaModel.getRomTypes()


class MediaHandler(QtCore.QObject):
	'''Base class for handling media stuff.
	The purpose is to make it easy to add a new media type, by
	only implementing/overriding what is specific for that new type
	in a specialized class.
	'''
	mediumType = None
	browseTitle = None
	imageSpec = None
	emptyPathDesc = None

	def __init__(self, ui, switcher):
		QtCore.QObject.__init__(self)
		self._ui = ui
		self._switcher = switcher

		# Look up UI elements.
		self._ejectButton = getattr(ui, self.mediumType + 'EjectButton', None)
		self._browseButton = getattr(ui, self.mediumType + 'BrowseImageButton')
		self._historyBox = getattr(ui, self.mediumType + 'HistoryBox')
		self._mediaLabel = getattr(ui, self.mediumType + 'Label')
		self._descriptionLabel = getattr(ui, self.mediumType + 'DescriptionLabel')

		# Load history.
		history = preferences.getList(self.mediumType + '/history')
		self._historyBox.addItems(history)
		# On OS X, the top item of the history is automatically put into
		# the edit box; this is not what we want, so we clear it.
		self._historyBox.clearEditText()

		# Connect signals.
		if (self._ejectButton):
			connect(self._ejectButton, 'clicked()', self.eject)
		connect(self._browseButton, 'clicked()', self.browseImage)
		connect(self._historyBox, 'activated(QString)', self._pathSelected)
		connect(self._historyBox.lineEdit(), 'editingFinished()', self.edited)

	def _pathSelected(self, path):
		print 'selected:', path or '<nothing>'
		if not path:
			return

		# Make sure the passed path is the current path in the UI (e.g.
		# after browse)
		self._historyBox.lineEdit().setText(path)

		self._insertMediumFromCurrentValues()

	def _createMediumFromCurrentDialog(self):
		'''Reads out the values from the current controls and composes the \
		   proper media object from it.
		'''
		path = unicode(self._historyBox.currentText())
		medium = Medium.create(self.mediumType, path)
		return medium

	def _insertMediumFromCurrentValues(self):
		'''Tells the model to insert the medium defined by the current controls.
		'''
		medium = self._createMediumFromCurrentDialog()

		self._addToHistory(medium)

		# Update the model.
		self._switcher.insertMedium(medium)

	def _addToHistory(self, medium):
		path = medium.getPath()
		historyBox = self._historyBox
		# Insert path at the top of the list.
		historyBox.insertItem(0, path)
		historyBox.setCurrentIndex(0)
		# Remove duplicates of the path from the history.
		index = 1
		while index < historyBox.count():
			if historyBox.itemText(index) == path:
				historyBox.removeItem(index)
			else:
				index += 1
		# Persist history.
		history = QtCore.QStringList()
		for index in range(historyBox.count()):
			history.append(historyBox.itemText(index))
		preferences[self.mediumType + '/history'] = history

	def eject(self):
		'''Removes the currently inserted medium.
		'''
		self._historyBox.clearEditText()
		self._switcher.insertMedium(None)

	def edited(self):
		'''Inserts the medium specified in the combobox line edit.
		'''
		self._pathSelected(self._historyBox.lineEdit().text())

	def browseImage(self):
		self._pathSelected(QtGui.QFileDialog.getOpenFileName(
			self._ui.mediaStack, self.browseTitle,
			self._historyBox.itemText(0) or QtCore.QDir.homePath(),
			self.imageSpec, None #, 0
			))

	
	def updatePage(self, identifier):
		medium = self._switcher.getMedium()
		
		if (self._ejectButton):
			self._ejectButton.setDisabled(medium is None)
		self._mediaLabel.setText(self._getLabelText(identifier))

		if medium:
			path = medium.getPath()
		else:
			path = ''

		fileInfo = QtCore.QFileInfo(path)

		if path == '':
			description = self.emptyPathDesc
		elif fileInfo.isDir():
			description = self._getDirDesc(fileInfo)
		elif fileInfo.isFile():
			lastDot = path.rfind('.')
			if lastDot == -1:
				ext = None
			else:
				ext = path[lastDot + 1 : ].lower()
			description = self._getFileDesc(fileInfo, ext)
		elif fileInfo.exists():
			description = 'Special file node'
		else:
			description = 'Not found'

		# TODO: Display "(read only)" somewhere if the media is
		#       read only for some reason:
		#       - image type that openMSX cannot write (XSA)
		#       - image file that is read-only on host file system
		#       I guess it's best if openMSX detects and reports this.
		#       The "mediaX" commands return a flag "readonly", but updates
		#       do not include flags.

		self._descriptionLabel.setText(description)

		self._historyBox.lineEdit().setText(path)
		self._historyBox.lineEdit().setToolTip(path)

	def _getLabelText(self, identifier):
		raise NotImplementedError

	def _getFileDesc(self, fileInfo, ext):
		raise NotImplementedError

	def _getDirDesc(self, dummy):
		# there's a default implementation in case
		# dirs are not supported
		return 'Not found'

	def signalSetVisible(self):
		'''Called when this page has become visible.
		'''
		# default implementation does nothing
		return

	def signalSetInvisible(self):
		'''Called when this page has become invisible
		'''
		# default implementation does nothing
		return

class PatchableMediaHandler(MediaHandler):
		# pylint: disable-msg=W0223
	'''Baseclass of a Mediahandler that supports IPS patches which should not
	be instantiated. (Hence we do not implement abstract methods of the baseclass.)
	'''
	def __init__(self, ui, switcher):
		MediaHandler.__init__(self, ui, switcher)

		# Look up UI elements.
		self._IPSButton = getattr(ui, self.mediumType + 'IPSButton', None)
		
		# Connect signals.
		connect(self._IPSButton, 'clicked()', self._IPSButtonClicked)

	def _createMediumFromCurrentDialog(self):
		baseMedium = MediaHandler._createMediumFromCurrentDialog(self)
		return baseMedium.copyWithNewPatchList(ipsDialog.getIPSList())

	def updatePage(self, identifier):
		MediaHandler.updatePage(self, identifier)

		medium = self._switcher.getMedium()
		if medium:
			patchList = medium.getIpsPatchList()
		else:
			patchList = []
		ipsDialog.fill(patchList)

	def _IPSButtonClicked(self):
		medium = self._switcher.getMedium()
		assert medium is not None, 'Click on IPS button without medium'
		if ipsDialog.exec_(self._IPSButton) == QtGui.QDialog.Accepted:
			self._insertMediumFromCurrentValues()
			
class DiskHandler(PatchableMediaHandler):
	mediumType = 'disk'
	browseTitle = 'Select Disk Image'
	imageSpec = 'Disk Images (*.dsk *.di? *.xsa *.zip *.gz);;All Files (*)'
	emptyPathDesc = 'No disk in drive'

	def __init__(self, ui, switcher):
		PatchableMediaHandler.__init__(self, ui, switcher)

		# Look up UI elements.
		self._browseDirButton = ui.diskBrowseDirectoryButton

		# Connect signals.
		connect(self._browseDirButton, 'clicked()', self.browseDirectory)

	def updatePage(self, identifier):
		PatchableMediaHandler.updatePage(self, identifier)
		medium = self._switcher.getMedium()
		if medium is None:
			self._ui.diskIPSLabel.setDisabled(True)
			self._IPSButton.setDisabled(True)
			amount = 0
		else:
			self._ui.diskIPSLabel.setEnabled(True)
			self._IPSButton.setEnabled(True)
			amount = len(medium.getIpsPatchList())
		self._ui.diskIPSLabel.setText('(' + str(amount) + ' selected)')

	def browseDirectory(self):
		self.insert(QtGui.QFileDialog.getExistingDirectory(
			self._ui.mediaStack, 'Select Directory',
			self._historyBox.itemText(0) or QtCore.QDir.homePath()
			))

	def _getLabelText(self, identifier):
		return 'Disk Drive %s' % identifier.upper()

	def _getFileDesc(self, fileInfo, ext):
		if ext in ('dsk', 'di1', 'di2'):
			description = 'Raw disk image'
			size = fileInfo.size()
			if size != 0:
				description += ' of %dkB' % (size / 1024)
		elif ext in ('xsa', 'zip', 'gz'):
			description = 'Compressed disk image'
		else:
			description = 'Disk image of unknown type'
		return description

	def _getDirDesc(self, fileInfo):
		return 'Directory as disk (%d entries)' % (
				fileInfo.dir().count()
			)

class CartHandler(PatchableMediaHandler):
	mediumType = 'cart'
	browseTitle = 'Select ROM Image'
	imageSpec = 'ROM Images (*.rom *.ri *.zip *.gz);;All Files (*)'
	emptyPathDesc = 'No cartridge in slot'

	def __init__(self, ui, switcher):
		PatchableMediaHandler.__init__(self, ui, switcher)

		self.__cartPageInited = False
		historyBox = self._historyBox

		mapperTypeHistory = preferences.getList(
					self.mediumType + 'mappertype/history'
					)
		# some backwards compatibility code:
		tooLittleItems = historyBox.count() - mapperTypeHistory.count()
		for dummy in xrange(tooLittleItems):
			mapperTypeHistory.append('Auto Detect')
		
		# fill our mapper type data dict
		self.__mapperTypeData = {}
	
		index = 0
		while index < historyBox.count():
			self.__mapperTypeData[
				unicode(historyBox.itemText(index))
				] = mapperTypeHistory[index]
			index += 1

		# Look up UI elements.
		self._mapperTypeCombo = ui.mapperTypeCombo

		# Connect signals.
		connect(self._mapperTypeCombo, 'activated(QString)',
			self.__mapperTypeSelected)

	def _createMediumFromCurrentDialog(self):
		baseMedium = PatchableMediaHandler._createMediumFromCurrentDialog(self)
		medium = Medium.create(
				self.mediumType, baseMedium.getPath(),
				baseMedium.getIpsPatchList(),
				str(self._mapperTypeCombo.currentText())
				)
		return medium

	def _pathSelected(self, path):
		print 'selected:', path or '<nothing>'
		if not path:
			return

		path = unicode(path)
		if path in self.__mapperTypeData:
			historyMapperType = self.__mapperTypeData[path]
			# restore mapper type from previous entry
			index = self._ui.mapperTypeCombo.findText(historyMapperType)
			self._ui.mapperTypeCombo.setCurrentIndex(index)

		PatchableMediaHandler._pathSelected(self, path)

	def _addToHistory(self, medium):
		PatchableMediaHandler._addToHistory(self, medium)

		path = medium.getPath()
		historyBox = self._historyBox
		self.__mapperTypeData[path] = medium.getMapperType()

		# Persist history (of mapper type).
		mapperTypeHistory = QtCore.QStringList()
		for index in range(historyBox.count()):
			mapperTypeHistory.append(self.__mapperTypeData[
				unicode(historyBox.itemText(index))
				])
		preferences[self.mediumType + 'mappertype/history'] = mapperTypeHistory

	def updatePage(self, identifier):
		PatchableMediaHandler.updatePage(self, identifier)
		if not self.__cartPageInited:
			# the next query might be empty, if it happens too soon
			mapperTypes = self._switcher.getRomTypes()
			if len(mapperTypes) != 0:
				self.__cartPageInited = True
				for item in mapperTypes:
					self._ui.mapperTypeCombo.addItem(QtCore.QString(item))
			else:
				print 'Interesting! We are preventing a race\
					condition here!'
		
		# set the mappertype combo to the proper value
		medium = self._switcher.getMedium()
		if medium is None:
			# mapper
			self._ui.mapperTypeCombo.setDisabled(True)
			index = self._ui.mapperTypeCombo.findText('Auto Detect')
			self._ui.mapperTypeCombo.setCurrentIndex(index)
			# patchlist
			self._ui.cartIPSLabel.setDisabled(True)
			self._IPSButton.setDisabled(True)
			amount = 0
		else:
			# mapper
			self._ui.mapperTypeCombo.setEnabled(True)
			mapperType = medium.getMapperType()
			index = self._ui.mapperTypeCombo.findText(mapperType)
			self._ui.mapperTypeCombo.setCurrentIndex(index)
			# patchlist
			self._ui.cartIPSLabel.setEnabled(True)
			self._IPSButton.setEnabled(True)
			amount = len(medium.getIpsPatchList())
		self._ui.cartIPSLabel.setText('(' + str(amount) + ' selected)')

	def __mapperTypeSelected(self, dummy):
		# We read it back from the combobox, so we don't need the
		# mapperType param here
		self._insertMediumFromCurrentValues()

	def _getLabelText(self, identifier):
		return 'Cartridge Slot %s' % identifier.upper()

	def _getFileDesc(self, fileInfo, ext):
		if ext in ('rom', 'ri'):
			description = 'ROM image'
			size = fileInfo.size()
			if size != 0:
				description += ' of %dkB' % (size / 1024)
				megabits = size / 1024 / 128
				if megabits == 1:
					description += ' (MegaROM)'
				elif megabits > 1:
					description += ' (%d MegaROM)' % megabits
		elif ext in ('zip', 'gz'):
			description = 'Compressed ROM image'
		else:
			description = 'ROM image of unknown type'
		return description

class CassetteHandler(MediaHandler):
	mediumType = 'cassette'
	browseTitle = 'Select Cassette Image'
	imageSpec = 'Cassette Images (*.cas *.wav *.zip *.gz);;All Files (*)'
	emptyPathDesc = 'No cassette in deck'

	play = 'play'
	rewind = 'rewind'
	stop = 'stop'
	record = 'record'

	def __init__(self, ui, switcher):
		MediaHandler.__init__(self, ui, switcher)

		# Look up UI elements.

		self.__pollTimer = QtCore.QTimer()
		self.__pollTimer.setInterval(500)

		self.__isVisible = False

		# Connect signals.
		connect(ui.tapePlayButton, 'clicked()', self.__playButtonClicked)
		connect(ui.tapeRewindButton, 'clicked()', self.__rewindButtonClicked)
		connect(ui.tapeStopButton, 'clicked()', self.__stopButtonClicked)
		connect(ui.tapeRecordButton, 'clicked()', self.__recordButtonClicked)
		connect(self.__pollTimer, 'timeout()', self.__queryTimes)
	
		self.__buttonMap = {
			self.play: ui.tapePlayButton,
			self.rewind: ui.tapeRewindButton,
			self.stop: ui.tapeStopButton,
			self.record: ui.tapeRecordButton,
		}

	def updatePage(self, identifier):
		MediaHandler.updatePage(self, identifier)
		medium = self._switcher.getMedium()
		if medium:
			length = medium.getLength()
		else:
			self.__updateTapePosition(0)
			length = 0
		self.__updateTapeLength(length)
		self._ui.tapeTime.setDisabled(medium is None)
		self._ui.tapeLength.setDisabled(medium is None)
		deck = self._switcher.getSlot()
		self.__updateButtonState(deck.getState())

	def __updateButtonState(self, newState):
		for state, button in self.__buttonMap.iteritems():
			button.setChecked(newState == state)
		if newState in ['play', 'record'] and self.__isVisible:
			self.__pollTimer.start()
		if newState == 'stop':
			self.__pollTimer.stop()
			if self.__isVisible:
				self.__queryTimes() # make sure end time is correct

	def __playButtonClicked(self):
		path = self._historyBox.currentText()
		if path == '':
			self.browseImage()
		else:
			deck = self._switcher.getSlot()
			deck.play(self.__errorHandler)
			# prevent toggling behaviour of play button:
			self.__updateButtonState(deck.getState())

	def __rewindButtonClicked(self):
		deck = self._switcher.getSlot()
		deck.rewind(self.__errorHandler)

	def __stopButtonClicked(self):
		# restore button state (this is actually a 'readonly' button)
		deck = self._switcher.getSlot()
		self.__updateButtonState(deck.getState())

	def __recordButtonClicked(self):
		filename = QtGui.QFileDialog.getSaveFileName(
			None, 'Enter New File for Cassette Image',
			QtCore.QDir.homePath(),
			'Cassette Images (*.wav);;All Files (*)',
			None #, 0
			)
		deck = self._switcher.getSlot()
		if filename == '':
			self.__updateButtonState(deck.getState())
		else:
			self.__updateTapeLength(0)
			deck.record(filename, self.__errorHandler)
	
	def __errorHandler(self, message):
		messageBox = QtGui.QMessageBox('Cassette deck problem', message,
				QtGui.QMessageBox.Warning, 0, 0, 0,
				self._ui.tapeStopButton
				)
		messageBox.show()
		deck = self._switcher.getSlot()
		self.__updateButtonState(deck.getState())

	def __updateTapeLength(self, length):
		zeroTime = QtCore.QTime(0, 0, 0)
		time = zeroTime.addSecs(round(float(length)))
		self._ui.tapeLength.setTime(time)
		
	def __updateTapePosition(self, position):
		deck = self._switcher.getSlot()
		if not deck: # can happen due to race conditions
			return
		zeroTime = QtCore.QTime(0, 0, 0)
		time = zeroTime.addSecs(round(float(position)))
		self._ui.tapeTime.setTime(time)
		# for now, we can have this optimization:
		if (deck.getState() == 'record'):
			self.__updateTapeLength(position)

	def __queryTimes(self):
		#medium = self._switcher.getMedium()
		# don't do something like this for now, but use the optimization
		# that length == position when recording, see above
		# deck = self._switcher.getSlot()
#		if (deck.getState() == 'record'):
#			medium.getTapeLength(self.__updateTapeLength,
#				self.__errorHandler
#			)
		self._switcher.getSlot().getPosition(self.__updateTapePosition,
			# errors can occur if cassetteplayer got removed
			lambda message: self.__updateTapePosition(0)
		)

	def signalSetVisible(self):
		assert self.__isVisible == False, 'Um, we already were visible!?'
		self.__isVisible = True
		# start timer in case we are in play or record mode
		deck = self._switcher.getSlot()
		state = deck.getState()
		if state in ['play', 'record']:
			self.__pollTimer.start()
		self._switcher.getSlot().stateChanged.connect(self.__updateButtonState)


	def signalSetInvisible(self):
		assert self.__isVisible == True, 'Um, we were not even visible!?'
		self.__isVisible = False
		# always stop timer
		self.__pollTimer.stop()
		self._switcher.getSlot().stateChanged.disconnect(self.__updateButtonState)

	def _getLabelText(self, dummy):
		return 'Cassette Deck'

	def _getFileDesc(self, dummy, ext):
		if ext == 'cas':
			description = 'Cassette image in CAS format'
		elif ext == 'wav':
			description = 'Raw cassette image'
		elif ext in ('zip', 'gz'):
			description = 'Compressed cassette image'
		else:
			description = 'Cassette image of unknown type'
		return description

class HarddiskHandler(MediaHandler):
	mediumType = 'hd'
	browseTitle = 'Select Hard Disk Image'
	imageSpec = 'Hard Disk Images (*.dsk *.zip *.gz);;All Files (*)'
	emptyPathDesc = 'No hard disk in drive'

	def _getLabelText(self, identifier):
		return 'Hard Disk Drive %s' % identifier.upper()

	def _getFileDesc(self, fileInfo, ext):
		if ext == 'dsk':
			description = 'Raw hard disk image'
			size = fileInfo.size()
			if size != 0:
				description += ' of %dMB' % (size / 1024 / 1024)
		elif ext in ('zip', 'gz'):
			description = 'Compressed hard disk image'
		else:
			description = 'Hard disk image of unknown type'
		return description

class CDROMHandler(MediaHandler):
	mediumType = 'cd'
	browseTitle = 'Select CD-ROM Image'
	imageSpec = 'CD-ROM Images (*.iso *.zip *.gz);;All Files (*)'
	emptyPathDesc = 'No CD-ROM in drive'

	def _getLabelText(self, identifier):
		return 'CD-ROM Drive %s' % identifier.upper()

	def _getFileDesc(self, fileInfo, ext):
		if ext == 'iso':
			description = 'ISO CD-ROM image'
			size = fileInfo.size()
			if size != 0:
				description += ' of %dMB' % (size / 1024 / 1024)
		elif ext in ('zip', 'gz'):
			description = 'Compressed CD-ROM image'
		else:
			description = 'CD-ROM image of unknown type'
		return description
