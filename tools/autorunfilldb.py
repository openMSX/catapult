#!/usr/bin/env python
# $Id:$

from PyQt4 import QtCore, QtGui
import os, sys

try:
	import sqlite3 as sqlite
except:
	from pysqlite2 import dbapi2 as sqlite

def createdbfiles(tablename):
	sqlfile = tablename + '.sql'
	infile = tablename + '.txt'
	outfile = tablename + '.db'
	#erase outfile if exists already :-)
	if os.path.exists(outfile):
		os.unlink(outfile)
		print "Erased old " + outfile
	
	f = open(sqlfile, 'r')
	createsql = f.readline()
	createsql.rstrip()

	toexec = f.readline()
	toexec.rstrip()

	print "Used to create : " + createsql
	print "Used to insert : " + toexec

	# connect will create the outfile again
	connection = sqlite.connect(outfile)
	cursor = connection.cursor()

	#creating the DB
	cursor.execute(createsql)

	#Filling the DB
	f = open(infile, 'r')
	headerline = f.readline()
	items = []

	for line in f:
		line = line.rstrip()
		items = line.split(';')
		if len(items) > 2:
			items[2] = items[2].decode('string_escape')
		# print items[2]
		cursor.execute(toexec, items )

	#cursor.execute('INSERT INTO software VALUES (null, "John Doe", "jdoe@jdoe.zz")')
	#name = "Luke Skywalker"
	#email ="use@the.force"
	#cursor.execute('INSERT INTO software VALUES (null, ?, ?)', (name, email))
	#cursor.lastrowid
	connection.commit()
	print "*********************************************************"

##retrieving data
#cursor.execute('SELECT count(*) FROM autorun')
#print cursor.fetchall()

#cursor.execute('SELECT count(*) FROM autorun WHERE Media LIKE "Cart"')
#print cursor.fetchall()

#cursor.execute('SELECT count(*) FROM autorun WHERE Media LIKE "Disk"')
#print cursor.fetchall()

#print
#print "*********************************************************"
#print

#cursor.execute('SELECT * FROM autorun ')
#print '-'*10
#for row in cursor:
#  print row
#print '-'*10


createdbfiles('autorun')
createdbfiles('softdb')
createdbfiles('hwimages')

