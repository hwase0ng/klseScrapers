#!/bin/bash
if [ $# -lt 1 ]
then
	echo "Usage: psd.sh [date] <counter>"
	exit 1
fi
cd /c/git/klseScrapers
if [ $# -gt 1 ]
then
 python analytics/mvpchart.py -psd -Ds -S $@
else
 python analytics/mvpchart.py -psd -Ds $@
fi
cd -