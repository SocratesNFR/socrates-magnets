#!/usr/bin/env python3
import sys
import os
import re
import numpy as np
import matplotlib.pyplot as plt
import zlib
import bz2
from collections import defaultdict
import pickle
import signal
import pdb
from mx3util import load_table

def handle_pdb(sig, frame):
    pdb.Pdb().set_trace(frame)    

def install_pdb(sig = signal.SIGINT):
    signal.signal(sig, handle_pdb)

install_pdb()

columns = [
    'm.region1x',
    'm.region2x',
    'm.region3x',
    'm.region4x',
    'm.region5x',
    'm.region6x',

    'm.region7y',
    'm.region8y',
    'm.region9y',
    'm.region10y',
    'm.region11y',
    'm.region12y',
]

# columns = ['m.region1x']

r = re.compile('(\S+)\.(\d+)\.(\d+)\.out$')

def parse_path(path):
    assert os.path.isdir(path)
    base = os.path.basename(path)
    m = r.search(base)
    assert m, "Path format not recognized: " + path
    return m.group(1), int(m.group(2)), int(m.group(3))

def digitize(data):
    return np.where(data > 0, 1, 0).astype('uint8')

def main(args):
    dir_info = list(map(parse_path, args.dirs))

    complexity = defaultdict(list)

    compress = bz2.compress
    if args.compression == 'zlib':
        compress = zlib.compress

    dirs_skipped = []

    for dir, info in zip(args.dirs, dir_info):
        key = info[1]
        filename = os.path.join(dir, 'table.txt')
        print("Loading {}...".format(filename))
        try:
            data = load_table(filename, columns)
        except ValueError as e:
            print("  ERROR: ", e, ", skipping!", sep='')
            dirs_skipped.append(dir)
            continue

        # debug
        # data = data[:100]

        print("  data:", data.shape, data.dtype)
        ddata = digitize(data)
        print("  ddata:", ddata.shape, ddata.dtype)
        oc = len(compress(ddata.tostring()))
        print("  complexity:", oc)
        complexity[key].append(oc)

    print("complexity=", complexity)

    for key in sorted(complexity.keys()):
        mean = np.mean(complexity[key])
        std = np.std(complexity[key])
        print("{}: mean={} std={}".format(key, mean, std))

    if args.output:
        print("Saving results to {}...".format(args.output))
        d = {
            'dirs': args.dirs,
            'dir_info': dir_info,
            'dirs_skipped': dirs_skipped,
            'compression': args.compression,
            'complexity': complexity
        }
        pickle.dump(d, open(args.output, 'wb'))

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Complexity analysis')
    parser.add_argument('-o', '--output', metavar='FILE',
            help='save result to file')
    parser.add_argument('-c', '--compression', choices=('zlib', 'bz2'), default='bz2',
            help='compression algorithm (default: %(default)s)')
    parser.add_argument('dirs', nargs='+', metavar='DIR',
            help='out directories to analyse')

    args = parser.parse_args()
    main(args)
