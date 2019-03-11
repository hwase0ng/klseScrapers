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
tmpmpv=$tmpdir/mpv
sigdir=${mpvdir}/signals
syndir=${mpvdir}/synopsis
prfdir=${mpvdir}/profiling

if [ $opt -eq 1 -o $opt -eq 5 ]
then
 params="-psj 1"
elif [ $opt -eq 2 ]
then
 params="-p -Dp -S"
elif [ $opt -eq 6 ]
then
 params="-Ds -psw"
else
 params="-Dp -S"
fi
if ! test -d ${prfdir}/$counter
then
 mkdir -p ${prfdir}/$counter
fi
logfile=${prfdir}/$counter/$counter.log
> $logfile
if [ $opt -eq 2 -o $opt -eq 6 ]
then
 cp ${sigdir}/$counter-signals.csv.2 ${sigdir}/$counter-signals.csv.3
 cp ${sigdir}/$counter-signals.csv ${sigdir}/$counter-signals.csv.2
 > ${sigdir}/$counter-signals.csv
 rm ${prfdir}/$counter/*.png | tee -a $logfile
 rm ${syndir}/${counter}-*.png | tee -a $logfile
 rm ${tmpmpv}/signals/${counter}-signals.csv.* | tee -a $logfile
 rm ${tmpmpv}/signals/${counter}-signals.csv | tee -a $logfile
elif [ $opt -eq 4 ]
then
 cp ${sigdir}/$counter-signals.csv.2 ${sigdir}/$counter-signals.csv.3
 cp ${sigdir}/$counter-signals.csv ${sigdir}/$counter-signals.csv.2
 > ${sigdir}/$counter-signals.csv
fi

if [ $opt -eq 1 -o $opt -eq 5 ]
then
	python analytics/mvpchart.py $counter $params -S $dates -c $chartdays -e ${indir} | tee -a $logfile
else
	if [ $opt -eq 6 ]
	then
		python analytics/mvpchart.py $counter $params -S $dates -c $chartdays -e ${indir} | tee -a $logfile
	else
		python analytics/mvpsignals.py $counter $params $dates -d ${indir} | tee -a $logfile
	fi
fi

if [ $opt -eq 1 -o $opt -eq 5 ]
then
 #cp $tmpdir/json/$counter.json $indir/json
 cd $tmpdir/json
 tar czvf $indir/json/${counter}.tgz ${counter}.2*.json
 cd -
else
 if [ $opt -eq 2 -o $opt -eq 6 ]
 then
  mv ${tmpmpv}/synopsis/${counter}.2*.png ${prfdir}/$counter/
 fi
 #cp ${tmpmpv}/signals/$counter-signals.csv ${sigdir}/
 #cat ${tmpmpv}/signals/${counter}-signals.csv.2* > ${sigdir}/${counter}-signals.csv
 #rm ${tmpmpv}/signals/${counter}-signals.csv.2*
fi
