#!/usr/bin/env python3

"""
Generate expected results for each GNF in the current directory; append those results to 'existing.csv'
Files will be tested in natural alphanumeric order, with files containing 'reduced' executed first.
Only files without entries in 'existing.csv' will be tested.
"""
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


expected = "expected.csv"

cmd = " ".join(sys.argv[1:])

root = "tests/"

if len(cmd) == 0:
    print("Usage: %s [monosat_command]" % (sys.argv[0]))
    sys.exit(1)

existing = set()
with open(expected) as expectedfile:
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
with open(expected, "a") as expectedfile:
    writer = csv.writer(expectedfile, quoting=csv.QUOTE_MINIMAL)
    for fileset in (reduced_files, original_files, remaining_files_reduced, remaining_files):
        for file in fileset:
            n += 1
            if file not in existing:
                full_command = cmd + " " + root + file
                print("%d/%d: %s" % (n, total, full_command), file=sys.stderr)
                start = time.time()
                expected = subprocess.run(full_command, shell=True, stdout=sys.stderr, check=False).returncode

                elapsed = time.time() - start
                # round this up to seconds
                if expected == 10 or expected == 20:
                    writer.writerow([os.path.basename(file), str(expected)])  # , int(math.ceil(elapsed))
                    sys.stdout.flush()
                else:
                    print("Exit code %d when running %s" % (expected, full_command), file=sys.stderr)
                    continue
