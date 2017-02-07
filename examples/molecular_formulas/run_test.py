"""Run tests to validate the MW parsers and compare timing results."""
# compare_mw.py

import parglare_mw
import ply_mw

# time.clock is more accurate under Windows
import time
import sys
if sys.platform == "win32":
    timer = time.clock
else:
    timer = time.time

_mw_table = {
    'H': 1.00794,
    'C': 12.001,
    'Cl': 35.453,
    'O': 15.999,
    'S': 32.06,
}

_element_names = list(_mw_table.keys())


def _generate_random_formulas():
    import random
    # Using semi-random values so I can check a wide space
    # Number of terms in the formula
    _possible_lengths = (1, 2, 3, 4, 5, 10, 53, 104)
    # Repeat count for each formula
    _possible_counts = tuple(range(12)) + (88, 91, 106, 107, 200, 1234)
    for i in range(2500):
        terms = []
        total_mw = 0.0
        # Use a variety of lengths
        for j in range(random.choice(_possible_lengths)):
            symbol = random.choice(_element_names)
            terms.append(symbol)
            count = random.choice(_possible_counts)
            if count == 1 and random.randint(0, 2) == 1:
                pass
            else:
                terms.append(str(count))

            total_mw += _mw_table[symbol] * count
        yield total_mw, "".join(terms)


_selected_formulas = [
    (0.0, ""),
    (1.00794, "H"),
    (1.00794, "H1"),
    (32.06, "S"),
    (12.001+1.00794*4, "CH4"),
    ]

good_test_data = (_selected_formulas +
                  list(_generate_random_formulas()))


def do_tests(calculate_mw):
    start_time = timer()
    for expected_mw, formula in good_test_data:
        got_mw = calculate_mw(formula)
        if expected_mw != got_mw:
            raise AssertionError("%r expected %r got %r" %
                                 (formula, expected_mw, got_mw))
    return timer() - start_time


print("Testing", len(good_test_data), "formulas")

# Evaluate everything with parglare
parglare_time = do_tests(parglare_mw.calculate_mw)
print("parglare", parglare_time)

# Evaluate everything with PLY
ply_time = do_tests(ply_mw.calculate_mw)
print("PLY", ply_time)

print("ratio = %.02f" % (parglare_time / ply_time))

# I really should test that they handle invalid formulas ...
