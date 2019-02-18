#!/bin/bash
MVP="CADJPY240 EIG FOCUSP FTFBM100 FTFBMEMAS FTFBMMES FTFBM70 FTFBMKLCI FTFBMSCAP GHLSYS3 JMEDU LEBTECH LYC MPCORP MPI2 PADINI2 XINGHE YFG"

if [ -z "$1" ]
then
	initials=[1-Z]
else
	initials=$1
fi

for i in /z/data/mpv/${initials}*.csv
do
	counter=`echo $i | awk -F[/.] '{print $5}'`
	if ! [ -n "`echo $MVP | xargs -n1 echo | grep -e \"^$counter$\"`" ]
	then
	    echo $counter
    fi
done

#if [ $# -lt 1 ]
#then
#	echo "Usage: counters.sh [a2z]"
#fi