#!/bin/bash
cd /c/git/klseScrapers
python analytics/mvpchart.py -psd -Ds -S $@
cd -