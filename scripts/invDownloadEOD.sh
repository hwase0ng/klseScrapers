if [ $# -lt 2 ]
then
 echo "download.sh counter stkcode [date to download from]"
 echo "Resume from last rec if no date is provided"
 exit 1
fi
COUNTER=$1
SCODE=$2
DATE=$3
CSVFILE=../../data/investingcom/$COUNTER.$SCODE.csv
export PYTHONPATH=../..
if ! test -s $CSVFILE || ! test -z "$3"
then
 if [ -z "$DATE" ]
 then
  DATE="2010-01-03"
 fi
 > $CSVFILE 
 echo Start downloading from $DATE
 python scrapeInvestingCom.py -s $DATE $1
else
 echo Resuming file
 python scrapeInvestingCom.py -r $1
fi
echo
tail -3 $CSVFILE