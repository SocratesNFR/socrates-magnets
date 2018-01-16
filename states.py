#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
from itertools import cycle
from mx3util import parse_table_header, load_table, match_vars

def run_load_sweep(sweep_data, suptitle=None):
    for data in sweep_data['sweep_data']:
        run_load_single(data, suptitle)

def load_run_info(filename):
    return pickle.load(open(args.filename, "rb"), encoding='latin1')

def poincare(X, step, skip=10):
    step = int(step)
    skip = int(skip * step)
    return X[skip::step]

def get_tablefile(mx3_filename):
    base, _ = os.path.splitext(mx3_filename)
    basedir = os.path.dirname(mx3_filename)
    outdir = os.path.join(basedir, base + ".out")
    tablefile = os.path.join(outdir, "table.txt")
    return tablefile

def load_data(tablefile, variables, spp=100, skip=1):
    X = load_table(tablefile, variables)
    if len(variables) == 1:
        X.shape += (1,)

    n_periods = int(X.shape[0] / spp)
    X = X[:n_periods * spp] # truncate
    step = spp
    assert skip < n_periods, "{}: Not enough periods ({}) to skip {}".format(tablefile, n_periods, skip)

    PX = poincare(X, step, skip)

    # digitize
    DX = np.where(PX > 0, 1, 0)

    return DX

def unique_states(X):
    return np.unique(X, axis=0)

def count_states(X):
    return len(unique_states(X))

def main(args):
    basedir = os.path.dirname(args.filename)
    info = load_run_info(args.filename)
    run_info = info['run_info']
    sweep_spec = info['sweep_spec']
    assert len(sweep_spec) == 1, "Sweep must be 1D"
    sweep_spec = sweep_spec[0]
    sweep_param = sweep_spec[0][0]
    sweep_values = [sp[1] for sp in sweep_spec]

    print("#Parameter values: {}".format(len(sweep_values)))
    print("#Runs per value: {}".format(len(run_info[0])))
    print("Sweep parameter: {}".format(sweep_param))
    print("Parameter range: {}..{} [{}]".format(
        np.min(sweep_values), np.max(sweep_values),
        sweep_values[1] - sweep_values[0]))

    # Learn available variables from first run
    mx3_filename = os.path.join(basedir, run_info[0][0]['filename'])
    tablefile = get_tablefile(mx3_filename)
    headers, _ = parse_table_header(tablefile)
    variables = match_vars(args.var, headers)

    print("Variables: {}".format(", ".join(variables)))

    n_vars = len(variables)

    state_count = np.zeros(len(sweep_values), dtype=int)

    for j, runs in enumerate(run_info):
        for run in runs:
            # print(".", end='', flush=True)
            mx3_filename = os.path.join(basedir, run['filename'])
            tablefile = get_tablefile(mx3_filename)
            X = load_data(tablefile, variables, args.spp, args.skip)
            # states = unique_states(X)
            state_count[j] = count_states(X)
            # print(state_count[j], states)
            print(state_count[j], end=' ', flush=True)

    print("")


    plt.plot(sweep_values, state_count, 'o-')

    # TODO: Better title
    title = str(info['args'].outdir)
    plt.title(title)

    plt.xlabel(sweep_param)
    plt.ylabel("#states")

    if args.savefig:
        filename = args.savefig
        if n_vars > 1:
            f, ext = os.path.splitext(filename)
            filename = '{}_%s{}'.format(f, ext)
        for i, v in zip(plt.get_fignums(), variables):
            plt.figure(i)
            f = filename % (v,) if n_vars > 1 else filename
            print("Saving figure {}".format(f))
            plt.savefig(f)
    else:
        plt.show()

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('filename', help='run_info file')
    parser.add_argument('var', nargs='+',
                        help='list of variables to plot')
    parser.add_argument('-s', '--spp', type=int, default=100,
            help='Samples per period')
    parser.add_argument('-k', '--skip', type=float, default=0,
            help='Periods to skip')
    parser.add_argument('-o', '--savefig',
            help='Save figure(s) to file')

    args = parser.parse_args()

    main(args)
