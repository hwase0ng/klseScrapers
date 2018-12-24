#!/bin/bash
if [ $# -lt 2 ]
then
	echo "Usage: psd.sh <date> <counter>"
	exit 1
fi
cd /c/git/klseScrapers
python analytics/mvpchart.py -psd -Ds -S $@
cd -