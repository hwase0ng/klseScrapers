'''
Usage: main [options] [COUNTER] ...

Arguments:
    COUNTER           Optional counters
Options:
    -c,--check            Check processing mode

Created on Mar 7, 2020

@author: hwase
'''
from common import formStocklist, loadCfg
from docopt import docopt
import settings as S
import yaml

I3_INSIDER_DIRECTOR_URL = 'https://klse.i3investor.com/servlets/stk/annchdr/'
I3_INSIDER_SHAREHOLDER_URL = 'https://klse.i3investor.com/servlets/stk/annchsh/'


def process():
    stream = open("insider.yaml", 'r')
    docs = yaml.load_all(stream, Loader=yaml.FullLoader)
    for doc in docs:
        for name, items in doc.items():
            # print (name + " : " + str(items))
            email = items["email"]
            if S.DBG_ALL or S.DBG_INSIDER:
                print (name + ": " + email)
            for trackinglist in items.iterkeys():
                if trackinglist == "email":
                    continue
                if S.DBG_ALL or S.DBG_INSIDER:
                    print ("  " + trackinglist + " : ")
                for counter in items[trackinglist]:
                    counter = counter.upper()
                    slist = formStocklist(counter, klse)
                    dirUrl = I3_INSIDER_DIRECTOR_URL + slist[counter] + ".jsp"
                    shdUrl = I3_INSIDER_SHAREHOLDER_URL + slist[counter] + ".jsp"
                    if S.DBG_ALL or S.DBG_INSIDER:
                        print ("\t" + counter + " " + slist[counter] + " " + dirUrl)
                print


if __name__ == '__main__':
    args = docopt(__doc__)
    cfg = loadCfg(S.DATA_DIR)

    global klse
    klse = "scrapers/i3investor/klse.txt"

    process()
