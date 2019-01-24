#!/bin/bash
if [ $# -lt 1 ]
then
	echo "Usage: j1.sh <a2z>"
	exit 1
fi
for i in /z/data/mpv/${1}*.csv
do
	counter=`echo $i | awk -F[/.] '{print $5}'`
	echo $counter
	group.sh -o 1 -c $counter
done