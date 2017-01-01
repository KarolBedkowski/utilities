#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Generate / check md5sum.txt.

Optionally add sums only for new/updated files.
"""

from __future__ import with_statement
from __future__ import print_function

__author__ = 'Karol Będkowski'
__copyright__ = 'Copyright (c) Karol Będkowski, 2008-2017'
__revision__ = '2014-12-23'
__licence__ = "GPLv2"
__version__ = "0.2"

import os
import sys
import io
import hashlib
from optparse import OptionParser


MD5SUMFILENAME = 'md5sum.txt'
BSIZE = 8192*1024
COLOR_OK = '\033[92m'
COLOR_WARNING = '\033[93m'
COLOR_FAIL = '\033[91m'
COLOR_END = '\033[0m'


def get_file_sum(filename):
    md5 = hashlib.md5()
    total, last_perc = 0, -5
    size = os.path.getsize(filename)
    print(filename, '       ', end="")
    with io.open(filename, 'rb') as file2check:
        while True:
            data = file2check.read(BSIZE)
            if not data:
                break
            total += len(data)
            perc = int(100 * total / size)
            if perc > last_perc:
                print('\b\b\b\b%3d%%' % perc, end="")
                last_perc = perc
            sys.stdout.flush()
            md5.update(data)
    digest = md5.hexdigest().lower()
    filepath = filename.replace('\\', '/')
    print ('\b\b\b\b\b      \r', end="")
    return filepath, digest


def write_md5sum(filename, sums):
    with open(filename, 'wb') as md5sumfile:
        for fname, fsum in sorted(sums.iteritems()):
            line = '%s  %s\n' % (fsum, fname)
            md5sumfile.write(line)


def generate_sums(filename, update):
    print('Generate md5sum ->', filename)
    sums = {}
    missing = None
    if update:
        sums = dict(load_md5(filename))
        missing = [fname for fname in sums.iterkeys()
                   if not os.path.isfile(fname)]
    for root, _dirs, files in sorted(os.walk('.')):
        for fname in sorted(files):
            if root == '.' and fname == 'md5sum.txt':
                continue
            fpath = os.path.join(root, fname)
            if not os.path.isfile(fpath):
                continue
            filepath, digest = get_file_sum(fpath)
            current_sum = sums.get(filepath)
            status = (" " if current_sum == digest else "*") \
                     if current_sum else '+'
            print(status, digest, filepath)
            sums[filepath] = digest
    if missing:
        print(COLOR_WARNING, "Missing", COLOR_END, sep="")
        for fname in missing:
            print('-', sums[fname], fname, sep=" ")
    write_md5sum(filename, sums)
    exit(0)


def load_md5(filename):
    with open(filename) as md5sumfile:
        for line in md5sumfile:
            if line.startswith('#') or len(line.strip()) == 0:
                continue
            md5sum, filename = line.split(' ', 1)
            if filename and filename[0] == '*':
                filename = filename[1:]
            yield filename.strip(), md5sum.lower()


def check_sums(filename):
    print('Check md5sum <-', filename)
    md5s = list(load_md5(filename))
    files_count = len(md5s)
    if files_count == 0:
        exit(0)
    good_files_count = 0
    bad_files_count = 0
    bad_files_names = []
    for filename, md5sum in md5s:
        print('[%3d/%3d' % (good_files_count + bad_files_count + 1,
                            files_count),
              'g:%3d' % good_files_count,
              'b:%3d] ' % bad_files_count, end="")
        if os.path.exists(filename):
            digest = 0
            try:
                digest = get_file_sum(filename)[1]
            except IOError, err:
                print("Error", filename, err, file=sys.stderr)
            if digest != md5sum:
                bad_files_count += 1
                bad_files_names.append((filename, 'bad checksum'))
                print(COLOR_FAIL, '\n  bad checksum !!!!\n', COLOR_END, sep="")
            else:
                good_files_count += 1
                print()
        else:
            bad_files_count += 1
            bad_files_names.append((filename, 'not found'))
            print('not found !!!!!!\n')
    show_errors(files_count, good_files_count, bad_files_names)
    exit(1 if bad_files_count else 0)


def quick_check_sums(filename):
    print('Quick check md5sum <-', filename)
    md5s = [fsum[0] for fsum in load_md5(filename)]
    files_count = len(md5s)
    if files_count == 0:
        exit(0)
    good_files_count = 0
    bad_files_count = 0
    bad_files_names = []
    for filename in md5s:
        print('[%3d/%3d' % (good_files_count + bad_files_count + 1,
                            files_count),
              'g:%3d' % good_files_count,
              'b:%3d] ' % bad_files_count, end="")
        if os.path.exists(filename):
            good_files_count += 1
            print(filename)
        else:
            bad_files_count += 1
            bad_files_names.append((filename, 'not found'))
            print(filename, ' not found')
    show_errors(files_count, good_files_count, bad_files_names)
    exit(1 if bad_files_count else 0)


def show_errors(files_cnt, good_cnt, bad_filenames):
    if bad_filenames:
        print('\n\n', COLOR_FAIL, 'Errors:', COLOR_END, sep="")
        for errors in bad_filenames:
            print('%-60s %s' % errors)
    print('\nFiles:', files_cnt,
          COLOR_OK, '\tgood:', good_cnt,
          COLOR_WARNING, '\tbad:', len(bad_filenames),
          COLOR_END)
    if bad_filenames:
        print("\n\n", COLOR_FAIL, "ERRORS!!!!!!!!!!!!", COLOR_END)


def main():
    parser = OptionParser(usage="%prog [options] [md5sum.txt]",
                          version="%prog " + __version__,
                          description=__doc__)

    parser.add_option("-c", "--check", action="store_true", dest='check',
                      default=False,
                      help="check md5sums")
    parser.add_option("-u", "--update", action="store_true", dest='update',
                      default=False,
                      help="update md5sums, add new files")
    parser.add_option("-q", "--quick", action="store_true", dest='quick',
                      default=False,
                      help="only check files presence")

    (options, args) = parser.parse_args()
    filename = args[0] if len(args) >= 1 else MD5SUMFILENAME
    if options.quick:
        quick_check_sums(filename)
    elif options.check:
        check_sums(filename)
    elif options.update:
        if not os.path.isfile(filename):
            print("File", filename, "not exists! Can't update",
                  file=sys.stderr)
            exit(-1)
        generate_sums(filename, True)
    else:
        if os.path.isfile(filename):
            raw_input('File exists! Continue (CTRL+C to break)?')
        generate_sums(filename, options.update)


if __name__ == "__main__":
    main()
