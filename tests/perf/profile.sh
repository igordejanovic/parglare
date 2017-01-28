#!/bin/bash
# Install gprof2dot: pip install gprof2dot

rm profile.pstats callgraph.pdf
python -m cProfile -o profile.pstats -s time test_speed.py
gprof2dot -f pstats profile.pstats | dot -Tpdf -o callgraph.pdf

