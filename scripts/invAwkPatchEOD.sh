COUNTER=$1
SCODE=$2
awk -F "," '{printf("%s,%s,%.4f,%.4f,%.4f,%.4f,%ld\n",$1,$2,$3,$4,$5,$6,$7)}' ../../data/investingcom/${COUNTER}.${SCODE}.csv > /z/data/${COUNTER}.${SCODE}.csvtmp
