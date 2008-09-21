# $Id$
# call with:
# PYTHONPATH=derived python win32exe.py py2exe

from distutils.core import setup
import py2exe
import glob

setup(
	windows = [
		{
			"script": "derived/catapult.py",
			"icon_resources": [(0, "derived/catapult.ico")],
			"name": "openMSX Catapult",
			"version": "0.0.0",
			"description": "The GUI for openMSX",
			"author": "openMSX Team",
			"copyright": "(c) 2006-2008, openMSX Team",
			"comments": "beware that this is still a prototype!",
			"company_name": "openMSX Team"
		}
	],
	data_files = [
			("", glob.glob("derived/*.png"))
		],
	zipfile = None,
	options = {"py2exe": {
			"includes": ["sip", "PyQt4"],
			"dist_dir": "derived/dist",
                	"unbuffered": True,
			"optimize": 2,
			"bundle_files": 1,
			"compressed": 1
			}
		}
	)
