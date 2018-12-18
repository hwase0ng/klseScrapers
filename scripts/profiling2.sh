counter=$1
dates=$2
opts="-ps"
opts2="-D s"
DATA=/z/data

if ! test -d $DATA/mpv/simulation/profiling/$counter
then
 mkdir ${DATA}/mpv/simulation/profiling/$counter
fi
python analytics/mvpchart.py $counter $opts -S $dates
