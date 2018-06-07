#!/usr/bin/env python3

# The MIT License (MIT)
#
# Copyright (c) 2018, Sam Bayless
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
# NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT
# OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
Run monosat regression tests on a specified command, with a given timeout
"""
import argparse
import multiprocessing
import csv
import shlex
import signal
import subprocess
import sys
import time
import os
import traceback

usg_string = __doc__[1:].replace("%s", "%%s").replace("regtest.py", """%(prog)s""")
parser = argparse.ArgumentParser(usage=usg_string, formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument("-t", "--timeout", type=int, help="Time limit in seconds.", default=5)

parser.add_argument(
    "-p", "--parallel", type=int, help="Number of parallel jobs to run (default: -1=#cores)", default=-1
)
parser.add_argument("--expected", type=str, help="Expected results to compare to", default="expected.csv")
parser.add_argument("command", nargs=argparse.REMAINDER)
# args, unknown_args = parser.parse_known_args()
args = parser.parse_args()

# command = " ".join(unknown_args)
command = " ".join(args.command)
if len(command) == 0:
    print("Usage: %s [-t TIMEOUT] [-p PARALLEL] [monosat_command]" % (sys.argv[0]))
    sys.exit(1)


processes = args.parallel
if processes < 0:
    processes = multiprocessing.cpu_count()
if processes == 0:
    processes = 1


root = "tests/"
row_count = 0

timeout = args.timeout

print("Time limit: %d, Parallel: %d" % (timeout, processes))
print("Command: " + command)


class BadResultException(Exception):
    pass


def init(queue, counterv, num_badv, num_satv, num_unsatv, num_crashv, num_timeoutv, num_memoutv):
    global idx, counter, num_bad, num_sat, num_unsat, num_crash, num_timeout, num_memout
    idx = queue.get()
    counter = counterv
    num_bad = num_badv
    num_sat = num_satv
    num_unsat = num_unsatv
    num_crash = num_crashv
    num_timeout = num_timeoutv
    num_memout = num_memoutv


def compare(args):
    signal.signal(signal.SIGINT, signal.default_int_handler)
    try:
        global printed_icmp
        rownum, row = args
        # skip this row
        if len(row) == 0 or row[0].strip().startswith("#"):
            return

        with counter.get_lock():
            counter.value += 1
            n = counter.value

        instance = root + row[0]
        # the file was removed
        if not os.path.isfile(instance):
            return
        expected = int(row[1]) if len(row) > 1 else None

        full_command = command + " " + instance
        with counter.get_lock():
            print("%d/%d: %s" % (counter.value, row_count, full_command))
        start = time.time()
        result = None
        timedout = False
        memdout = False
        try:
            process = subprocess.run(
                shlex.split(full_command),
                # shell=True, # shell=true seems to break the timeout option
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=timeout if timeout > 0 else None,
                start_new_session=True,
            )
            result = process.returncode
        except subprocess.TimeoutExpired:
            # process timed out
            timedout = True

        elapsed = time.time() - start

        if timedout:
            with num_timeout.get_lock():
                num_timeout.value += 1
        elif memdout:
            with num_memout.get_lock():
                num_memout.value += 1
        elif result == 10:
            with num_sat.get_lock():
                num_sat.value += 1
        elif result == 20:
            with num_unsat.get_lock():
                num_unsat.value += 1
        else:
            with num_crash.get_lock():
                num_crash.value += 1
            if result != expected:
                with counter.get_lock():
                    print("Unexpected exit code on %s: Expected %d, Found %d" % (instance, expected, result))  # new
                    # line
                    try:
                        sys.stdout.write(process.stdout.decode("utf-8"))
                        sys.stdout.flush()
                    except:
                        pass  # ignore

                    try:
                        sys.stderr.flush()
                        sys.stderr.write(process.stderr.decode("utf-8"))
                        sys.stderr.flush()

                    except:
                        pass  # ignore

        if (expected == 10 and result == 20) or (expected == 20 and result == 10):
            # critical error
            with num_bad.get_lock():
                num_bad.value += 1

            with counter.get_lock():
                print("")  # new line
                try:
                    sys.stdout.write(process.stdout.decode("utf-8"))
                    sys.stdout.flush()
                except:
                    pass  # ignore

                try:
                    sys.stderr.flush()
                    sys.stderr.write(process.stderr.decode("utf-8"))
                    sys.stderr.flush()

                except:
                    pass  # ignore

                print(
                    "\nBad result on %s: found %d, expected %d.\nFull Command: %s"
                    % (instance, result, expected, full_command)
                )
                raise BadResultException()
                # sys.exit(1)
        else:
            with counter.get_lock():
                # should really aquire locks on all the values below
                print(
                    "Runs {}={}+{} SAT+UNSAT + Crashes {} = BAD {} + TO {}+ MO {} + Unknown {}), in {:3.2f} s".format(
                        counter.value,
                        num_sat.value,
                        num_unsat.value,
                        num_crash.value,
                        num_bad.value,
                        num_timeout.value,
                        num_memout.value,
                        num_crash.value - (num_bad.value - num_timeout.value + num_memout.value),
                        elapsed,
                    ),
                    end="\n",
                )

    except KeyboardInterrupt:

        raise
        # sys.exit(1)


start = time.time()

with open(args.expected) as expectedfile:
    reader = csv.reader(expectedfile)
    rows = [row for row in reader if len(row) > 0 and not row[0].strip().startswith("#")]
    row_count = len(rows)

    manager = multiprocessing.Manager()
    counter = multiprocessing.Value("i", 0)
    num_bad = multiprocessing.Value("i", 0)
    num_crash = multiprocessing.Value("i", 0)
    num_sat = multiprocessing.Value("i", 0)
    num_unsat = multiprocessing.Value("i", 0)
    num_timeout = multiprocessing.Value("i", 0)
    num_memout = multiprocessing.Value("i", 0)
    idQueue = manager.Queue()
    for i in range(processes):
        idQueue.put(i)
    pool = multiprocessing.Pool(
        processes, init, (idQueue, counter, num_bad, num_sat, num_unsat, num_crash, num_timeout, num_memout)
    )
    signal.signal(signal.SIGINT, signal.default_int_handler)
    try:
        pool.map(compare, enumerate(rows))
        elapsed = time.time() - start
        print(
            "Finished. Runs {}={}+{} SAT+UNSAT, crashes {} = BAD {} + TO {}+ MO {} + Unknown {}), in {:3.2f} s".format(
                counter.value,
                num_sat.value,
                num_unsat.value,
                num_crash.value,
                num_bad.value,
                num_timeout.value,
                num_memout.value,
                num_crash.value - (num_bad.value - num_timeout.value + num_memout.value),
                elapsed,
            )
        )
    except KeyboardInterrupt as e:
        elapsed = time.time() - start
        print(
            "Aborting. Runs {}={}+{} SAT+UNSAT, crashes {} = BAD {} + TO {}+ MO {} + Unknown {}), in {:3.2f} s".format(
                counter.value,
                num_sat.value,
                num_unsat.value,
                num_crash.value,
                num_bad.value,
                num_timeout.value,
                num_memout.value,
                num_crash.value - (num_bad.value - num_timeout.value + num_memout.value),
                elapsed,
            )
        )
        for p in multiprocessing.active_children():
            p.terminate()
        sys.exit(1)
    except BadResultException as e:
        elapsed = time.time() - start
        print(
            "Bad Result. Runs {}={}+{} SAT+UNSAT, crashes {} = BAD {} + TO {}+ MO {} + Unknown {}), in {:3.2f} "
            "s".format(
                counter.value,
                num_sat.value,
                num_unsat.value,
                num_crash.value,
                num_bad.value,
                num_timeout.value,
                num_memout.value,
                num_crash.value - (num_bad.value - num_timeout.value + num_memout.value),
                elapsed,
            )
        )
        for p in multiprocessing.active_children():
            p.terminate()
        sys.exit(1)
