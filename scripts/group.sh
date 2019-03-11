#!/bin/bash
OPTIND=1
source /c/git/klseScrapers/scripts/groups.klse

CHARTDAYS=500  # 2013-09-10 KESM newlowM gets blocked if 600
INDIR=/z/data
TMPDIR=data
GROUP=
ENDDT=`date +%Y-%m-%d`
OPT=1
STEPS=2
re='^[0-9]+$'
dateopt=0

#usage() { echo "Usage: group.sh -cds [counter(s)] [start date] [steps]" 1>&2; exit 1 }

while getopts ":c:C:d:g:o:s:D:" opt
do
 case "$opt" in
  C)
   CHARTDAYS=$OPTARG
   if ! [[ "$CHARTDAYS" =~ $re ]]
   then
    echo "$CHARTDAYS is not an integer number!"
    exit 2
   fi
   ;;
  D)
   INDIR=$OPTARG
   if ! [ -d $INDIR ]
   then
    echo $INDIR is not a valid directory!
    exit 2
   fi
   ;;
  d)
   STARTDT=$OPTARG
   dateopt=1
   ;;
  c)
   GROUP=$OPTARG
   ;;
  o)
   OPT=$OPTARG
   if [ $OPT -eq 1 -o $OPT -eq 5 ]
   then
    STEPS=1
   fi
   ;;
  s)
   STEPS=$OPTARG
   if ! [[ "$STEPS" =~ $re ]]
   then
    echo "$STEPS is not an integer number!"
    exit 2
   fi
   ;;
  g)
   SET=`echo ${OPTARG} | tr '[:lower:]' '[:upper:]'`
   #echo $(eval echo "\$$SET")
   GROUP=$(eval echo "\$$SET")
   ;;
  *)
   #usage
   echo "Usage: group.sh -cCdgoDs [counter] [Chartdays] [date] [groups] [opt=1234] [Dir] [steps]" 1>&2
   echo "  opt: 1 - gen JSON, 2 - Signal scanning, 3 - Daily Charting only, 4-signals without plot, 5-gen JSON for selected files, 6-WFM charting" 1>&2
   exit 1
   ;;
 esac
done
shift $((OPTIND-1))
[ "${1:-}" = "--" ] && shift
#echo "c=$GROUP, D=$INDIR, d=$STARTDT, e=$ENDDT, s=$STEPS, leftovers: $@"
if [ -z "$GROUP" ]
then
   echo "Usage: group.sh -cCdgoDs [counter] [Chartdays] [date] [groups] [opt=1234] [Dir] [steps]" 1>&2
   echo "  opt: 1-gen json, 2-scan signals, 3-daily charting only, 4-signals without plot, 5-gen JSON for selected files, 6-WFM charting"
   exit 1
fi

for i in $GROUP
do
 counter=`echo ${i} | tr '[:lower:]' '[:upper:]'`
 if [ ${dateopt} -eq 0 ]
 then
  STARTDT=`head -350 $INDIR/mpv/${counter}.csv | tail -1 | awk -F , '{print $2}'`
 fi
 if [ ${OPT} -eq 5 ]
 then
  ENDDT=`head -400 $INDIR/mpv/${counter}.csv | tail -1 | awk -F , '{print $2}'`
  echo "End date is $ENDDT"
 fi
 if ! [ $OPT -eq 3 ]
 then
  echo Profiling $counter, $STARTDT, $STEPS
  #if [ $OPT -eq 1 ]
  #then
  # genmpv $counter
  #fi
  ./scripts/newprofiling.sh $counter "${STARTDT}:${ENDDT}:${STEPS}" $OPT $CHARTDAYS $TMPDIR $INDIR
 fi
 if ! [ $OPT -eq 1 -o $OPT -eq 5 ]
 then
  echo Daily Charting $counter, $STARTDT
  ./scripts/charting.sh $counter ${STARTDT}:${ENDDT} $OPT $TMPDIR $INDIR
 fi
done
