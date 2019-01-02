if [ $# -lt 1 ]
then
 echo "download.sh counter [date to download from]"
 echo "Resume from last rec if no date is provided"
 exit 1
fi
COUNTER=`echo $1 | tr '[:lower:]' '[:upper:]'`
DATE=$2
SRC=/c/git/klseScrapers
INDATA=/z/data
cd $INDATA
SCODE=`ls $COUNTER.*.csv | awk -F. '{print $2}'`
OUTDATA=$SRC/data
CSVFILE=${OUTDATA}/investingcom/$COUNTER.$SCODE.csv
cd $SRC
export PYTHONPATH=../..
cd $SRC/scrapers/investingcom
if ! test -s $CSVFILE || ! test -z "$3"
then
 if [ -z "$DATE" ]
 then
  DATE="2010-01-03"
 fi
 > $CSVFILE 
 echo Start downloading $COUNTER from $DATE
 python scrapeInvestingCom.py -s $DATE $1
else
 echo Resuming $COUNTER file
 python scrapeInvestingCom.py -r $1
fi
cd $SRC
echo
tail -3 $CSVFILE
