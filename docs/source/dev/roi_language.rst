*************
ROI formulas language
*************

Syntax
-----------------

ROI expression syntax is similar to Python, it has math and logial expressions, it can refer prediction, actual and feature values, it can call some builtin functions and constants.

| All expressions are evaluated per one row of data (prediction, actual and corresponding feature values).
| Filter expression drop all rows that don't match. Filter is optional.
| Investment expression is calculated for each row of data then it's aggregated by days.
| Same for revenue expression.
| Then ROI is calculated as a ``(revenue - investment) / investment``

Examples:

| filter: ``P >= 0.20``
| investment: ``$100``
| revenue: ``(1 + A) * $100``

or

| filter: ``P = True``
| investment: ``$loan_amount``
| revenue: ``if(A = True, $loan_amount * ((1 + $interest_percent / 100) ** $period_years), $0)``

Expressions can be nested with parentheses, the operators precedence `same as in Python <https://docs.python.org/3/reference/expressions.html#operator-precedence>`_

Tuples
-----------------
Tuples can be defined as a several values inside a parentheses separated by comma

``(1, "one")``
``(1 + 2, "something", f(1, 2))``

If expression
-----------------

ROI syntax has one flow control expression

``if(P > 0.2, $1050, $0)``

in this case if prediction value is greater than 0.2 if expression returns 1050, else 0

Top expression
-----------------

This expression allows to filter rows by some aggregates

``top 2 by P per $symbol`` - group all rows by ``$symbol`` and return top 2 by ``P`` rows per each group.

``top 10 by P from (bottom 5 by $spread per $symbol)`` - first it finds 5 records with lowest ``$spread`` per each ``$symbol``, then it returns top 10 by ``P`` from these records

Full syntax:

``(((top | bottom) NUMBER by expression) | all) [with_expression] [per expression [having expression]] [where expression] [from (top_expression)]``

* ``top`` - sort in descending order
* ``bottom`` - sort in ascending order
* ``all`` - select all items
* ``NUMBER`` - number of values to select
* ``with_expression`` - allows to add additional fields to result e.g. ``all with agg_max(P) as max_p``
* ``by expression`` - define a value for sorting
* ``per expression`` (optional) - define a grouping
* ``having expression`` (optional) - define a filter to drop a group, if all rows do not match the expression then whole group is dropped
* ``where expression`` (optional) - define addition filter
* ``from (top_expression)`` (optional) - define nested top expression

Numbers
-----------------
* ``123`` integer numbers
* ``123.456`` float numbers
* ``-123.456`` numbers can be negative
* ``$50.99`` numbers can start with dollar sign to express money

String literals
-----------------
* ``"some value"``

Variables
-----------------

* ``P`` or ``prediction`` predicted value
* ``A`` or ``actual`` actual value
* ``$feature1`` value of feature with name ``feature1``, name should start with alphabetical char or underscore, name can contain digits

Builtin operators
-----------------

Math operators:
^^^^^^^

* ``+`` addition
* ``-`` subtraction and unary minus
* ``*`` multiplication
* ``/`` divison
* ``//`` floor division
* ``%`` modulus
* ``**`` exponentiation

Bitwise operators:
^^^^^^^

* ``|`` or
* ``&`` and
* ``^`` xor
* ``~`` unary not
* ``<<`` zero fill left shift
* ``>>`` signed right shift

Logical operators:
^^^^^^^

* ``or`` logical or
* ``and`` logical and
* ``not`` logical unary not

Comparison operators:
^^^^^^^

* ``==`` equal
* ``!=`` not equal
* ``>`` greater than
* ``>=`` greater than or equal to
* ``<`` less than
* ``<=`` less than or equal

Builtin constants
-----------------
* ``None`` - None value
* ``True`` - True value
* ``False`` - False value

Builtin functions
-----------------

abs(x : number) : number
^^^^^^^
Return the absolute value of a number

ceil(x : float) : integer
^^^^^^^
Return the ceiling of ``x``, the smallest integer greater than or equal to ``x``

cos(x : number) : float
^^^^^^^
Return the arc cosine of ``x``, in radians. The result is between ``0`` and ``pi``.

exp(x : number) : float
^^^^^^^
Return ``e`` raised to the power ``x``, where ``e = 2.718281…`` is the base of natural logarithms.

floor(x : floor) : float
^^^^^^^
Return the floor of ``x``, the largest integer less than or equal to ``x``.

if(<boolean predicate>, <true expression>, <false expression>)
^^^^^^^
Evaludate predicate, if it's True returns result of true expression else result of false expression

len(s : string) : integer
^^^^^^^
Return the length (the number of chars) of an string.

log(x : number, [base : number]) : float
^^^^^^^
| With one argument, return the natural logarithm of ``x`` (to base ``e``).
| With two arguments, return the logarithm of ``x`` to the given base, calculated as ``log(x)/log(base)``.

log10(x : number) : float
^^^^^^^
Return the base-10 logarithm of ``x``. This is usually more accurate than ``log(x, 10)``.

log2(x : number) : float
^^^^^^^
Return the base-2 logarithm of ``x``. This is usually more accurate than ``log(x, 2)``.

max(arg1 : number, arg2 : number, *args) : number
^^^^^^^
Return the largest of two or more arguments.

min(arg1 : number, arg2 : number, *args) : number
^^^^^^^
Return the smallest of two or more arguments.

randint(a : integer, b : integer) : integer
^^^^^^^
Return a random integer ``N`` such that ``a <= N <= b``.

random() : float
^^^^^^^
Return the next random floating point number in the range ``[0.0, 1.0)``.

round(number : float [, ndigits : integer]) : integer
^^^^^^^
Return ``number`` rounded to ``ndigits`` precision after the decimal point. If ``ndigits`` is omitted or is ``None``, it returns the nearest integer to its input.

sin(x : number) : number
^^^^^^^
Return the sine of ``x`` radians.

sqrt(x : number) : number
^^^^^^^
Return the square root of ``x``.

tan(x : number) : number
^^^^^^^
Return the tangent of ``x`` radians.

Builtin agg functions
-----------------

agg_max(expression) : number
^^^^^^^
Max value in the group

agg_min(expression) : number
^^^^^^^
Min value in the group
