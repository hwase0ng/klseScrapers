counter=$1
dates=$2
opt=$3
datadir=$4

if [ $opt -eq 1 ]
then
 params="-ps -c 400 -C"
else
 if [ $opt -eq 2 ]
 then
  params="-ps -c 400 -D s -C"
 else
  params="-ps -c 400 -D p -C"
 fi
fi

if ! test -d ${datadir}/mpv/simulation/profiling/$counter
then
 mkdir ${datadir}/mpv/simulation/profiling/$counter
fi

rm ${datadir}/mpv/simulation/profiling/$counter/*.png > ${datadir}/mpv/simulation/profiling/$counter/$counter.log 2>&1
rm ${datadir}/mpv/simulation/signals/${counter}-signals.csv > ${datadir}/mpv/simulation/profiling/$counter/$counter.log 2>&1
rm ${datadir}/mpv/simulation/synopsis/${counter}-*.png > ${datadir}/mpv/simulation/profiling/$counter/$counter.log 2>&1

python analytics/mvpchart.py $counter $params -S $dates -e ${datadir} | tee -a ${datadir}/mpv/simulation/profiling/$counter/$counter.log

mv ${datadir}/mpv/simulation/synopsis/$counter-*.png ${datadir}/mpv/simulation/profiling/$counter/
cp ${datadir}/mpv/simulation/signals/$counter-signals.csv ${datadir}/mpv/signals/
