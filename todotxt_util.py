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


TODO:
    * reorganize re
    * status_date nie jest parsowane - zmienić?

"""

import shutil
import os
import sys
import argparse
import re
import locale
import time
import datetime

from dateutil.relativedelta import relativedelta

_MATCH_CONTEXT_RE = re.compile(r'(@\S+)', re.L)
_MATCH_PROJECT_RE = re.compile(r'\s(\+\S+)', re.L)
_MATCH_PRIORITY_RE = re.compile(r'\(([A-Za-z])\)', re.L)
_MATCH_DUE_RE = re.compile(r' due:(\d\d\d\d-\d\d-\d\d)')
_MATCH_TDUE_RE = re.compile(r' t:(\d\d\d\d-\d\d-\d\d)')
_MATCH_R_RE = re.compile(r' rec:(\+?\d+)([dmywq]?)', re.I)
_MATCH_STATUS_RE = re.compile(r'^(x)( (\d\d\d\d-\d\d-\d\d))? ', re.I)


def _today():
    ttd = time.localtime(time.time())
    return time.mktime((ttd.tm_year, ttd.tm_mon, ttd.tm_mday, 0, 0, 0, 0, 0,
                        ttd.tm_isdst))

NOW = _today()

_DEFAULT_SORT_MODE = 'sdtPpcT'
_DEFAULT_FPATH = "~/Todo/todo.txt"


def load_task(line):
    """Parse one line and return tasks"""
    task = {'content': line,
            'over_due': 0,
            'over_t': 0,
            'project': "",
            'context': "",
            'priority': "\xff",
            'status': 'a',
            'status_date': None,
            'recurse': None,
            'due': None,
            'tdue': None,
            'text': None}
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
            task['over_due'] = date - NOW - 86400
        except ValueError:
            pass
    tdue = _MATCH_TDUE_RE.search(line)
    if tdue:
        try:
            date = time.mktime(time.strptime(tdue.group(1), "%Y-%m-%d"))
            task['tdue'] = date
            task['over_t'] = date - NOW
        except ValueError:
            pass
    status = _MATCH_STATUS_RE.search(line)
    if status:
        task['status'] = status.group(1).lower()
        if len(status.groups()) == 3:
            task['status_date'] = status.group(3)
            task['text'] = line[11:]
        else:
            task['text'] = line[3:]
    else:
        task['text'] = line
    rec = _MATCH_R_RE.search(line)
    if rec:
        task['recurse'] = (rec.group(1), rec.group(2))
    return task


def load_tasks(lines):
    """load tasks from lines."""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        line = line.replace("  ", " ")
        task = load_task(line)
        yield task


def load_tasks_from_file(args):
    """load content of todo.txt."""

    filename = os.path.expanduser(args.file)

    if args.verbose:
        print("loading " + filename, file=sys.stderr)

    if not os.path.isfile(filename):
        print("file {} not found".format(filename), file=sys.stderr)
        exit(-2)

    with open(filename) as finp:
        yield from load_tasks(finp)


def print_tasks(tasks, args, header):
    """Print tasks on std"""
    if args.verbose:
        header = '----------- ' + header + ' -----------'
        print(header)
    for task in tasks:
        print(task['content'])
    if args.verbose:
        print('-' * len(header))


def write_tasks(tasks, args):
    """write task into file or stdout."""
    if args.stdout:
        print_tasks(tasks, args, "TASKS")
        return

    filename = args.file

    if args.verbose:
        print("writing {} file".format(filename), file=sys.stderr)

    # create backup
    if os.path.isfile(filename):
        shutil.copyfile(filename, filename + ".bak")
    with open(filename, "w") as ofile:
        for task in tasks:
            ofile.write(task['content'])
            ofile.write("\r\n")


def write_archive(tasks, args):
    """Append task to archive file or print to stdout."""
    if args.stdout:
        print_tasks(tasks, args, "ARCHIVE")
        return

    if args.verbose:
        print("writing done task", file=sys.stderr)

    basefilename = args.file
    arch_fpath = os.path.join(
        os.path.dirname(basefilename), "done.txt")

    # create backup
    if os.path.isfile(arch_fpath):
        shutil.copyfile(arch_fpath, arch_fpath + ".bak")

    with open(arch_fpath, "a") as ofile:
        for task in tasks:
            ofile.write(task['content'])
            ofile.write("\r\n")


def archive_tasks(tasks, _args):
    """Move done tasks to archive"""
    tasks = list(tasks)
    done = (task for task in tasks if task['status'] == 'x')
    active = (task for task in tasks if task['status'] != 'x')
    return active, done


def _move_date(indate, offset):
    if indate and offset:
        data = datetime.date.fromtimestamp(indate)
        data += offset
        return time.mktime(data.timetuple())
    return indate


def _replace_date(content, prefix, old_date, new_date):
    if not old_date or not new_date:
        return content
    replstr = prefix + time.strftime("%Y-%m-%d", time.localtime(old_date))
    deststr = prefix + time.strftime("%Y-%m-%d", time.localtime(new_date))
    return content.replace(replstr, deststr)


def recurse_tasks(tasks, args):
    """create new task from finished tasks with 'rec' tag """
    for task in tasks:
        yield task
        rec = task['recurse']
        if task['status'] != 'x' or not rec:
            continue
        oval = 0
        try:
            oval = int(rec[0])
        except ValueError as err:
            print("error {}".format(err), file=sys.stderr)
            continue
        offset = None
        if rec[1] == 'm':
            offset = relativedelta(months=oval)
        elif rec[1] == 'w':
            offset = relativedelta(weeks=oval)
        elif rec[1] == 'y':
            offset = relativedelta(years=oval)
        elif rec[1] == 'q':
            offset = relativedelta(months=oval * 3)
        elif rec[1] == 'd':
            offset = relativedelta(days=oval)
        else:
            print("error: unknown rec step: {}", rec, file=sys.stderr)
            continue

        if args.verbose:
            print("recurse task '{}'".format(task['content']),
                  file=sys.stderr)

        ntask = task.copy()
        content = ntask['content'][2:]
        if task['status_date']:
            content = content[11:]
        ntask['status'] = 'a'
        tdue = ntask['tdue'] = _move_date(task['tdue'], offset)
        ntask['over_t'] = (tdue - NOW) if tdue else None
        content = _replace_date(content, ' t:', task['tdue'], ntask['tdue'])
        due = ntask['due'] = _move_date(task['due'], offset)
        ntask['over_due'] = (due - NOW - 86400) if due else None
        content = _replace_date(content, ' due:', task['due'], ntask['due'])
        ntask['content'] = content
        yield ntask


_SORT_KEYS_SK = {
    'p': 'project',
    'd': 'over_due',
    't': 'over_t',
    'P': 'priority',
    'c': 'context',
    's': 'status',
    'T': 'text',
}


def sort_tasks(tasks, args):
    """Sort tasks by mode."""
    mode = args.mode or _DEFAULT_SORT_MODE
    s_keys = [_SORT_KEYS_SK[char] for char in mode if char in _SORT_KEYS_SK]
    if not s_keys:
        print("invalid sort mode: '{}'".format(args.mode), file=sys.stderr)
        exit(-1)

    def key_fn(task):
        return [task.get(key, '') for key in s_keys]

    tasks = sorted(tasks, key=key_fn)
    return tasks


def parse_args():
    parser = argparse.ArgumentParser(description='Todo.txt utility')
    parser.add_argument("-f", "--file",
                        default=os.path.expanduser(_DEFAULT_FPATH),
                        help="todo.txt filename")
    parser.add_argument("--stdout", action="store_true",
                        default=False,
                        help="print result on stdout")
    parser.add_argument("-v", "--verbose", action="store_true")
    subparsers = parser.add_subparsers(help='Commands', dest='command')

    parser_sort = subparsers.add_parser('sort', help='sorting functions')
    parser_sort.add_argument(
        '-m', '--mode', default=_DEFAULT_SORT_MODE,
        help='sorting mode, default: by status, due, t, project, '
        'Priority, context')
    parser_sort.add_argument(
        '--archive', action="store_true",
        help='archive done tasks')
    parser_sort.add_argument(
        '--recurse', action="store_true",
        help='create new task according to recurse tags')

    parser_arch = subparsers.add_parser('archive', help='archive done tasks')
    parser_arch.add_argument(
        '--recurse', action="store_true",
        help='create new task according to recurse tags')

    parser_clean = subparsers.add_parser('clean',
                                         help='sort, archive and recurse tasks')
    parser_clean.add_argument(
        '-m', '--mode', default=_DEFAULT_SORT_MODE,
        help='sorting mode, default: by status, due, t, project, '
        'Priority, context')

    return parser.parse_args()


def main():
    """main function."""
    locale.setlocale(locale.LC_ALL, locale.getdefaultlocale())

    args = parse_args()

    if not args.command:
        print("missing command", file=sys.stderr)
        exit(-1)

    tasks = load_tasks_from_file(args)
    archive = None

    if args.command == 'sort':
        if args.recurse:
            tasks = recurse_tasks(tasks, args)
        tasks = sort_tasks(tasks, args)
        if args.archive:
            tasks, archive = archive_tasks(tasks, args)
    elif args.command == 'archive':
        if args.recurse:
            tasks = recurse_tasks(tasks, args)
        tasks, archive = archive_tasks(tasks, args)
    elif args.command == 'clean':
        tasks = recurse_tasks(tasks, args)
        tasks, archive = archive_tasks(tasks, args)
        tasks = sort_tasks(tasks, args)

    write_tasks(tasks, args)
    if archive is not None:
        write_archive(archive, args)

    if args.verbose:
        print("done", file=sys.stderr)


if __name__ == "__main__":
    main()
