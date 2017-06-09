#!/bin/bash
mkdir -p reports

python --version > reports/${1}_speed_report_lr.txt 2>&1
python test_speed_lr.py >> reports/${1}_speed_report_lr.txt

python --version > reports/${1}_speed_report_glr.txt 2>&1
python test_speed_glr.py >> reports/${1}_speed_report_glr.txt
