from speed_test import run_tests
from parglare import GLRParser

if __name__ == '__main__':
    run_tests(GLRParser, prefer_shifts=True)
