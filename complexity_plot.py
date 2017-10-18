#!/usr/bin/env python3
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import pickle

plt.style.use('ggplot')

# Hard-coded x axis values for now...
x = np.linspace(10e-3, 100e-3, 10)
xlabel = "B"

def main(args):
    print("Loading {}...".format(args.filename))

    data = pickle.load(open(args.filename, 'rb'))
    complexity = data['complexity']
    keys = sorted(complexity.keys())
    values = [complexity[k] for k in keys]

    n_results = len(values)
    n_runs = np.mean([len(v) for v in values])

    print("  {} results, {} runs each".format(n_results, n_runs))
    print("  Compression: {}".format(data['compression']))

    mean = np.array([np.mean(v) for v in values])
    std = np.array([np.std(v) for v in values])

    for i, v in enumerate(mean):
        print("  {:.2f}: mean={:.2f} std={:.2f} #runs={}".format(x[i], mean[i], std[i], len(values[i])))

    plt.title(os.path.basename(args.filename))

    c = None
    for xi,v in zip(x, values):
        line, = plt.plot(np.repeat(xi, len(v)), v, '.', color=c)
        c = line.get_color()

    line, = plt.plot(x, mean)
    plt.fill_between(x, mean-std, mean+std, alpha=0.25, facecolor=line.get_color())

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
    parser.add_argument('filename', metavar='FILE',
                        help='pickle file from complexity_analysis.py')

    args = parser.parse_args()
    main(args)
