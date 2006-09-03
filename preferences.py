# $Id$

from PyQt4 import QtCore
from custom import *

preferences = QtCore.QSettings('openMSX Team', 'openMSX Catapult')

# set defaults for keys if they don't exist
# TODO: try to determine sensible defaults automatically
preferences.beginGroup('dirs')

# openMSX documentation directory.
if not preferences.contains('doc'):
	preferences.setValue('doc', QtCore.QVariant(docDir))

# A directory containing MSX ROM images.
# This is used as the default directory to browse for ROM images.
if not preferences.contains('initialrom'):
	preferences.setValue('initialrom', QtCore.QVariant(initialRomDir))

# A directory containing MSX disk images.
# This is used as the default directory to browse for disk images.
if not preferences.contains('initialdisk'):
	preferences.setValue('initialdisk', QtCore.QVariant(initialDiskDir))

# A directory containing MSX cassette images.
# This is used as the default directory to browse for cassette images.
if not preferences.contains('initialcas'):
	preferences.setValue('initialcas', QtCore.QVariant(initialCasDir))

preferences.endGroup()


preferences.beginGroup('system')

# openMSX executable.
if not preferences.contains('executable'):
	preferences.setValue('executable', QtCore.QVariant(executable))

preferences.endGroup()
