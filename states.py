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

# def load_stats(f,v,s,spp,skip):
    # return 'Foo', np.arange(10), np.random.uniform(size=10)

def main(args):
    labels = args.label if args.label else args.filename
    title = args.title

    sweep_params = []
    sweep_values = []
    stats = []
    for filename in args.filename:
        sp, sv, st = load_stats(filename, args.variables, args.stat, args.spp, args.skip)
        sweep_params.append(sp)
        sweep_values.append(sv)
        stats.append(st)

    assert len(set(sweep_params)) == 1, "Different sweep params?"

    if args.combine:
        sweep_params = [sweep_params[0]]
        sweep_values = [np.concatenate(sweep_values)]
        stats = [np.concatenate(stats)]

    assert len(labels) >= len(stats), "Need more labels!"

    for sp, sv, st, lb in zip(sweep_params, sweep_values, stats, labels):
        # plt.plot(sweep_values, stats, 'o-')
        # plt.semilogy(sweep_values, stats, 'o-', basey=2)
        plt.plot(sv, st, 'o-', label=lb)
        # plt.plot(2**np.array(sweep_values), stats, 'o-')
        # plt.plot(sv, 2**np.array(sv))

    if title:
        plt.title(title)

    plt.xlabel(sweep_params[0])
    plt.ylabel(args.stat)

    if len(stats) > 1:
        plt.legend()

    if args.savefig:
        print("Saving figure {}".format(args.savefig))
        plt.savefig(args.savefig)
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
    parser.add_argument('-c', '--combine', action='store_true', default=False,
            help='Combine input files to single plot')
    parser.add_argument('-s', '--spp', type=int, default=100,
            help='Samples per period')
    parser.add_argument('-k', '--skip', type=float, default=0,
            help='Periods to skip')
    parser.add_argument('-o', '--savefig',
            help='Save figure(s) to file')
    parser.add_argument('-l', '--label', nargs='+')
    parser.add_argument('--title')

    args = parser.parse_args()

    main(args)
