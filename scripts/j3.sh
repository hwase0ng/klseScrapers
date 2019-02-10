#!/bin/bash
MVP="CADJPY240 CHGP CMMT CNOUHUA DEGEM DUFU EIG FOCUSP"
last="amedia bjfood censof"

if [ $# -lt 1 ]
then
	echo "Usage: j2.sh <a2z>"
	exit 1
fi
for i in /z/data/mpv/${1}*.csv
do
	counter=`echo $i | awk -F[/.] '{print $5}'`
	if [ -n "`echo $MVP | xargs -n1 echo | grep -e \"^$counter$\"`" ]
	then
		echo "Skipped: $counter"
	else
        echo $counter
	    invAwkPatchEOD.sh $counter
    fi
done
