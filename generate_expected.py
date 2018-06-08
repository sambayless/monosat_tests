#!/usr/bin/env python3

"""
Generate expected results for each GNF in the current directory; append those results to 'existing.csv'
Files will be tested in natural alphanumeric order, with files containing 'reduced' executed first.
Only files without entries in 'existing.csv' will be tested.
"""
import argparse
import math
import shlex
import subprocess
import sys
import os
import csv
import time

import re

# from https://stackoverflow.com/a/16090640
def natural_sort_key(s, _nsre=re.compile("([0-9]+)")):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(_nsre, s)]


parser = argparse.ArgumentParser(usage="Generate expected results")

parser.add_argument("-t", "--timeout", type=int, help="Time limit in seconds.", default=5)
parser.add_argument("--expected", type=str, help="Expected results to compare to", default="expected.csv")

parser.add_argument("command", nargs=argparse.REMAINDER)

args = parser.parse_args()

command = " ".join(args.command)
if len(command) == 0:
    print("Usage: %s [-t TIMEOUT] [monosat_command]" % (sys.argv[0]))
    sys.exit(1)


expected_filename = args.expected

timeout = args.timeout
root = "tests/"

existing = set()
if not os.path.isfile(expected_filename):
    f = open(expected_filename, "w")
    f.write("# Instance, Expected Exit Code\n")
    f.close()

with open(expected_filename) as expectedfile:
    reader = csv.reader(expectedfile)
    rows = [row for row in reader if len(row) > 0 and not row[0].strip().startswith("#")]
    for row in rows:
        if len(row) >= 2:
            existing.add(row[0])

files = [f for f in os.listdir(root) if os.path.isfile(root + f) and f.endswith(".gnf")]

reduced_files = sorted([f for f in files if "reduced" in f and f.startswith("test_")], key=natural_sort_key)
original_files = sorted([f for f in files if "reduced" not in f and f.startswith("test_")], key=natural_sort_key)
remaining_files_reduced = sorted(
    [f for f in files if "reduced" in f and not f.startswith("test_")], key=natural_sort_key
)
remaining_files = sorted([f for f in files if "reduced" not in f and not f.startswith("test_")], key=natural_sort_key)
n = 0
total = len(reduced_files) + len(original_files) + len(remaining_files_reduced) + len(remaining_files)
with open(expected_filename, "a") as expectedfile:
    writer = csv.writer(expectedfile, quoting=csv.QUOTE_MINIMAL)
    for fileset in (reduced_files, original_files, remaining_files_reduced, remaining_files):
        for file in fileset:
            n += 1
            if file not in existing:
                full_command = command + " " + root + file
                print("%d/%d: %s" % (n, total, full_command), file=sys.stderr)
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
                    # don't record anything
                    print("Timed out when running %s" % (full_command), file=sys.stderr)
                else:
                    if result == 10 or result == 20 or result == 1:
                        writer.writerow([os.path.basename(file), str(result)])
                        expectedfile.flush()
                    else:
                        print("Exit code %d when running %s" % (result, full_command), file=sys.stderr)
                        continue
