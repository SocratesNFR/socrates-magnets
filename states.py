#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
from itertools import cycle, groupby
from mx3util import *

def load_data(tablefile, variables, spp=100, skip=1):
    X = load_table(tablefile, variables)
    return digitize(X, spp, skip)

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

def count_final_len(X):
    final_lens = []
    for Xi in X:
        # Going backwards, find the first group of equal elements
        groups = groupby(map(tuple, Xi[::-1]))
        first = next(groups)
        final_len = len(list(first[1]))
        final_lens.append(final_len)
        '''
        eqfinal = np.all(Xi == Xi[-1], axis=1)
        print(eqfinal)
        # Going backwards, find index first state not equal to final state
        final_len = np.where(eqfinal[::-1] == False)[0][0]
        final_lens.append(final_len)
        '''
    return np.mean(final_lens)

stats_available = {
    'state_count': count_states,
    'state_diff': count_diff,
    'final_count': count_final_states,
    'final_len': count_final_len,
}

def load_stats(filename, var, stat, spp, skip):
    print("Loading {}...".format(filename))
    run = RunInfo(filename, load=True)
    sweep_spec = run['sweep_spec']
    assert len(sweep_spec) == 1, "Sweep must be 1D"
    sweep_spec = sweep_spec[0]
    sweep_param = sweep_spec[0][0]
    sweep_values = [sp[1] for sp in sweep_spec]
    assert len(sweep_values) == run.run_count, "Not enough runs"
    stat_fn = stats_available[stat]

    print("#Parameter values: {}".format(len(sweep_values)))
    print("#Runs per value: {}".format(run.repeat_counts()))
    print("Sweep parameter: {}".format(sweep_param))
    print("Parameter range: {}..{} [{}]".format(
        np.min(sweep_values), np.max(sweep_values),
        sweep_values[1] - sweep_values[0]))
    print("Statistic: {}".format(stat))

    # Learn available variables from first run
    header = run.get_header(0, 0)
    variables = match_vars(var, header)

    print("Variables: {}".format(", ".join(variables)))

    n_vars = len(variables)

    stats = np.zeros(len(sweep_values), dtype=int)
    state_count = np.zeros(len(sweep_values), dtype=int)

    for run_index in range(run.run_count):
        X = []
        try:
            for repeat_index in range(run.repeat_count(run_index)):
                Xi = run.load_table(run_index, repeat_index, variables)
                Xi = poincare(Xi, spp, skip)
                Xi = digitize(Xi)
                X.append(Xi)
        except FileNotFoundError:
            print("incomplete", end=' ', flush=True)
            continue

        X = np.array(X)
        stats[run_index] = stat_fn(X)
        print(stats[run_index], end=' ', flush=True)

    print("\n")

    return sweep_param, sweep_values, stats

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
