downloadEOD() {
 cd $SRC/scrapers/investingcom
 if ! test -s $CSVFILE || ! test -z "$3"
 then
 if [ -z "$DATE" ]
 then
  DATE="2010-01-03"
 fi
 > $CSVFILE 
 echo Start downloading $COUNTER from $DATE
 python scrapeInvestingCom.py -s $DATE $COUNTER
 else
 echo Resuming $COUNTER file
 python scrapeInvestingCom.py -r $COUNTER
 fi
 cd $SRC
}

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
ddate=`head -1 $INDATA/$COUNTER.$SCODE.csv | awk -F, '{print $2}'`
dyear=`echo $ddate | awk -F"-" '{print $1}'`
if [ "$dyear" -le "2010" ]
then
 echo "$COUNTER is good"
else
 while True
 do
  downloadEOD
  ddate=`tail -1 $CSVFILE | awk -F, '{print $2}'`
  dyear=`echo $ddate | awk -F"-" '{print $1}'`
  if [ "$dyear" == "2019" ]
  then
   echo "$COUNTER completed download"
   invAwkPatchEOD.sh $COUNTER
   break
  else
   echo "$COUNTER resume download from $ddate"
  fi
 done
fi
