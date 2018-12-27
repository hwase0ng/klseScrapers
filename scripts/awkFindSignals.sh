#!/bin/bash
datadir=/z/data
mpvdir=$datadir/mpv
signaldir=$mpvdir/signals
re='^[0-9]+$'

c=16
v=17
tripleM=18
tripleP=19
narrowM=20
narrowP=21
countP=22
lowbaseC=23
tripleBottoms=24
tripleTops=25

signalfile=""
val=0
val2=0
signal=""
signal2=""

while getopts ":s:S:v:V:c:d:" opt
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
  S)
   name=$OPTARG
   signal2=$(eval echo "\$$name")
   if [ -z ${signal2} ]
   then
   	echo "$name is not a valid signal!"
   	exit 3
   fi
   ;;
  v)
   val=$OPTARG
   if ! [[ "$val" =~ $re ]]
   then
    echo "$val is not an integer number!"
    exit 2
   fi
   ;;
  V)
   val2=$OPTARG
   if ! [[ "$val2" =~ $re ]]
   then
    echo "$val2 is not an integer number!"
    exit 2
   fi
   ;;
  *)
   #usage
   echo "Usage: awkFindSignals.sh -sSvVcd <signal name> <value> [counter] [datadir]" 1>&2
   exit 1
   ;;
 esac
done
shift $((OPTIND-1))
[ "${1:-}" = "--" ] && shift

if [ -z "$signal" -o "$val" -eq 0 ]
then
   echo "Usage: awkFindSignals.sh -sSvVcd <signal name> <value> [counter] [datadir]" 1>&2
   exit 1
fi

if [ -z "${signal2}" -o "${val2}" -eq 0 ]
then
    if [ -z $signalfile ]
	then
        awk -F'[,.]' -v sn=$signal -v val=$val '{if ($sn == val) {print $0}}' $@
    else
        awk -F'[,.]' -v sn=$signal -v val=$val '{if ($sn == val) {print $0}}' $signalfile
    fi
else
    if [ -z $signalfile ]
	then
        awk -F'[,.]' -v sn=$signal -v sn2=${signal2} -v val=$val -v val2=$val2 '{if ($sn == val && $sn2 == val2) {print $0}}' $@
    else
        awk -F'[,.]' -v sn=$signal -v sn2=${signal2} -v val=$val -v val2=$val2 '{if ($sn == val && $sn2 == val2) {print $0}}' $signalfile
    fi
fi