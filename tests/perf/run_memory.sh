#!/bin/bash
mkdir -p reports

python --version > reports/${1}_memory_report_lr.txt 2>&1 
python test_memory_lr.py >> reports/${1}_memory_report_lr.txt

python --version > reports/${1}_memory_report_glr.txt 2>&1 
python test_memory_glr.py >> reports/${1}_memory_report_glr.txt
