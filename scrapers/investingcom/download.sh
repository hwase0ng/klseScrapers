COUNTER=$1
SCODE=$2
export PYTHONPATH=../..
python scrapeInvestingCom.py -s 2010-01-02 $1
awk -F "," '{printf("%s,%s,%.4f,%.4f,%.4f,%.4f,%ld\n",$1,$2,$3,$4,$5,$6,$7)}' ../../data/investingcom/${COUNTER}.${SCODE}.csv > /z/data/${COUNTER}.${SCODE}.csvtmp
