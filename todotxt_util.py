#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 Todo.txt utility.
 Copyright (c) Karol Będkowski, 2016

 This is free software; you can redistribute it and/or modify it under the
 terms of the GNU General Public License as published by the Free Software
 Foundation; either version 2 of the License, or (at your option) any later
 version.

 This application is distributed in the hope that it will be useful, but
 WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
 or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
 for more details.

 You should have received a copy of the GNU General Public License along
 with this program; if not, write to the Free Software Foundation, Inc.,
 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""

import shutil
import os
import sys
import argparse
import re
import locale
import time

_MATCH_CONTEXT_RE = re.compile(r'(@\S+)', re.L)
_MATCH_PROJECT_RE = re.compile(r'(\+\S+)', re.L)
_MATCH_PRIORITY_RE = re.compile(r'\(([A-Za-z])\)', re.L)
_MATCH_DUE_RE = re.compile(r'due:(\d\d\d\d-\d\d-\d\d)')
_MATCH_TDUE_RE = re.compile(r't:(\d\d\d\d-\d\d-\d\d)')

_NOW = time.time()


def _load_task(line):
    """Parse one line and return tasks"""
    task = {'content': line,
            'over_due': 0,
            'over_t': 0,
            'project': "\xff",
            'context': "\xff",
            'priority': "\xff"}
    context = _MATCH_CONTEXT_RE.search(line)
    if context:
        task['context'] = context.group(1)
    project = _MATCH_PROJECT_RE.search(line)
    if project:
        task['project'] = project.group(1)
    priority = _MATCH_PRIORITY_RE.search(line)
    if priority:
        task['priority'] = priority.group(1)
    due = _MATCH_DUE_RE.search(line)
    if due:
        try:
            date = time.mktime(time.strptime(due.group(1), '%Y-%m-%d'))
            task['due'] = date
            task['over_due'] = date - _NOW
        except ValueError:
            pass
    tdue = _MATCH_TDUE_RE.search(line)
    if tdue:
        try:
            date = time.mktime(time.strptime(tdue.group(1), "%Y-%m-%d"))
            task['tdue'] = date
            task['over_t'] = date - _NOW
        except ValueError:
            pass
    return task


def load_tasks(filename):
    """load content of todo.txt."""

    if not os.path.isfile(filename):
        print("file {} not found".format(filename), file=sys.stderr)
        exit(-2)

    with open(filename) as finp:
        for line in finp:
            line = line.strip()
            if not line:
                continue
            task = _load_task(line)
            yield task


def print_tasks(tasks):
    """Print tasks on std"""
    for task in tasks:
        print(task['content'])


def write_tasks(tasks, filename):
    """write task into file."""
    # crate backup
    shutil.copyfile(filename, filename + ".bak")
    with open(filename, "w") as ofile:
        for task in tasks:
            ofile.write(task['content'])
            ofile.write("\r\n")


_SORT_KEYS_SK = {
    'p': 'project',
    'd': 'over_due',
    't': 'over_t',
    'P': 'priority',
    'c': 'context',
}


def sort_tasks(args):
    """Sort tasks by mode."""
    if args.verbose:
        print("loading {} file".format(args.file), file=sys.stderr)
    tasks = load_tasks(args.file)

    mode = args.mode or 'dtpPc'
    s_keys = [_SORT_KEYS_SK[char] for char in mode if char in _SORT_KEYS_SK]
    if not s_keys:
        print("invalid sort mode: '{}'".format(args.mode), file=sys.stderr)
        exit(-1)

    def key_fn(task):
        return [task.get(key, '') for key in s_keys]

    tasks = sorted(tasks, key=key_fn)
    if not tasks:
        return
    if args.stdout:
        print_tasks(tasks)
    else:
        if args.verbose:
            print("writing {} file".format(args.file), file=sys.stderr)
        write_tasks(tasks, args.file)
    if args.verbose:
        print("done", file=sys.stderr)


def parse_args():
    parser = argparse.ArgumentParser(description='Todo.txt utility')
    parser.add_argument("-f", "--file", default="todo.txt",
                        help="todo.txt filename")
    parser.add_argument("--stdout", action="store_true",
                        default=False,
                        help="print result on stdout")
    parser.add_argument("-v", "--verbose", action="store_true")
    subparsers = parser.add_subparsers(help='Commands',
                                       dest='command',)
    parser_sort = subparsers.add_parser('sort', help='sorting functions')
    parser_sort.add_argument(
        '-m', '--mode', default="dtpPc",
        help='sorting mode, default: by due, t, project, Priority, context')
    return parser.parse_args()


def main():
    """main function."""
    locale.setlocale(locale.LC_ALL, locale.getdefaultlocale())

    args = parse_args()

    if args.command == 'sort':
        sort_tasks(args)
    else:
        print("missing command", file=sys.stderr)

if __name__ == "__main__":
    main()
