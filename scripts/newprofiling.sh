counter=$1
dates=$2
opt=$3

if [ $opt -eq 1 ]
then
 params="-ps -c 400"
else
 params="-ps -c 400 -D p"
fi

DATA=/z/data

if ! test -d ${DATA}/mpv/simulation/profiling/$counter
then
 mkdir ${DATA}/mpv/simulation/profiling/$counter
fi

rm ${DATA}/mpv/simulation/profiling/$counter/*.png > ${DATA}/mpv/simulation/profiling/$counter/$counter.log 2>&1
rm ${DATA}/mpv/simulation/signals/${counter}-signals.csv > ${DATA}/mpv/simulation/profiling/$counter/$counter.log 2>&1
rm ${DATA}/mpv/simulation/synopsis/${counter}-*.png > ${DATA}/mpv/simulation/profiling/$counter/$counter.log 2>&1

python analytics/mvpchart.py $counter $params -S $dates | tee -a ${DATA}/mpv/simulation/profiling/$counter/$counter.log
mv ${DATA}/mpv/simulation/synopsis/$counter-*.png ${DATA}/mpv/simulation/profiling/$counter/
cp ${DATA}/mpv/simulation/signals/$counter-signals.csv ${DATA}/mpv/signals/
