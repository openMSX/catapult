$Id: ChangeLog 1 2008-01-11 21:10:03Z Vampier $

#call with python win32exe.py py2exe

from distutils.core import setup
import py2exe

setup(windows=[{"script" : "catapult.py"}], options={"py2exe" : {"includes" : ["sip", "PyQt4._qt"]}})
