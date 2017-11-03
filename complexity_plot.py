#!/usr/bin/env python3
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import pickle
from collections import defaultdict

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

    x = np.array(sorted(ydata.keys()))

    if args.xmin is not None:
        xmin = float(args.xmin)
        x = x[x >= xmin]
    if args.xmax is not None:
        xmax = float(args.xmax)
        x = x[x <= xmax]

    y = [ydata[xi] for xi in x]

    mean = np.array([np.mean(yi) for yi in y])
    max = np.array([np.max(yi) for yi in y])
    std = np.array([np.std(yi) for yi in y])

    print("Stats:")
    for i in range(len(mean)):
        print("  {:.3f}: mean={:.2f} std={:.2f} #runs={}".format(x[i], mean[i], std[i], len(y[i])))

    if args.style:
        plt.style.use(args.style)

    if args.title is None:
        title = " + ".join(map(os.path.basename, args.filenames))
    else:
        title = args.title

    plt.title(title)

    line_color = None

    plot = args.plot.split(',')
    if 'all' in plot:
        plot = ['mean', 'std', 'max', 'scatter']

    for p in plot:
        if p == 'mean':
            line, = plt.plot(x, mean)
            line_color = line.get_color()
        elif p == 'max':
            plt.plot(x, max)
        elif p == 'std':
            line = plt.fill_between(x, mean-std, mean+std, alpha=0.25, facecolor=line_color)
            line_color = line.get_facecolor()
        elif p == 'scatter':
            c = None
            for xi, yi in zip(x, y):
                line, = plt.plot(np.repeat(xi, len(yi)), yi, '.', color=c)
                c = line.get_color()
        else:
            raise ValueError(p)

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
    parser.add_argument('-p', '--plot', default='scatter,mean,std',
                        help='what to plot [mean|std|max|scatter] (default: %(default)s)')
    parser.add_argument('-t', '--title')
    parser.add_argument('--style', default=None)
    parser.add_argument('-x0', '--xmin', type=float)
    parser.add_argument('-x1', '--xmax', type=float)
    parser.add_argument('filenames', metavar='FILE', nargs='+',
                        help='pickle file from complexity_analysis.py')

    args = parser.parse_args()
    main(args)
