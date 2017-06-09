#!/bin/bash
# pip install pyprof2calltree

rm lr.pstats
python -m cProfile -o lr.pstats -s time test_speed_lr.py
pyprof2calltree -k -i lr.pstats

