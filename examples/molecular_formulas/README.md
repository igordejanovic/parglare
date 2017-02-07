This example is based
on
[article by Andrew Dalke](http://www.dalkescientific.com/writings/diary/archive/2007/11/03/antlr_java.html) comparing
ANTLR and PLY performance in parsing molecular formulas.

An example is modified to compare PLY and parglare. You can see the difference
in styles of grammar/actions definition and parser construction.

At the time of this writing `parglare/PLY` ratio on my machine is around 1.7
which is very good considering that `parglare` is a very young project and there
is a room for performance improvements.
