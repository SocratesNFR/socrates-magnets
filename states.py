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
    return pickle.load(open(filename, "rb"), encoding='latin1')

def poincare(X, step, skip=10):
    step = int(step)
    skip = int(skip * step)
    return X[skip::step]

def get_tablefile(mx3_filename):
    base, _ = os.path.splitext(mx3_filename)
    # print("base", base)
    # basedir = os.path.dirname(mx3_filename)
    # outdir = os.path.join(basedir, base + ".out")
    outdir = base + ".out"
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
    # Concatenate runs
    return np.unique(np.concatenate(X), axis=0)

def count_states(X):
    return len(unique_states(X))

def final_states(X):
    return X[None, :, -1] # retain shape

def count_final_states(X):
    X = final_states(X)
    return count_states(X)

def count_diff(X):
    # Treat runs separately
    diff = np.count_nonzero(X[:,:-1] != X[:,1:], axis=2)
    return np.sum(diff, axis=1)

stats_available = {
    'state_count': count_states,
    'state_diff': count_diff,
    'final_count': count_final_states,
}

def load_stats(filename, var, stat, spp, skip):
    print("Loading {}...".format(filename))
    basedir = os.path.dirname(filename)
    info = load_run_info(filename)
    run_info = info['run_info']
    sweep_spec = info['sweep_spec']
    assert len(sweep_spec) == 1, "Sweep must be 1D"
    sweep_spec = sweep_spec[0]
    sweep_param = sweep_spec[0][0]
    sweep_values = [sp[1] for sp in sweep_spec]
    stat_fn = stats_available[stat]

    print("#Parameter values: {}".format(len(sweep_values)))
    print("#Runs per value: {}".format(list(map(len, run_info))))
    print("Sweep parameter: {}".format(sweep_param))
    print("Parameter range: {}..{} [{}]".format(
        np.min(sweep_values), np.max(sweep_values),
        sweep_values[1] - sweep_values[0]))
    print("Statistic: {}".format(stat))

    # Learn available variables from first run
    mx3_filename = os.path.join(basedir, run_info[0][0]['filename'])
    tablefile = get_tablefile(mx3_filename)
    headers, _ = parse_table_header(tablefile)
    variables = match_vars(var, headers)

    print("Variables: {}".format(", ".join(variables)))

    n_vars = len(variables)

    stats = np.zeros(len(sweep_values), dtype=int)
    state_count = np.zeros(len(sweep_values), dtype=int)

    for j, runs in enumerate(run_info):
        X = []
        try:
            for run in runs:
                mx3_filename = os.path.join(basedir, run['filename'])
                tablefile = get_tablefile(mx3_filename)
                Xi = load_data(tablefile, variables, spp, skip)
                X.append(Xi)
        except FileNotFoundError:
            print("incomplete", end=' ', flush=True)
            continue

        X = np.array(X)
        stats[j] = stat_fn(X)
        print(stats[j], end=' ', flush=True)

    print("\n")

    return sweep_param, sweep_values, stats


def main(args):
    sweep_params = []
    sweep_values = []
    stats = []
    for filename in args.filename:
        sp, sv, st = load_stats(filename, args.variables, args.stat, args.spp, args.skip)
        sweep_params.append(sp)
        sweep_values.append(sv)
        stats.append(st)

    assert len(set(sweep_params)) == 1, "Different sweep params?"
    sweep_param = sweep_params[0]
    sweep_values = np.concatenate(sweep_values)
    stats = np.concatenate(stats)

    # plt.plot(sweep_values, stats, 'o-')
    # plt.semilogy(sweep_values, stats, 'o-', basey=2)
    plt.plot(sweep_values, stats, 'o-')
    # plt.plot(2**np.array(sweep_values), stats, 'o-')
    # plt.plot(sweep_values, 2**sweep_values)

    # TODO: Better title
    title = "\n".join(args.filename)
    plt.title(title)

    plt.xlabel(sweep_param)
    plt.ylabel(args.stat)

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
    parser.add_argument('-f', '--filename', nargs='+', help='run_info file(s)')
    parser.add_argument('-v', '--variables', nargs='+',
                        help='list of variables to plot')
    parser.add_argument('-t', '--stat', choices=stats_available.keys(),
            default='state_count')
    parser.add_argument('-s', '--spp', type=int, default=100,
            help='Samples per period')
    parser.add_argument('-k', '--skip', type=float, default=0,
            help='Periods to skip')
    parser.add_argument('-o', '--savefig',
            help='Save figure(s) to file')

    args = parser.parse_args()

    main(args)
