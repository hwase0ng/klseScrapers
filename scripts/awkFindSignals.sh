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
useEqual="0"

while getopts ":s:S:v:V:c:e:g:d:" opt
do
 case "$opt" in
  c)
   counter=$OPTARG
   group=`echo ${counter} | tr '[:lower:]' '[:upper:]'`
   ;;
  d)
   datadir=$OPTARG
   if ! [ -d $datadir ]
   then
    echo $datadir is not a directory!
    exit 4
   fi
   ;;
  e)
   useEqual="$OPTARG"
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
  V)
   val2=$OPTARG
   if ! [[ "$val2" =~ $re ]]
   then
    echo "$val2 is not an integer number!"
    exit 2
   fi
   ;;
  g)
   SET=`echo ${OPTARG} | tr '[:lower:]' '[:upper:]'`
   group=$(eval echo "\$$SET")
   if [ -z "$group" ]
   then
    echo "$SET not in groups!"
    exit 6
   fi
   ;;
  *)
   echo "Usage: awkFindSignals.sh -sSvVcegd <signal name> <value> [counter|group] [equal] [datadir]" 1>&2
   exit 1
   ;;
 esac
done
shift $((OPTIND-1))
[ "${1:-}" = "--" ] && shift

if [ -z "$signal" -o "$val" == "0" ]
then
   echo "Usage: awkFindSignals.sh -sSvVcegd <signal name> <value> [counter|group] [equal] [datadir]" 1>&2
   exit 1
fi

if [ -z "$group" ]
then
	if ! [ -z $@ ]
	then
        if [ -z "${signal2}" -o "${val2}" == "0" ]
        then
			if [[  "$useEqual" == "1" ]]
			then
				awk -F'[,.^]' -v sn=$signal -v val=$val '{if ($sn == val) {print $0}}' $@
			else
				awk -F'[,.^]' -v sn=$signal -v val=$val '{if ($sn > val) {print $0}}' $@
			fi
		else
            awk -F'[,.^]' -v sn=$signal -v sn2=${signal2} -v val=$val -v val2=$val2 '{if ($sn == val && $sn2 == val2) {print $0}}' $@
		fi
		exit 0
	else
		echo "Missing input"
		exit 1
	fi
fi

for counter in $group
do
	signalfile=${signaldir}/${counter}-signals.csv
    if [ -f $signalfile ]
    then
		if [ -z "${signal2}" -o "${val2}" == "0" ]
		then
			echo "Searching $counter: e=$useEqual, s=$signal, v=$val, file=$signalfile"
			if [[ "$useEqual" == "1" ]]
			then
				awk -F'[,.^]' -v sn=$signal -v val=$val '{if ($sn == val) {print $0}}' $signalfile
			else
				awk -F'[,.^]' -v sn=$signal -v val=$val '{if ($sn > val) {print $0}}' $signalfile
			fi
		else
			echo "Searching $counter: e=$useEqual, s=$signal, v=$val, s2=$signal2, v2=$val2, file=$signalfile"
			if [[  "$useEqual" == "1" ]]
			then
  				awk -F'[,.^]' -v sn=$signal -v sn2=${signal2} -v val=$val -v val2=$val2 '{if ($sn == val && $sn2 == val2) {print $0}}' $signalfile
  			else
  				awk -F'[,.^]' -v sn=$signal -v sn2=${signal2} -v val=$val -v val2=$val2 '{if ($sn > val && $sn2 > val2) {print $0}}' $signalfile
  			fi
		fi
    else
    	echo "$signalfile not found! Skipped $counter."
    fi
done