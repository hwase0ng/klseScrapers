counter=$1
dates=$2
opts="-po -c 150"
DATA=/z/data
python analytics/mvpchart.py $counter $opts -S $dates:130
mv ${DATA}/mpv/simulation/synopsis/$counter_*.png ${DATA}/mpv/simulation/profiling/$counter/
