#!/bin/bash
MVP="KLSE N2N PADINI PETRONM KESM YSPSAH SCGM VSTECS GHLSYS MAGNI MUDA ORNA RANHILL RAPI RCECAP"
if [ $# -lt 1 ]
then
	echo "Usage: j1.sh <a2z>"
	exit 1
fi
for i in /z/data/mpv/${1}*.csv
do
	counter=`echo $i | awk -F[/.] '{print $5}'`
	# if [ -n "`echo $LIST | sed 's|:|\\n|g' | grep -e \"^$VALUE`$\"`" ]; then
	if [ -n "`echo $MVP | xargs -n1 echo | grep -e \"^$counter$\"`" ]
	then
		echo "Skipped: $counter"
	else
		group.sh -o 1 -c $counter
	fi
done
