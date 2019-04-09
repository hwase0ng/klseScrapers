counter=`echo ${1} | tr '[:lower:]' '[:upper:]'`
dates=$2
OPT=$3
nasdir=$4
indir=$5
chartdays=150
steps=`expr $chartdays - 10`

mpvdir=${indir}/mpv
prfdir=${mpvdir}/profiling

if [ $OPT -gt 1 ]
then
 opts="-om -c $chartdays"
else
 opts="-o -c $chartdays"
fi

python analytics/mvpchart.py $counter $opts -S $dates:$steps
mv ${mpvdir}/synopsis/${counter}_2*.png ${prfdir}/$counter/