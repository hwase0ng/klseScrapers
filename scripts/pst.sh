#!/bin/bash
if [ $# -lt 1 ]
then
	echo "Usage: pst.sh [date] <counter>"
	exit 1
fi
cd /c/git/klseScrapers
if [ $# -gt 1 ]
then
 python analytics/mvpchart.py -ps -Du -S $@
else
 python analytics/mvpchart.py -ps -Du $@
fi
