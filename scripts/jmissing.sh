group="DANCO DUFU PADINI CARLSBG KESM KLSE F&N"
for counter in $group
do
 echo $counter
 sfile="/z/data/mpv/${counter}.csv"
 for j in `tail -n +200 $sfile`
 do
  ddate=`echo $j | awk -F, '{print $2}'`
  f="data/json/$counter.$ddate.json"
  echo $f
  if ! [ -e $f ]
  then
   python analytics/mvpchart.py $counter -psj 1 -S $ddate -c 500
  fi
  done
 done

