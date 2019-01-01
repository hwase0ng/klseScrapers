counter=$1
cat /d/temp/$counter.csv | grep -v null | awk -F, -v sname=$counter '{printf("%s,%s,%.2f,%.2f,%.2f,%.2f,%s\n",sname,$1,$2,$3,$4,$6,$7)}' > /d/temp/$counter.csvtmp