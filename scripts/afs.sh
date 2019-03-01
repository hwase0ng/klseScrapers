#!/bin/bash
source /c/git/klseScrapers/scripts/groups.klse
datadir=/z/data
mpvdir=$datadir/mpv
signaldir=$mpvdir/signals
re='^[0-9]+$'

# Regular divergence                   Hidden divergence:
#   Bias,     Price,       Oscillator      Bias,     Price,       Oscillator
#   ----------------------------------    -----------------------------------
#   Bullish,  Lower Low,   Higher Low      Bullish,  Higher Low,  Lower Low
#   Bearish,  Higher High, Lower High      Bearish,  Lower High,  Higher High
#
#  i.e. PEAK divergence = Bearish, VALLEY divergence = BULLISH
#
#        Nx   N^   Nv
#  P^    1    2    3
#  Pv    4    5    6
#  Px    X    7    8

# p3u=1,2,3 p3d=,4,5,6, n3u=2,5,7, n3d=3,6,8
# 1,2,3(narrowC), 4(m10x3), 5(3tops), 6(3bottoms), 7(narrowM), 8(highC), 9(lowC)
# divC, divMP, n3uM, n3uP, pcnt, hlP/lhP, hlM/lhM = 0, 1, 2, 3, 4, 5, 6

ss=4
sss=5
ns=6
nss=7
ps=8
pss=9
c=14		# hltb = ['0', 'h', 't', 'l', 'b']
m=15
p=16
v=17
tripleM=18	# 9=3xM>10
tripleP=19
tripleV=20
narrowC=21
narrowM=22  # 5,6,7,8=5<m<10, 9=decreasing prange
narrowP=23	# 1,2=p<0, 3,4=prange<0.20, 9=decreasing prange
countP=24
tripleBottoms=25
tripleTops=26
mvalp=27   # 1 plistM[-1]<=5, 3 nlistM[-1]>=10
pvalp=28   # 1 plistP[-1]<=0, 3 nlistP[-1]> 0
vvalp=29
mvaln=30   # 1 plistM[-1]<=5, 3 nlistM[-1]>=10
pvaln=31   # 1 plistP[-1]<=0, 3 nlistP[-1]> 0
vvaln=32
#matrix=27
#cmpdiv=28   # 1,2,3,7=CP+CM,CP,CM in pdiv (PEAK bearish divergence); 4,5,6,8=same in ndiv (VALLEY bullish)

signalfile=""
val=0
val2=0
signal=""
signal2=""
ops="1"

while getopts ":s:v:o:d:" opt
do
 case "$opt" in
  d)
   datadir=$OPTARG
   if ! [ -d $datadir ]
   then
    echo $datadir is not a directory!
    exit 4
   fi
   ;;
  o)
   ops="$OPTARG"
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
    echo "$val is not an integer number!"
    exit 2
   else
    if [ "$signal" -eq 14 -o "$signal" -eq 27 ]
    then
     val=`echo "("$val`
    else
     if [ "$signal" -eq 26 -o "$signal" -eq 29 ]
     then
      val=`echo ${val}")"`
     fi
    fi
   fi
   ;;
  *)
   echo "Usage: awkFindSignals.sh -svod <signal name> <value> [counter|group] [equal] [datadir]" 1>&2
   exit 1
   ;;
 esac
done
shift $((OPTIND-1))
[ "${1:-}" = "--" ] && shift

if [ -z "$signal" -o "$val" == "0" ]
then
   echo "Usage: afs.sh -svod <signal name> <value> [counter|group] [equal] [datadir]" 1>&2
   exit 1
fi

while read line
do
    if [[  "$ops" == "1" ]]
    then
        awk -F'[,.^]' -v sn=$signal -v val=$val '{if ($sn > val) {print $0}}'
    else
        if [[  "$ops" == "2" ]]
        then
	        awk -F'[,.^]' -v sn=$signal -v val=$val '{if ($sn < val) {print $0}}'
        else
	        awk -F'[,.^]' -v sn=$signal -v val=$val '{if ($sn == val) {print $0}}'
	    fi
    fi
done < /dev/stdin