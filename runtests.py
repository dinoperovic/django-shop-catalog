#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys
import os


def main(verbosity=1, *test_args):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'

    from django_nose import NoseTestSuiteRunner
    test_runner = NoseTestSuiteRunner(verbosity)

    test_apps = ['addresses', 'catalog', 'orders', 'reviews']

    if not test_args:
        test_args = ['tests.%s' % x for x in test_apps]
    else:
        test_args = ['tests.%s' % x for x in test_args if x in test_apps]

    failures = test_runner.run_tests(test_args)
    sys.exit(failures)

if __name__ == '__main__':
    main(1, *sys.argv[1:])
