#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import time

import todotxt_util as tu


class TestParseTask(unittest.TestCase):
    def test_parse_full(self):
        # mock today
        tu.NOW = time.mktime((2016, 7, 12, 0, 0, 0, 0, 0, 1))

        data = "x 2016-07-12 (A) 2016-07-10 task test 1 +project @context " \
            "due:2016-07-13 t:2016-07-11 rec:+1m"
        parsed = tu.load_task(data)
        self.assertEqual(parsed['status'], 'x')
        self.assertEqual(parsed['content'], data)
        self.assertEqual(parsed['over_due'], 0)
        self.assertEqual(parsed['over_t'], -24 * 60 * 60)
        self.assertEqual(parsed['project'], '+project')
        self.assertEqual(parsed['context'], '@context')
        self.assertEqual(parsed['priority'], 'A')
        self.assertEqual(parsed['status_date'], '2016-07-12')
        self.assertEqual(parsed['recurse'], ('+1', 'm'))
        self.assertEqual(parsed['due'], time.mktime(
                (2016, 7, 13, 0, 0, 0, 0, 0, 1)))
        self.assertEqual(parsed['tdue'], time.mktime(
                (2016, 7, 11, 0, 0, 0, 0, 0, 1)))

    def test_parse_wo_status_date(self):
        # mock today
        tu.NOW = time.mktime((2016, 7, 12, 0, 0, 0, 0, 0, 1))

        data = "x (A) 2016-07-10 task test 1 +project @context " \
            "due:2016-07-13 t:2016-07-11 rec:+1m"
        parsed = tu.load_task(data)
        self.assertEqual(parsed['status'], 'x')
        self.assertEqual(parsed['content'], data)
        self.assertEqual(parsed['over_due'], 0)
        self.assertEqual(parsed['over_t'], -24 * 60 * 60)
        self.assertEqual(parsed['project'], '+project')
        self.assertEqual(parsed['context'], '@context')
        self.assertEqual(parsed['priority'], 'A')
        self.assertEqual(parsed['status_date'], None)
        self.assertEqual(parsed['recurse'], ('+1', 'm'))
        self.assertEqual(parsed['due'], time.mktime(
                (2016, 7, 13, 0, 0, 0, 0, 0, 1)))
        self.assertEqual(parsed['tdue'], time.mktime(
                (2016, 7, 11, 0, 0, 0, 0, 0, 1)))

    def test_parse_wo_prio(self):
        # mock today
        tu.NOW = time.mktime((2016, 7, 12, 0, 0, 0, 0, 0, 1))
        data = "X 2016-07-12 2016-07-10 task test 1 +project @context " \
            "due:2016-07-13 t:2016-07-11 rec:+1m"
        parsed = tu.load_task(data)
        self.assertEqual(parsed['status'], 'x')
        self.assertEqual(parsed['status_date'], '2016-07-12')
        self.assertEqual(parsed['content'], data)
        self.assertEqual(parsed['over_due'], 0)
        self.assertEqual(parsed['over_t'], -24 * 60 * 60)
        self.assertEqual(parsed['project'], '+project')
        self.assertEqual(parsed['context'], '@context')
        self.assertEqual(parsed['priority'], '\xff')
        self.assertEqual(parsed['recurse'], ('+1', 'm'))
        self.assertEqual(parsed['due'], time.mktime(
                (2016, 7, 13, 0, 0, 0, 0, 0, 1)))
        self.assertEqual(parsed['tdue'], time.mktime(
                (2016, 7, 11, 0, 0, 0, 0, 0, 1)))

    def test_parse_wo_status(self):
        # mock today
        tu.NOW = time.mktime((2016, 7, 12, 0, 0, 0, 0, 0, 1))
        data = "2016-07-10 task test 1 +project @context " \
            "due:2016-07-13 t:2016-07-11 rec:+1m"
        parsed = tu.load_task(data)
        self.assertEqual(parsed['status'], 'a')
        self.assertEqual(parsed['status_date'], None)
        self.assertEqual(parsed['content'], data)
        self.assertEqual(parsed['over_due'], 0)
        self.assertEqual(parsed['over_t'], -24 * 60 * 60)
        self.assertEqual(parsed['project'], '+project')
        self.assertEqual(parsed['context'], '@context')
        self.assertEqual(parsed['priority'], '\xff')
        self.assertEqual(parsed['recurse'], ('+1', 'm'))
        self.assertEqual(parsed['due'], time.mktime(
                (2016, 7, 13, 0, 0, 0, 0, 0, 1)))
        self.assertEqual(parsed['tdue'], time.mktime(
                (2016, 7, 11, 0, 0, 0, 0, 0, 1)))

    def test_parse_simple(self):
        # mock today
        tu.NOW = time.mktime((2016, 7, 12, 0, 0, 0, 0, 0, 1))
        data = "task test 2"
        parsed = tu.load_task(data)
        self.assertEqual(parsed['status'], 'a')
        self.assertEqual(parsed['status_date'], None)
        self.assertEqual(parsed['content'], data)
        self.assertEqual(parsed['over_due'], 0)
        self.assertEqual(parsed['over_t'], 0)
        self.assertEqual(parsed['project'], '\xff')
        self.assertEqual(parsed['context'], '\xff')
        self.assertEqual(parsed['priority'], '\xff')
        self.assertEqual(parsed['recurse'], None)
        self.assertEqual(parsed['due'], None)
        self.assertEqual(parsed['tdue'], None)

    def test_parse_rec(self):
        # mock today
        tu.NOW = time.mktime((2016, 7, 12, 0, 0, 0, 0, 0, 1))

        data = "task test 1 rec:+2w"
        parsed = tu.load_task(data)
        self.assertEqual(parsed['recurse'], ('+2', 'w'))

        data = "task test 1 rec:+2y"
        parsed = tu.load_task(data)
        self.assertEqual(parsed['recurse'], ('+2', 'y'))

        data = "task test 1 rec:+3m"
        parsed = tu.load_task(data)
        self.assertEqual(parsed['recurse'], ('+3', 'm'))

        data = "task test 1 rec:4d"
        parsed = tu.load_task(data)
        self.assertEqual(parsed['recurse'], ('4', 'd'))


