# $Id$
#call with python win32exe.py py2exe

from distutils.core import setup
import py2exe

setup(windows=[{"script" : "catapult.py"}], options={"py2exe" : {"includes" : ["sip", "PyQt4._qt"]}})
