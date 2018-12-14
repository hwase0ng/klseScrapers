counter=$1
dates=$2
opts="-ps -D p -c 400"
DATA=/z/data

if ! test -d ${DATA}/mpv/simulation/profiling/$counter
then
 mkdir ${DATA}/mpv/simulation/profiling/$counter
fi

rm ${DATA}/mpv/simulation/profiling/$counter/*.png > ${DATA}/mpv/simulation/profiling/$counter/$counter.log 2>&1
rm ${DATA}/mpv/simulation/signals/${counter}-signals.csv > ${DATA}/mpv/simulation/profiling/$counter/$counter.log 2>&1
rm ${DATA}/mpv/simulation/synopsis/${counter}-*.png > ${DATA}/mpv/simulation/profiling/$counter/$counter.log 2>&1

python analytics/mvpchart.py $counter $opts -S $dates | tee -a ${DATA}/mpv/simulation/profiling/$counter/$counter.log
mv ${DATA}/mpv/simulation/synopsis/$counter-*.png ${DATA}/mpv/simulation/profiling/$counter/
cp ${DATA}/mpv/simulation/signals/$counter-signals.csv ${DATA}/mpv/signals/
