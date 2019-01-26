counter=`echo ${1} | tr '[:lower:]' '[:upper:]'`
dates=$2
OPT=$3
tmpdir=$4
indir=$5/mpv
chartdays=150
steps=`expr $chartdays - 10`

mpvdir=${tmpdir}/mpv
prfdir=${indir}/profiling

if [ $OPT -gt 1 ]
then
 opts="-om -c $chartdays"
else
 opts="-o -c $chartdays"
fi

python analytics/mvpchart.py $counter $opts -S $dates:$steps
mv ${mpvdir}/synopsis/${counter}_2*.png ${prfdir}/$counter/