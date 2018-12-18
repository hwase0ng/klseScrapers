COUNTER=$1
SCODE=$2
INDATA=/c/git/klseScrapers/data
OUTDATA=/z/data
awk -F "," '{printf("%s,%s,%.4f,%.4f,%.4f,%.4f,%ld\n",$1,$2,$3,$4,$5,$6,$7)}' ${INDATA}/investingcom/${COUNTER}.${SCODE}.csv > ${OUTDATA}/${COUNTER}.${SCODE}.csvtmp
