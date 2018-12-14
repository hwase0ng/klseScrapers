counter=$1
dates=$2
opts="-ps"
opts2="-D s"

if ! test -d /z/data/mpv/simulation/profiling/$counter
then
 mkdir /z/data/mpv/simulation/profiling/$counter
fi
> /z/data/mpv/simulation/profiling/$counter/${counter}2.log 2>&1
python analytics/mvpchart.py $counter $opts $opts2 -S $dates | tee -a /z/data/mpv/simulation/profiling/$counter/${counter}2.log
