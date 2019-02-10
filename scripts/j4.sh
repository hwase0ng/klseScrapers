#!/bin/bash
MVP="CADJPY240 FOCUSP FTFBM100
FTFBMEMAS FTFBMMES FTFBM70 FTFBMKLCI FTFBMSCAP GHLSYS3 JMEDU 
LEBTECH LYC MPCORP MPI2 PADINI2 XINGHE YFG"

if [ $# -lt 1 ]
then
	echo "Usage: j4.sh <a2z>"
	exit 1
fi
for i in /z/data/mpv/${1}*.csv
do
	counter=`echo $i | awk -F[/.] '{print $5}'`
	if [ -n "`echo $MVP | xargs -n1 echo | grep -e \"^$counter$\"`" ]
	then
		echo "Skipped: $counter"
	else
	    python analytics/mvp.py -g $counter
        scripts/group.sh -o 1 -c $counter
    fi
done
