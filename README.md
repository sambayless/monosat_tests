# MonoSAT Tests
Test suite for the constraint solver [MonoSAT](https://github.com/sambayless/monosat).

## Contents: 
* tests/ contains a large set of test inputs in MonoSAT's GNF constraint format.
* regtest.py is an executable Python 3 script for running regression tests (requires python 3.4+)
* expected.csv lists, for many of the test caes, an expected exit code (10=SAT, 20=UNSAT, 1=Error)
* generate_expected.py is a Python 3 script that prodcues expected.csv

## Usage:
```
$ regtest.py [-t TIMEOUT] [-p PARALLEL] monosat [optional arguments for MonoSAT]
```

An example invocation, running with a 10 second timeout (applied to each individual test case), in 4 threads:
```
$ regtest.py -t 10 -p 4 ./monosat -decide-theories
Time limit: 10, Parallel: 4
Command: ./monosat/monosat -decide-theories
1/386: ./monosat/monosat -decide-theories tests/test_2_reduced.gnf
2/386: ./monosat/monosat -decide-theories tests/test_6_reduced_3.gnf
3/386: ./monosat/monosat -decide-theories tests/test_8_reduced_4.gnf
4/386: ./monosat/monosat -decide-theories tests/test_20_reduced_3.gnf
Runs 4=1+0 SAT+UNSAT + Crashes 0 = BAD 0 + TO 0+ MO 0 + 0), in 0.02 s
5/386: ./monosat/monosat -decide-theories tests/test_2_reduced_2.gnf
Runs 5=2+0 SAT+UNSAT + Crashes 0 = BAD 0 + TO 0+ MO 0 + 0), in 0.02 s
6/386: ./monosat/monosat -decide-theories tests/test_6_reduced_3b.gnf
Runs 6=2+1 SAT+UNSAT + Crashes 0 = BAD 0 + TO 0+ MO 0 + 0), in 0.02 s
7/386: ./monosat/monosat -decide-theories tests/test_20_reduced_4.gnf
...
137/386: ./monosat/monosat -decide-theories tests/test_60_reduced_cb.gnf
Runs 137=105+18 SAT+UNSAT + Crashes 0 = BAD 0 + TO 0+ MO 0 + 0), in 0.04 s
138/386: ./monosat/monosat -decide-theories tests/test_42_reduced.gnf
Runs 138=106+18 SAT+UNSAT + Crashes 0 = BAD 0 + TO 0+ MO 0 + 0), in 0.02 s
139/386: ./monosat/monosat -decide-theories tests/test_60_reduced_d.gnf
Runs 139=107+18 SAT+UNSAT + Crashes 0 = BAD 0 + TO 0+ MO 0 + 0), in 0.02 s
140/386: ./monosat/monosat -decide-theories tests/test_60_reduced_e.gnf
Runs 140=108+18 SAT+UNSAT + Crashes 0 = BAD 0 + TO 0+ MO 0 + 0), in 0.06 s
...
```

If no tests produce bad results (as compared to expected.csv), then regest.py will exit normally, else it will exit with code 1.



