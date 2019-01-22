counter=`echo ${1} | tr '[:lower:]' '[:upper:]'`
dates=$2
OPT=$3
tmpdir=$4
indir=$5/mpv

mpvdir=${tmpdir}/mpv
prfdir=${indir}/profiling
patdir=${indir}/patterns

if [ $OPT -eq 3 -o $OPT -eq 4 ]
then
 opts="-om -c 200"
else
 opts="-o -c 200"
fi

python analytics/mvpchart.py $counter $opts -S $dates:190

if [ $OPT -eq 3 -o $OPT -eq 4 ]
then
 mv ${mpvdir}/synopsis/${counter}_2*.png ${patdir}/$counter/
else
 mv ${mpvdir}/synopsis/${counter}_2*.png ${prfdir}/$counter/
fi