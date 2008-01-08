#!/usr/bin/env python

"""This is a slideshow widget developed for Catapult the openMSX launcher"""

import sys
from PyQt4 import QtCore, QtGui

class Slideshow(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

	self.imageLabel = QtGui.QLabel()
        self.scrollArea = QtGui.QScrollArea(self)
	self.reset()

	self.timer = QtCore.QTimer(self)
	self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.slideTimeOut)

        self.imageLabel.setBackgroundRole(QtGui.QPalette.Base)
        self.imageLabel.setSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setAlignment(QtCore.Qt.AlignCenter)

	self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

	self.keepAspect = True
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
	self.scrollArea.resize(QtCore.QSize(40,40))
	self.updateGeometry()

    def slidepauzed(self):
	return self.slidePauzed

    def setSlidepauzed(self,b):
	print "def setSlidepauzed(self,b):"
	print b
	if b ==  self.slideStarted:
		return
	if b == False and self.slideStarted :
		self.slideStarted = False
		self.timer.stop()
	if b == True and not  self.slideStarted :
		self.slideStarted = True
		self.timer.start(self.slideSpeed)
	self.slidePauzed = b

    def setSlideSpeed(self,i):
	self.slideSpeed = i
	if  self.slideStarted:
		self.timer.stop()
		self.timer.start(self.slideSpeed)

    def keepaspect(self):
	return self.keepAspect

    def setKeepaspect(self,b):
	print "def setKeepaspect(self,b):"
	print b
	if self.keepAspect == b:
		return
	self.keepAspect = b
	self.adereToAspectAutozoom()

    def autozoom(self):
	return self.autozoom

    def setAutozoom(self,b):
	print "def setAutozoom(self,b):"
	print b
	if self.autozoom == b:
		return
	self.autozoom=b
	self.adereToAspectAutozoom()

    def adereToAspectAutozoom(self):
	if self.autozoom and not self.keepAspect:
		self.scrollArea.setWidgetResizable(True)
	else:
		self.scrollArea.setWidgetResizable(False)

	self.resizeImageLabel(self.scrollArea.contentsRect().size())

    def minimumSize(self):
	return QtCore.QSize(40,40)

    def setGeometry(self, r):
	QtGui.QWidget.setGeometry(r)

    def maximumSize(self):
    	print "maximumSize called"
    	return QtCore.QSize(self.maxImagWidth,self.maxImagHeight)

    def sizeHint(self):
    	return QtCore.QSize(self.maxImagWidth,self.maxImagHeight)

    def addFile(self,fileName):
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


    def loadFile(self,fileName):
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
	    if not self.autozoom:
                self.imageLabel.adjustSize()

	    if self.autozoom and self.keepAspect:
		h = event.height()
		w = event.width()
		ah = w * self.curImagHeight / self.curImagWidth
		aw = h * self.curImagWidth / self.curImagHeight 
		if aw > w :
			self.imageLabel.resize(QtCore.QSize(w,ah))
		else:
			self.imageLabel.resize(QtCore.QSize(aw,h))

    def findImagesForMedia(self,mediafile):
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
	    file = directory.absoluteFilePath(files[i])
	    ext = QtCore.QFileInfo(file).suffix().toLower();
	    print ext
	    if ext == "jpg" or ext == "png" or ext == "jpeg" or ext == "gif":
		    self.addFile(file)

    def scaleImage(self, factor):
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                                + ((factor - 1) * scrollBar.pageStep()/2)))


