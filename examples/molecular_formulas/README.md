This example is based
on
[article by Andrew Dalke](http://www.dalkescientific.com/writings/diary/archive/2007/11/03/antlr_java.html) comparing
ANTLR and PLY performance in parsing molecular formulas.

An example is modified to compare PLY and parglare. You can see the difference
in styles of grammar/actions definition and parser construction.

By running `python run_test.py` you will see the speed difference. PLY is faster
in this tests.
