#!/bin/bash
# pip install pyprof2calltree

rm glr.pstats
python -m cProfile -o cpu.pstats -s time test_cpu.py
pyprof2calltree -k -i cpu.pstats
