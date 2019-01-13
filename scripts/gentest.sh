#!/bin/bash
src=/c/git/klseScrapers
grep -E 'eval|# 20' $src/analytics/mvpsignals.py | grep -v "=" | awk '{print $2, $3}'