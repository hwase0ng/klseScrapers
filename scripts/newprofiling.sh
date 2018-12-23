counter=$1
dates=$2
opt=$3
chartdays=$4
if [ -z $chartdays ]
then
 chartdays=600
fi
datadir=$5
if [ -z $datadir ]
then
 datadir=/z/data
fi

simdir=${datadir}/mpv/simulation
prfdir=${simdir}/profiling
patdir=${simdir}/patterns

if [ $opt -lt 3 ]
then
 if [ $opt -eq 1 ]
 then
  params="-ps -C"
 else
  params="-ps -D s -C"
 fi
 if ! test -d ${prfdir}/$counter
 then
  mkdir ${prfdir}/$counter
 fi
 rm ${prfdir}/$counter/*.png > ${prfdir}/$counter/$counter.log 2>&1
 rm ${prfdir}/${counter}-signals.csv > ${prfdir}/$counter/$counter.log 2>&1
 rm ${prfdir}/${counter}-*.png > ${prfdir}/$counter/$counter.log 2>&1
 
 logfile=${prfdir}/$counter/$counter.log
else
 params="-ps -D p -C"
 if ! test -d ${patdir}/$counter
 then
  mkdir ${patdir}/$counter
 fi
 rm ${patdir}/$counter/*.png > ${patdir}/$counter/$counter.log 2>&1
 rm ${patdir}/${counter}-signals.csv > ${patdir}/$counter/$counter.log 2>&1
 rm ${patdir}/${counter}-*.png > ${patdir}/$counter/$counter.log 2>&1
 
 logfile=${patdir}/$counter/$counter.log
fi

python analytics/mvpchart.py $counter $params -S $dates -c $chartdays -e ${datadir} | tee -a $logfile

if [ $opt -lt 3 ]
then
 mv ${simdir}/synopsis/$counter-*.png ${patdir}/$counter/
else
 mv ${simdir}/synopsis/$counter-*.png ${prfdir}/$counter/
fi
cp ${simdir}/signals/$counter-signals.csv ${datadir}/mpv/signals/