#!/usr/bin/env python3
# ====================================================================
# Copyright 2018 by Martin Rünz <contact@martinruenz.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
# ====================================================================

import argparse
import os
import re
import sys
from shutil import copyfile

parser = argparse.ArgumentParser(description='''A tool to replace placeholder files with the preceding valid file.''')
parser.add_argument('-i', required=True, help='Path to start file.')
parser.add_argument('-s', required=False, help='Proceed silently, without confirmation prompt.', action='store_true')
parser.add_argument('-l', required=False, help='Create symbolic links instead of copies.', action='store_true')
args = parser.parse_args()

index_re = re.compile('(\d+)(?!.*\d)')  # Gets last number in a string


def get_index(path):
    m = index_re.search(path)
    if m is None:
        raise RuntimeError("Index could not be found.")
    return m.group(0)


def increment_path(path):
    index = get_index(path)
    return index_re.sub(str(int(index)+1).zfill(len(index)), path)


replacements = []
current_path = args.i
last_valid_file = None

if not os.path.isfile(current_path):
    print("ERROR. Could not find input file:", current_path, file=sys.stderr)
    exit(1)


while os.path.isfile(current_path):
    if os.path.getsize(current_path) == 0:
        if last_valid_file is None:
            print("WARNING can not replace file:", current_path,
                  "\n as no valid preceding file was found.", file=sys.stderr)
        else:
            replacements.append((current_path, last_valid_file))
    else:
        last_valid_file = current_path
    current_path = increment_path(current_path)

if len(replacements) > 0:
    while not args.s:
        response = input("{} files are going to be replaced.\n"
                         "Press 'p' to proceed, 'l' to list files, or 'c' to cancel:\n".format(len(replacements)))
        if response == "l":
            for r in replacements:
                print("Replace:", r[0], "with", r[1])
        else:
            break
else:
    print("0 replacements found. Nothing to do.")
    exit(0)

if args.s or response == 'p':
    print("Removing placeholder...", end=' ')
    for r in replacements:
        os.remove(r[0])
    print("done.")
    if args.l:
        print("Creating symlinks...", end=' ')
        for r in replacements:
            os.symlink(r[1], r[0])
    else:
        print("Copying files...", end=' ')
        for r in replacements:
            copyfile(r[1], r[0])
    print("done.")
else:
    print("Cancelled.")
