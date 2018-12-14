counter=$1
dates=$2
opts="-ps"

if ! test -d /z/data/mpv/simulation/profiling/$counter
then
 mkdir /z/data/mpv/simulation/profiling/$counter
fi

rm /z/data/mpv/simulation/profiling/$counter/*.png > /z/data/mpv/simulation/profiling/$counter/$counter.log 2>&1
rm /z/data/mpv/simulation/signals/${counter}-signals.csv > /z/data/mpv/simulation/profiling/$counter/$counter.log 2>&1
rm /z/data/mpv/simulation/synopsis/${counter}-*.png > /z/data/mpv/simulation/profiling/$counter/$counter.log 2>&1

python analytics/mvpchart.py $counter $opts -S $dates | tee -a /z/data/mpv/simulation/profiling/$counter/$counter.log
mv /z/data/mpv/simulation/synopsis/$counter-*.png /z/data/mpv/simulation/profiling/$counter/
cp /z/data/mpv/simulation/signals/$counter-signals.csv /z/data/mpv/signals/
