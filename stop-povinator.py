#!/usr/bin/env python3

import psutil
import sys


def pidof(pgname):
    for proc in psutil.process_iter(['cmdline']):
        if ' '.join(proc.info['cmdline']).startswith(pgname):
            return proc


if (povinator := pidof('python -m povinator3000')) is not None:
    povinator.terminate()
    sys.exit(0)
else:
    sys.exit(1)