_DATA1 = """2016-07-10 task test 1 +project @context due:2016-07-13 t:2016-07-11 rec:+1m
(A) task test 2 due:2017-01-01
x task 4
x 2016-06-01 (B) """


class TestParseTasks(unittest.TestCase):
    def test_parse(self):
        tasks = list(tu.load_tasks(_DATA1.split("\n")))
        self.assertEqual(len(tasks), 4)
        self.assertEqual(tasks[0]['project'], '+project')
        self.assertEqual(tasks[1]['due'], time.mktime(
                (2017,  1, 1, 0, 0, 0, 0, 0, 0)))
        self.assertEqual(tasks[2]['content'], 'x task 4')
        self.assertEqual(tasks[3]['status_date'], '2016-06-01')


class TestArchive(unittest.TestCase):
    def test_archive(self):
        tasks = list(tu.load_tasks(_DATA1.split("\n")))
        self.assertEqual(len(tasks), 4)
        active, done = tu.archive_tasks(tasks, None)
        active = list(active)
        done = list(done)
        self.assertEqual(len(active), 2)
        self.assertEqual(len(done), 2)
        self.assertEqual(active[0]['project'], '+project')
        self.assertEqual(active[1]['due'], time.mktime(
                (2017,  1, 1, 0, 0, 0, 0, 0, 0)))
        self.assertEqual(done[0]['content'], 'x task 4')
        self.assertEqual(done[1]['status_date'], '2016-06-01')


class _ArgsMock(object):
    def __init__(self):
        self.mode = None
        self.verbose = False


class TestSortTasks(unittest.TestCase):
    def test_sort1(self):
        data = """2016-07-10 task test 1 +project @context due:2016-07-13 t:2016-07-11 rec:+1m
x task 4
x 2016-06-01 (B)
(A) task test 2 due:2017-01-01"""
        tasks = tu.load_tasks(data.split("\n"))
        args = _ArgsMock()
        args.mode = 'sdtpPc'
        tasks = list(tu.sort_tasks(tasks, args))
        self.assertEqual(len(tasks), 4)
        self.assertEqual(tasks[0]['project'], '+project')
        self.assertEqual(tasks[1]['due'], time.mktime(
                (2017,  1, 1, 0, 0, 0, 0, 0, 0)))
        self.assertEqual(tasks[2]['status_date'], '2016-06-01')
        self.assertEqual(tasks[3]['content'], 'x task 4')

    def test_sort2(self):
        data = """2016-07-10 task test 1 +project @context due:2016-07-13 t:2016-07-11 rec:+1m
x task 4
x 2016-06-01 (B)
(A) task test 2 due:2017-01-01"""
        tasks = tu.load_tasks(data.split("\n"))
        args = _ArgsMock()
        args.mode = 'sPl'
        tasks = list(tu.sort_tasks(tasks, args))
        self.assertEqual(len(tasks), 4)
        self.assertEqual(tasks[0]['due'], time.mktime(
                (2017,  1, 1, 0, 0, 0, 0, 0, 0)))
        self.assertEqual(tasks[1]['project'], '+project')
        self.assertEqual(tasks[2]['status_date'], '2016-06-01')
        self.assertEqual(tasks[3]['content'], 'x task 4')


