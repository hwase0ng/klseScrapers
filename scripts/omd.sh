#!/bin/bash
if [ $# -lt 1 ]
then
	echo "Usage: omd.sh [date] <counter>"
	exit 1
fi
cd /c/git/klseScrapers
if [ $# -gt 1 ]
then
 python analytics/mvpchart.py -omd -Ds -S $@
else
 python analytics/mvpchart.py -omd -c 100 -Ds $@
fi
cd -
