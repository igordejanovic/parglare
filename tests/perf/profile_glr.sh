#!/bin/bash
# pip install pyprof2calltree

rm glr.pstats
python -m cProfile -o glr.pstats -s time test_speed_glr.py
pyprof2calltree -k -i glr.pstats
