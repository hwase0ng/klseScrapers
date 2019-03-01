#!/bin/bash
MVP="CADJPY240 EIG FOCUSP FTFBM100 FTFBMEMAS FTFBMMES FTFBM70 FTFBMKLCI FTFBMSCAP GHLSYS3 JMEDU LEBTECH LYC MPCORP MPI2 PADINI2 XINGHE YFG"

if [ $# -lt 1 ]
then
	echo "Usage: patchcsv.sh <a2z>"
	exit 1
fi
for i in /z/data/mpv/${1}*.csv
do
	counter=`echo $i | awk -F[/.] '{print $5}'`
	if [ -n "`echo $MVP | xargs -n1 echo | grep -e \"^$counter$\"`" ]
	then
		echo "Skipped: $counter"
	else
		python utils/patchcsv.py $counter
		python analytics/mvp.py -g $counter
		if ls data/json/$counter.2019-01*.json 1> /dev/null 2>&1
		then
			echo "re-generating missing JSON file for $counter"
			jmissing.sh $counter
		else
			echo "generating JSON file for $counter"
			scripts/group.sh -o 1 -c $counter
	    fi
	fi
done
