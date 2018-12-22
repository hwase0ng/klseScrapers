#!/bin/bash
datadir=/z/data
mpvdir=$datadir/mpv
signaldir=$mpvdir/signals

c=16
v=17
mp=18
narrowM=19
lowbaseC=20
tripleM10=21
tripleBottoms=22
tripleTops=23
retrace=24

signalfile=""
val=0

while getopts ":s:v:c:d:" opt
do
 case "$opt" in
  c)
   counter=$OPTARG
   signalfile=${signaldir}/${counter}-signals.csv
   if ! [ -f $signalfile ]
   then
    echo "$signalfile not found" 1>&2
    exit 5
   fi
   ;;
  d)
   datadir=$OPTARG
   if ! [ -d $datadir ]
   then
    echo $datadir is not a directory!
    exit 4
   fi
   ;;
  s)
   name=$OPTARG
   signal=$(eval echo "\$$name")
   if [ -z $signal ]
   then
   	echo "$name is not a valid signal!"
   	exit 3
   fi
   ;;
  v)
   val=$OPTARG
   if ! [[ "$val" =~ $re ]]
   then
    echo "$val must be an integer number!"
    exit 2
   fi
   ;;
  *)
   #usage
   echo "Usage: awkFindSignals.sh -vsd <value> <signal name> [datadir]" 1>&2
   exit 1
   ;;
 esac
done
shift $((OPTIND-1))
[ "${1:-}" = "--" ] && shift

if [ -z $signal -o $val == 0 ]
then
   echo "Usage: awkFindSignals.sh -svcd <signal name> <value> [counter] [datadir]" 1>&2
   exit 1
fi

if [ -z $signalfile ]
then
	awk -F'[,.]' -v fn=$signal -v val=$val '{if ($fn == val) {print $0}}' $@
else
	awk -F'[,.]' -v fn=$signal -v val=$val '{if ($fn == val) {print $0}}' $signalfile
fi