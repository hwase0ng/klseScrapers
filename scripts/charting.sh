counter=$1
dates=$2
OPT=$3
DATA=$4
if [ $OPT -eq 3 -o $OPT -eq 4 ]
then
 opts="-om -c 200"
else
 opts="-o -c 200"
fi
python analytics/mvpchart.py $counter $opts -S $dates:150
mv ${DATA}/mpv/simulation/synopsis/$counter_*.png ${DATA}/mpv/simulation/profiling/$counter/
