#!/usr/bin/env python3
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import pickle
from collections import defaultdict

plt.style.use('ggplot')

def load_files(filenames):
    xlabel = None
    y = defaultdict(list)
    has_params = False

    for filename in filenames:
        print("Loading {}...".format(filename))

        data = pickle.load(open(filename, 'rb'))
        complexity = data['complexity']
        keys = sorted(complexity.keys())
        values = [complexity[k] for k in keys]

        if 'param_name' in data:
            xlabel = data['param_name']

        # All files must either have params or none at all
        if 'params' in data:
            has_params = True
        assert has_params and 'params' in data

        params = data.get('params', keys)

        n_results = len(values)
        n_runs = np.mean([len(v) for v in values])

        print("  {} results, {} runs each".format(n_results, n_runs))
        print("  Compression: {}".format(data['compression']))
        if 'param_name' in data:
            print("  Param name: {}".format(data['param_name']))
        print("  Params: {}".format(keys))

        for x, v in zip(params, values):
            y[x].extend(v)

    return y, xlabel


def main(args):
    ydata, xlabel = load_files(args.filenames)

    x = sorted(ydata.keys())
    y = [ydata[xi] for xi in x]

    mean = np.array([np.mean(yi) for yi in y])
    std = np.array([np.std(yi) for yi in y])

    print("Stats:")
    for i in range(len(mean)):
        print("  {:.3f}: mean={:.2f} std={:.2f} #runs={}".format(x[i], mean[i], std[i], len(y[i])))

    title = ", ".join(map(os.path.basename, args.filenames))
    plt.title(title)

    c = None
    for xi, yi in zip(x, y):
        line, = plt.plot(np.repeat(xi, len(yi)), yi, '.', color=c)
        c = line.get_color()

    line, = plt.plot(x, mean)
    plt.fill_between(x, mean-std, mean+std, alpha=0.25, facecolor=line.get_color())

    if xlabel:
        plt.xlabel(xlabel)
    plt.ylim(ymin=0)
    plt.ylabel("Complexity")

    if args.output:
        plt.savefig(args.output)
    else:
        plt.show()

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Complexity plot')
    parser.add_argument('-o', '--output', metavar='FILE',
                        help='save plot to file')
    parser.add_argument('filenames', metavar='FILE', nargs='+',
                        help='pickle file from complexity_analysis.py')

    args = parser.parse_args()
    main(args)
