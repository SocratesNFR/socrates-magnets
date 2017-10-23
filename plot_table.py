#!/usr/bin/env python3
import sys
import re
import numpy as np
import matplotlib.pyplot as plt
from mx3util import parse_table_header, load_table

plt.style.use('ggplot')

def main(args):
    # get header
    headers, _ = parse_table_header(args.filename)

    if args.list:
        print("Available variables from {}:".format(args.filename))
        print("    {}".format(headers[0]))
        for i in range(1, len(headers), 3):
            print("    {}".format(", ".join(headers[i:i+3])))
        return

    data = np.loadtxt(args.filename)

    if args.var:
        variables = ['t']
        for v in args.var:
            if v in headers:
                variables.append(v)
            elif v + "x" in headers:
                variables.append(v + "x")
                variables.append(v + "y")
                variables.append(v + "z")
            else:
                raise IndexError(v)
    else:
        variables = headers

    data = load_table(args.filename, variables)
    t0 = args.t0
    t1 = args.t1

    n_rows = 1
    if args.digitize:
        n_rows += 1
    fig, axes = plt.subplots(n_rows, 1, sharex=True, sharey=False)
    axes = np.atleast_1d(axes)
    axes = axes.flatten()

    t = data[t0:t1,0] # first is always time
    for i, v in enumerate(variables[1:], start=1):
        d = data[t0:t1,i]
        line, = axes[0].plot(t, d, label=v)

        if args.digitize:
            dd = np.where(d > 0, 1, 0)
            axes[1].plot(t, dd - 1.1*(i - 1), color=line.get_color())


    # Shrink current axis by 10%
    for ax in axes:
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])

    fig.suptitle(args.filename)
    axes[0].legend(loc='upper left', bbox_to_anchor=(1.0, 1.0))
    axes[0].set_xlim(t[0], t[-1])

    axes[-1].set_xlabel("t")
    if args.digitize:
        axes[1].get_yaxis().set_visible(False)

    if args.output:
        plt.savefig(args.output)
    else:
        plt.show()

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Plot mumax3 table data.')
    parser.add_argument('-f', '--filename', metavar='FILE', default='table.txt',
                        help='filename of table data (default: %(default)s)')
    parser.add_argument('-o', '--output', metavar='FILE',
                        help='save plot to file')
    parser.add_argument('-l', '--list', action='store_true',
                        help='list available variables')
    parser.add_argument('-d', '--digitize', action='store_true')
    parser.add_argument('-t0', type=int, default=0,
                        help='start at sample')
    parser.add_argument('-t1', type=int, default=None)
                        help='stop at sample')
    parser.add_argument('var', nargs='*',
                        help='list of variables to plot')

    args = parser.parse_args()
    main(args)
