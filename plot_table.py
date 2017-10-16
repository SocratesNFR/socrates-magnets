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

    t = data[:,0] # first is always time
    for i, v in enumerate(variables[1:], start=1):
        d = data[:,i]
        plt.plot(t, d, label=v)

        if args.digitize:
            dd = np.where(d > 0, 1, 0)
            plt.plot(t, -1.5 + 0.2 * dd)


    # Shrink current axis by 10%
    ax = plt.gca()
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])

    plt.title(args.filename)
    plt.xlabel("t")
    plt.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0))
    plt.xlim(0, t[-1])

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
    parser.add_argument('var', nargs='*',
                        help='list of variables to plot')

    args = parser.parse_args()
    main(args)
