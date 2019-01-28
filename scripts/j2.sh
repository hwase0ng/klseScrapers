#!/bin/bash
if [ $# -lt 1 ]
then
	echo "Usage: j2.sh <a2z>"
	exit 1
fi
for i in /z/data/mpv/${1}*.csv
do
	counter=`echo $i | awk -F[/.] '{print $5}'`
	# if [ -n "`echo $LIST | sed 's|:|\\n|g' | grep -e \"^$VALUE`$\"`" ]; then
	invDownloadEOD.sh $counter
done
