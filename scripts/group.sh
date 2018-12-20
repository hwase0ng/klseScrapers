#!/bin/bash
OPTIND=1

HOLDINGS="ASTINO BOILERM DANCO DUFU GKENT LAYHONG NOTION ORNA"
WATCHLIST="AEMULUS BONIA ECS HAIO HENGYUAN KGB LAYHONG MBSB MKH MMODE PADINI PETRONM SAMCHEM SCGM GCB"
MOMENTUM="BCMALL CHINWEL DANCO FLBHD KOBAY ORIENT YSPSAH"
DIVIDEND="FPI LCTITAN MAGNI UCHITEC KMLOONG MPI DUFU TONGHER CSCSTEL LIHEN TGUAN CHOOBEE GADANG OKA POHUAT PECCA SURIA"
GENISTA="APEX BURSA CBIP CIMB HIBISCS IOICORP IOIPG IVORY KPS PCHEM PRESBHD RSENA"
CONSUMER="BONIA PADINI HAIO ZHULIAN"
FURNITURE="FLBHD HEVEA"
PRECISION="DUFU KOBAY NOTION"
PAYMT="GHLSYS MPAY REVENUE"
PLASTIC="SCGM TGUAN TOMYPAK BOXPAK"
SEMICON="KESM VITROX INARI MPI UNISEM AEMULUS"
GLOVE="TOPGLOV HARTA KOSSAN SUPERMX COMFORT"
PAPER="MUDA ORNA"
SNIPER="UCREST YONGTAI NGGB LIONIND ANNJOO KESM"
GRANDPINE="KAWAN KESM YSPSAH"
TRIPLEFALLC="SCGM VSTECS"
MVP="KLSE DUFU N2N PADINI PETRONM KESM YSPSAH SCGM VSTECS GHLSYS MAGNI"

DATADIR=/z/data
TEST=$MVP
ENDDT=`date +%Y-%m-%d`
OPT=1
STEPS=5
re='^[0-9]+$'
dateopt=0

#usage() { echo "Usage: group.sh -cds [counter(s)] [start date] [steps]" 1>&2; exit 1 }

while getopts ":c:d:o:s:D:S:" opt
do
 case "$opt" in
  c)
   TEST=$OPTARG
   ;;
  D)
   DATADIR=$OPTARG
   if ! [ -d $DATADIR ]
   then
    echo $DATADIR is not a directory!
    exit 2
   fi
   ;;
  d)
   STARTDT=$OPTARG
   dateopt=1
   ;;
  o)
   OPT=$OPTARG
   ;;
  s)
   STEPS=$OPTARG
   if ! [[ "$STEPS" =~ $re ]]
   then
    echo "$STEPS is not an integer number!"
    exit 2
   fi
   ;;
  S)
   SET=$OPTARG
   #echo $(eval echo "\$$SET")
   TEST=$(eval echo "\$$SET")
   ;;
  *)
   #usage
   echo "Usage: group.sh -cdoDsS [counter(s)] [date] [opt=1234] [Dir] [steps] [Set]" 1>&2
   echo "  opt: 1 - Normal scanning, 2 - Signal scanning, 3 - Pattern scanning, 4 - Daily Charting only" 1>&2
   exit 1
   ;;
 esac
done
shift $((OPTIND-1))
[ "${1:-}" = "--" ] && shift
#echo "c=$TEST, D=$DATADIR, d=$STARTDT, e=$ENDDT, s=$STEPS, leftovers: $@"

for i in $TEST
do
 if [ ${dateopt} -eq 0 ]
 then
  STARTDT=`head -100 $DATADIR/mpv/${i}.csv | tail -1 | awk -F , '{print $2}'`
 fi
 if ! [ $OPT -eq 4 ]
 then
  echo Profiling $i, $STARTDT
  ./scripts/newprofiling.sh $i "${STARTDT}:${ENDDT}:${STEPS}" $OPT $DATADIR
 fi
 echo Daily Charting $i, $STARTDT
 ./scripts/charting.sh $i ${STARTDT}:${ENDDT} $DATADIR
done
