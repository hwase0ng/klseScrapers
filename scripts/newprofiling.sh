counter=`echo ${1} | tr '[:lower:]' '[:upper:]'`
dates=$2
opt=$3
chartdays=$4
if [ -z $chartdays ]
then
 chartdays=600
fi
tmpdir=$5
if [ -z $tmpdir ]
then
 tmpdir=/z/data
fi
indir=$6
mpvdir=$indir/mpv

sigdir=${mpvdir}/signals
syndir=${mpvdir}/synopsis
prfdir=${mpvdir}/profiling
patdir=${mpvdir}/patterns

if [ $opt -lt 3 ]
then
 if [ $opt -eq 1 ]
 then
  params="-psj 1 -C"
 else
  params="-ps -D s -C"
 fi
 if ! test -d ${prfdir}/$counter
 then
  mkdir -p ${prfdir}/$counter
 fi
 logfile=${prfdir}/$counter/$counter.log
 > $logfile
 if ! [ $opt -eq 1 ]
 then
  rm ${prfdir}/$counter/*.png | tee -a $logfile
 fi
else
 params="-psj2 -Dp -C"
 if ! test -d ${patdir}/$counter
 then
  mkdir -p ${patdir}/$counter
 fi
 logfile=${patdir}/$counter/$counter.log
 > $logfile
 rm ${patdir}/$counter/*.png | tee -a $logfile
fi
if ! [ $opt -eq 1 ]
then
 > ${sigdir}/$counter-signals.csv
 rm ${syndir}/${counter}-*.png | tee -a $logfile
 rm ${tmpdir}/mpv/signals/${counter}-signals.csv.* | tee -a $logfile
 rm ${tmpdir}/mpv/signals/${counter}-signals.csv | tee -a $logfile
fi

python analytics/mvpchart.py $counter $params -S $dates -c $chartdays -e ${indir} | tee -a $logfile

if [ $opt -eq 1 ]
then
 #cp $tmpdir/json/$counter.json $indir/json
 tar czvf $indir/json/$counter.tgz $tmpdir/json/$counter.*.json
else
 if [ $opt -lt 3 ]
 then
  mv ${tmpdir}/mpv/synopsis/$counter-*.png ${prfdir}/$counter/
 else
  mv ${tmpdir}/mpv/synopsis/$counter-*.png ${patdir}/$counter/
 fi
 #cp ${tmpdir}/mpv/signals/$counter-signals.csv ${sigdir}/
 uniq ${tmpdir}/mpv/signals/$counter-signals.csv > ${sigdir}/${counter}-signals.csv
fi