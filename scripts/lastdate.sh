#!/bin/bash
OPTIND=1
DATADIR=/z/data
COUNTER=""

while getopts ":c:d:" opt
do
 case "$opt" in
  c)
   COUNTER=`echo ${OPTARG} | tr '[:lower:]' '[:upper:]'`
   ;;
  d)
   DATADIR=$OPTARG
   if ! [ -d $DATADIR ]
   then
    echo $DATADIR is not a valid directory!
    exit 1
   fi
   ;;
 esac
done
shift $((OPTIND-1))
[ "${1:-}" = "--" ] && shift

if [ -z $COUNTER ]
then
	echo "Usage: $0 -c <counter> -d [datadir]"
	exit 1
fi

/usr/bin/ls -l ${DATADIR}/json/${COUNTER}*.json | /usr/bin/tail -1 | /usr/bin/awk '{print $NF}' | /usr/bin/awk -F[_.] '{print $2}'