class TestRecurseTasks(unittest.TestCase):
    def test_recurse_no(self):
        data = "2016-07-10 task test 1 due:2016-07-13 t:2016-07-11 rec:+1m"
        task = tu.load_task(data)
        ntasks = list(tu.recurse_tasks([task], _ArgsMock()))
        self.assertEqual(len(ntasks), 1)
        self.assertEqual(ntasks[0]['content'], data)

    def test_recurse_wo_dates(self):
        tu.NOW = time.mktime((2016, 7, 12, 0, 0, 0, 0, 0, 1))
        data = "x 2016-07-12 2016-07-10 task test 1 rec:+1m"
        task = tu.load_task(data)
        ntasks = list(tu.recurse_tasks([task], _ArgsMock()))
        self.assertEqual(len(ntasks), 2)
        self.assertEqual(ntasks[0]['content'], data)
        self.assertEqual(ntasks[1]['content'],
                         "2016-07-10 task test 1 rec:+1m")

    def test_recurse_w_dates_m(self):
        tu.NOW = time.mktime((2016, 7, 12, 0, 0, 0, 0, 0, 1))
        data = "x 2016-07-10 2016-07-10 "\
            "task test 1 due:2016-07-13 t:2016-07-11 rec:+1m"
        task = tu.load_task(data)
        ntasks = list(tu.recurse_tasks([task], _ArgsMock()))
        self.assertEqual(len(ntasks), 2)
        self.assertEqual(ntasks[0]['content'], data)
        self.assertEqual(
            ntasks[1]['content'],
            "2016-07-10 task test 1 due:2016-08-13 t:2016-08-11 rec:+1m")

    def test_recurse_w_dates_w(self):
        tu.NOW = time.mktime((2016, 7, 12, 0, 0, 0, 0, 0, 1))
        data = "x 2016-07-10 2016-07-10 "\
            "task test 1 due:2016-07-13 t:2016-07-11 rec:+1w"
        task = tu.load_task(data)
        ntasks = list(tu.recurse_tasks([task], _ArgsMock()))
        self.assertEqual(len(ntasks), 2)
        self.assertEqual(ntasks[0]['content'], data)
        self.assertEqual(
            ntasks[1]['content'],
            "2016-07-10 task test 1 due:2016-07-20 t:2016-07-18 rec:+1w")

    def test_recurse_w_dates_d(self):
        tu.NOW = time.mktime((2016, 7, 12, 0, 0, 0, 0, 0, 1))
        data = "x 2016-07-10 2016-07-10 "\
            "task test 1 due:2016-07-13 t:2016-07-11 rec:+4d"
        task = tu.load_task(data)
        ntasks = list(tu.recurse_tasks([task], _ArgsMock()))
        self.assertEqual(len(ntasks), 2)
        self.assertEqual(ntasks[0]['content'], data)
        self.assertEqual(
            ntasks[1]['content'],
            "2016-07-10 task test 1 due:2016-07-17 t:2016-07-15 rec:+4d")

    def test_recurse_w_dates_y(self):
        tu.NOW = time.mktime((2016, 7, 12, 0, 0, 0, 0, 0, 1))
        data = "x 2016-07-10 2016-07-10 "\
            "task test 1 due:2016-07-13 t:2016-07-11 rec:+2y"
        task = tu.load_task(data)
        ntasks = list(tu.recurse_tasks([task], _ArgsMock()))
        self.assertEqual(len(ntasks), 2)
        self.assertEqual(ntasks[0]['content'], data)
        self.assertEqual(
            ntasks[1]['content'],
            "2016-07-10 task test 1 due:2018-07-13 t:2018-07-11 rec:+2y")

    def test_recurse_w_dates_q(self):
        tu.NOW = time.mktime((2016, 7, 12, 0, 0, 0, 0, 0, 1))
        data = "x 2016-07-10 2016-07-10 "\
            "task test 1 due:2016-07-13 t:2016-07-11 rec:+1q"
        task = tu.load_task(data)
        ntasks = list(tu.recurse_tasks([task], _ArgsMock()))
        self.assertEqual(len(ntasks), 2)
        self.assertEqual(ntasks[0]['content'], data)
        self.assertEqual(
            ntasks[1]['content'],
            "2016-07-10 task test 1 due:2016-10-13 t:2016-10-11 rec:+1q")


if __name__ == '__main__':
    unittest.main()
