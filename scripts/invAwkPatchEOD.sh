COUNTER=`echo $1 | tr '[:lower:]' '[:upper:]'`
SRCDIR=/c/git/klseScrapers
INDATA=$SRCDIR/data
OUTDATA=/z/data
cd $OUTDATA
SCODE=`ls $COUNTER.*.csv | awk -F. '{print $2}'`
cd $SRCDIR
awk -F "," '{printf("%s,%s,%.4f,%.4f,%.4f,%.4f,%ld\n",$1,$2,$3,$4,$5,$6,$7)}' ${INDATA}/investingcom/${COUNTER}.${SCODE}.csv > ${OUTDATA}/${COUNTER}.${SCODE}.csvtmp
