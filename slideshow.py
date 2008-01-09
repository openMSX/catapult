#!/usr/bin/env python

"""This is a slideshow widget developed for Catapult the openMSX launcher"""

from PyQt4 import QtCore, QtGui

class Slideshow(QtGui.QWidget):
	def __init__(self, parent=None):
		QtGui.QWidget.__init__(self, parent)

		self.imageLabel = QtGui.QLabel()
		self.scrollArea = QtGui.QScrollArea(self)
		#following self.variables are defined here to satisfy pylint
		#there values are altered by the reset() anyway
		self.files = []
		self.autoHide = False
		self.slideSpeed = 3000
		self.slideStarted = False
		self.slidePauzed = False
		self.currentSlide = 0
		self.curImagWidth = 40
		self.curImagHeight = 40
		self.maxImagWidth = 40
		self.maxImagHeight = 40

		self.reset()

		self.timer = QtCore.QTimer(self)
		self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.slideTimeOut)

		self.imageLabel.setBackgroundRole(QtGui.QPalette.Base)
		self.imageLabel.setSizePolicy(QtGui.QSizePolicy.Ignored,
			QtGui.QSizePolicy.Ignored)
		self.imageLabel.setScaledContents(True)

		self.scrollArea.setWidget(self.imageLabel)
		self.scrollArea.setAlignment(QtCore.Qt.AlignCenter)

		self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

		self.keepAspect = True
		#following self.__autozoom is defined here to satisfy pylint
		self.__autozoom = True
		self.setAutozoom(True)

	def reset(self):
		self.files = []
		self.autoHide = False
		self.slideSpeed = 3000
		self.slideStarted = False
		self.slidePauzed = False
		self.currentSlide = 0
		
		self.curImagWidth = 40
		self.curImagHeight = 40
		self.maxImagWidth = 40
		self.maxImagHeight = 40
		self.imageLabel.setText("No images")
		self.scrollArea.setWidgetResizable(False)
		self.imageLabel.adjustSize()
		self.scrollArea.resize(QtCore.QSize(40, 40))
		self.updateGeometry()

	def slidepauzed(self):
		return self.slidePauzed

	def setSlidepauzed(self, value):
		print "def setSlidepauzed(self, value):"
		print value
		if value ==  self.slideStarted:
			return
		if value == False and self.slideStarted :
			self.slideStarted = False
			self.timer.stop()
		if value == True and not  self.slideStarted :
			self.slideStarted = True
			self.timer.start(self.slideSpeed)
		self.slidePauzed = value

	def setSlideSpeed(self, value):
		self.slideSpeed = value
		if  self.slideStarted:
			self.timer.stop()
			self.timer.start(self.slideSpeed)

	def keepaspect(self):
		return self.keepAspect

	def setKeepaspect(self, value):
		print "def setKeepaspect(self, value):"
		print value
		if self.keepAspect == value:
			return
		self.keepAspect = value
		self.adereToAspectAutozoom()

	def autozoom(self):
		return self.__autozoom

	def setAutozoom(self, value):
		print "def setAutozoom(self, value):"
		print value
		if self.__autozoom == value:
			return
		self.__autozoom = value
		self.adereToAspectAutozoom()

	def adereToAspectAutozoom(self):
		if self.__autozoom and not self.keepAspect:
			self.scrollArea.setWidgetResizable(True)
		else:
			self.scrollArea.setWidgetResizable(False)

		self.resizeImageLabel(self.scrollArea.contentsRect().size())

	def minimumSize(self):
		return QtCore.QSize(40, 40)

	def setGeometry(self, value):
		QtGui.QWidget.setGeometry(value)

	def maximumSize(self):
		print "maximumSize called"
		return QtCore.QSize(self.maxImagWidth, self.maxImagHeight)

	def sizeHint(self):
		return QtCore.QSize(self.maxImagWidth, self.maxImagHeight)

	def addFile(self, fileName):
		print fileName
		self.files.append(fileName)
		self.loadFile(fileName)
		if not self.slideStarted and not self.slidePauzed:
			self.slideStarted = True
			self.timer.start(self.slideSpeed)

	def slideTimeOut(self):
		self.nextSlide()

	def nextSlide(self):
		if len(self.files) > 1:
			self.currentSlide =  self.currentSlide + 1
			if self.currentSlide >= len(self.files):
				self.currentSlide = 0
			self.loadFile(self.files[self.currentSlide])


	def loadFile(self, fileName):
		#if not fileName.isEmpty():
		image = QtGui.QImage(fileName)
		if image.isNull():
			QtGui.QMessageBox.information(self, self.tr("Image Viewer"),
				self.tr("Cannot load %1.").arg(fileName))
			return

		self.imageLabel.setPixmap(QtGui.QPixmap.fromImage(image))
		self.curImagWidth = image.width()
		if self.maxImagWidth < image.width():
			self.maxImagWidth = image.width()
		self.curImagHeight = image.height()
		if self.maxImagHeight < image.height():
			self.maxImagHeight = image.height()
		self.resizeImageLabel(self.scrollArea.contentsRect().size())
		#self.updateGeometry()

	def resizeEvent(self, event):
		self.scrollArea.resize(event.size())
		self.resizeImageLabel(self.scrollArea.contentsRect().size())

	def resizeImageLabel(self, event):
		if not self.__autozoom:
			self.imageLabel.adjustSize()

		if self.__autozoom and self.keepAspect:
			ch = event.height()
			cw = event.width()
			ah = cw * self.curImagHeight / self.curImagWidth
			aw = ch * self.curImagWidth / self.curImagHeight
			if aw > cw :
				self.imageLabel.resize(QtCore.QSize(cw, ah))
			else:
				self.imageLabel.resize(QtCore.QSize(aw, ch))

	def findImagesForMedia(self, mediafile):
		info = QtCore.QFileInfo(mediafile)
		path = info.path()
		filename  = info.completeBaseName()
		print filename
		# We strip off the 2 last suffixes ourself.
		# Using baseName() might strip off too much.
		# Each suffix might be max 4 chars, this will take
		# care of all '.crt.gz','dsk.gz' etc
		if filename.lastIndexOf(".") >= (filename.length() - 4):
			filename = filename.left( filename.lastIndexOf(".") )
		if filename.lastIndexOf(".") >= (filename.length() - 4):
			filename = filename.left( filename.lastIndexOf(".") )
		filename = filename + "*"

		directory = QtCore.QDir(path)
		files = QtCore.QStringList()
		files = directory.entryList(QtCore.QStringList(filename),
				QtCore.QDir.Files | QtCore.QDir.NoSymLinks)
		for i in range(files.count()):
			imgfile = directory.absoluteFilePath(files[i])
			ext = QtCore.QFileInfo(imgfile).suffix().toLower()
			print ext
			if ext == "jpg" or ext == "png" or ext == "jpeg" or ext == "gif":
				self.addFile(imgfile)

	def scaleImage(self, factor):
		self.scaleFactor *= factor
		self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

		self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
		self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

	def adjustScrollBar(self, scrollBar, factor):
		scrollBar.setValue(int(factor * scrollBar.value()
			+ ((factor - 1) * scrollBar.pageStep()/2)))


