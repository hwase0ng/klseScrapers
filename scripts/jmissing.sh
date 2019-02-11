if [ -z "$1" ]
then
	echo "Usage: jmissing.sh <counter>"
	exit 1
fi
counter=`echo $1 | tr '[:lower:]' '[:upper:]'`
echo $counter
sfile="/z/data/mpv/${counter}.csv"
for j in `tail -n +200 $sfile`
do
	ddate=`echo $j | awk -F, '{print $2}'`
	f="data/json/$counter.$ddate.json"
	if ! [ -e $f ]
	then
		echo $f
		python analytics/mvpchart.py $counter -psj 1 -S $ddate -c 500
	fi
done