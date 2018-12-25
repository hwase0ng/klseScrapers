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
sigdir=${simdir}/signals
syndir=${simdir}/synopsis
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
 > $logfile
 logfile=${prfdir}/$counter/$counter.log
 rm ${prfdir}/$counter/*.png | tee -a $logfile
else
 params="-ps -D p -C"
 if ! test -d ${patdir}/$counter
 then
  mkdir ${patdir}/$counter
 fi
 logfile=${patdir}/$counter/$counter.log
 > $logfile
 rm ${patdir}/$counter/*.png | tee -a $logfile
fi
> $logfile
> ${simdir}/signals/$counter-signals.csv
rm ${syndir}/${counter}-*.png | tee -a $logfile
rm ${sigdir}/${counter}-signals.csv.* | tee -a $logfile
rm ${sigdir}/${counter}-signals.csv | tee -a $logfile

python analytics/mvpchart.py $counter $params -S $dates -c $chartdays -e ${datadir} | tee -a $logfile

if [ $opt -lt 3 ]
then
 mv ${simdir}/synopsis/$counter-*.png ${prfdir}/$counter/
else
 mv ${simdir}/synopsis/$counter-*.png ${patdir}/$counter/
fi
#cp ${simdir}/signals/$counter-signals.csv ${datadir}/mpv/signals/
uniq ${simdir}/signals/$counter-signals.csv > ${datadir}/mpv/signals/${counter}-signals.csv