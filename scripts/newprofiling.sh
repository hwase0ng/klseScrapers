counter=$1
dates=$2
opt=$3
chartdays=$4
if [ -z $chartdays ]
then
 chartdays=500
fi
datadir=$5
if [ -z $datadir ]
then
 datadir=/z/data
fi

if [ $opt -eq 1 ]
then
 params="-ps -C"
else
 if [ $opt -eq 2 ]
 then
  params="-ps -D s -C"
 else
  params="-ps -D p -C"
 fi
fi

if ! test -d ${datadir}/mpv/simulation/profiling/$counter
then
 mkdir ${datadir}/mpv/simulation/profiling/$counter
fi

rm ${datadir}/mpv/simulation/profiling/$counter/*.png > ${datadir}/mpv/simulation/profiling/$counter/$counter.log 2>&1
rm ${datadir}/mpv/simulation/signals/${counter}-signals.csv > ${datadir}/mpv/simulation/profiling/$counter/$counter.log 2>&1
rm ${datadir}/mpv/simulation/synopsis/${counter}-*.png > ${datadir}/mpv/simulation/profiling/$counter/$counter.log 2>&1

python analytics/mvpchart.py $counter $params -S $dates -c $chartdays -e ${datadir} | tee -a ${datadir}/mpv/simulation/profiling/$counter/$counter.log

mv ${datadir}/mpv/simulation/synopsis/$counter-*.png ${datadir}/mpv/simulation/profiling/$counter/
cp ${datadir}/mpv/simulation/signals/$counter-signals.csv ${datadir}/mpv/signals/
