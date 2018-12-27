counter=`echo ${1} | tr '[:lower:]' '[:upper:]'`
dates=$2
OPT=$3
datadir=$4

simdir=${datadir}/mpv/simulation
prfdir=${simdir}/profiling
patdir=${simdir}/patterns

if [ $OPT -eq 3 -o $OPT -eq 4 ]
then
 opts="-om -c 200"
else
 opts="-o -c 200"
fi

python analytics/mvpchart.py $counter $opts -S $dates:190

if [ $OPT -eq 3 -o $OPT -eq 4 ]
then
 mv ${simdir}/synopsis/$counter_*.png ${patdir}/$counter/
else
 mv ${simdir}/synopsis/$counter_*.png ${prfdir}/$counter/
fi