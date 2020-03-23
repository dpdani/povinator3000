#!/usr/bin/env python3

import subprocess
import platform
import os
import time

stop = False

POV3K_YES = 'y\n'
POV3K_NO = 'n\n'
POV3K_WELCOME = 'Welcome to Povinator3000!\nPlease, enter the "Lauree" folder: '
POV3K_RESPONSES_SHEET_SUFFIX = 'a responses sheet? [Y/n]: '
POV3K_DOWNLOAD = 'Would you like to download the presentations? [Y/n]: '
POV3K_ZIP = 'Would you like to make a ZIP archive of the presentations? [Y/n]: '
POV3K_BYE = 'Done. Bye :)\n'
POV3K_NO_SHEETS = 'No responses sheets found.\n'


log = {}


os.chdir('../..')


def open_povinator(args):
    if platform.system() == 'Windows':
        return open_povinator_windows(args)
    else:
        return open_povinator_linux(args)


def open_povinator_linux(args):
    import fcntl
    pp = subprocess.Popen(
        ['python', 'povinator3000.py', *args],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding='utf8',
    )
    fd = pp.stdout.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    log[pp] = ''
    return pp


def open_povinator_windows(args):
    pp = subprocess.Popen(
        ['python', 'povinator3000.py', *args],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding='utf8',
    )
    log[pp] = ''
    return pp


def read(proc):
    try:
        r = proc.stdout.read()
    except:
        return ''
    log[proc] += r
    return r


def wait_and_read(proc, timeout=60):
    start = time.time()
    r = read(proc)
    while r == '' and (time.time()-start < timeout):
        time.sleep(.2)
        r = read(proc)
    return r


def write(proc, string):
    proc.stdin.write(string)
    proc.stdin.flush()
    log[proc] += string


def go(url, sheets, download, zip):
    povinator = open_povinator(['go'])
    init = wait_and_read(povinator)
    if init != POV3K_WELCOME:
        raise RuntimeError
    if not url.endswith('\n'):
        url = url + '\n'
    write(povinator, url)
    got = wait_and_read(povinator)
    while got.endswith(POV3K_RESPONSES_SHEET_SUFFIX):
        found = False
        for s in sheets:
            if s in got:
                write(povinator, POV3K_YES)
                found = True
                break
        if not found:
            write(povinator, POV3K_NO)
        got = wait_and_read(povinator)
    if got == POV3K_NO_SHEETS:
        povinator.wait()
        return povinator, None
    while got != '':
        got = wait_and_read(povinator, timeout=3)
    if download:
        write(povinator, POV3K_YES)
        _ = wait_and_read(povinator)  # "Downloading presentations..."
        r = wait_and_read(povinator)
        if r.endswith(POV3K_ZIP):
            if zip:
                write(povinator, POV3K_YES)
            else:
                write(povinator, POV3K_NO)
    else:
        write(povinator, POV3K_NO)
    r = wait_and_read(povinator)
    povinator.wait()
    return povinator, r == POV3K_BYE


def get_sheets(url):
    povinator = open_povinator(['go'])
    init = wait_and_read(povinator)
    if init != POV3K_WELCOME:
        raise RuntimeError
    if not url.endswith('\n'):
        url = url + '\n'
    write(povinator, url)
    got = wait_and_read(povinator)
    sheets = []
    while got.endswith(POV3K_RESPONSES_SHEET_SUFFIX):
        sheet = got[got.find('"') + 1:]
        sheet = sheet[:sheet.find('"')]
        sheets.append(sheet)
        write(povinator, POV3K_NO)
        got = wait_and_read(povinator)
    povinator.wait()
    return sheets
