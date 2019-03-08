if [ -z "$1" ]
then
	echo "Usage: jresume.sh <counter>"
	exit 1
fi
cd $SRCDIR
counter=`echo $1 | tr '[:lower:]' '[:upper:]'`
sfile="/z/data/mpv/${counter}.csv"
sdate=`ls -l data/json/${counter}.201[89]*.json | tail -1 | awk '{print $NF}' | awk -F[/.] '{print $4}'`
if [ -z "$sdate" ]
then
    echo "Skipped empty $sfile"
    exit 1
fi
lnum=`grep -n ${sdate} ${sfile} | awk -F: '{print $1}'`
lcount=`wc -l ${sfile} | awk '{print $1}'`
if [ $lcount -lt 300 ]
then
    echo "Line count $lcount. Skipped $sfile"
    exit 1
fi
tnum=`expr $lnum - $lcount`
echo $counter, $sdate, $lcount, $lnum, $tnum
if [ $tnum -eq 0 ]
then
	echo "$counter is good!"
	exit 0
fi

for j in `tail -n $tnum $sfile`
do
	ddate=`echo $j | awk -F, '{print $2}'`
	f="data/json/$counter.$ddate.json"
	echo $f
	if ! [ -e $f ]
	then
		python analytics/mvpchart.py $counter -psj 1 -S $ddate -c 500
	fi
done
cd -
