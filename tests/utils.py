# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import sys


def warning(*args):
    print('WARNING: ', *args, file=sys.stderr)
