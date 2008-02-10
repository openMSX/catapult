#!/bin/sh
HERE=`dirname $0`
LOG=$HERE/../../../app.log
date > $LOG
PYTHONDIR=/System/Library/Frameworks/Python.framework/Versions/Current
export PYTHONPATH=`find $PYTHONDIR/lib/ -name "python*" -depth 1 | sort | tail -n 1`/site-packages
echo "$PYTHONPATH" >> $LOG
exec $PYTHONDIR/bin/python $HERE/catapult.py >> $LOG 2&>1
