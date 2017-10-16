#!/usr/bin/env python3
import sys
import re
import numpy as np
import matplotlib.pyplot as plt

plt.style.use('ggplot')

def main(args):
    # get header
    r = re.compile('(\S+) \((\S*)\)')
    with open(args.filename) as f:
        l = f.readline()
        l = l.strip('# \n')
        head = l.split('\t')
        head = [r.match(h).groups() for h in head]
        headers = [h[0] for h in head]
        units = [h[1] for h in head]
        indices = dict([(headers[i], i) for i in range(len(headers))])
        # print(header)
        # print(indices)

    if args.list:
        print("Available variables from {}:".format(args.filename))
        print("    {}".format(headers[0]))
        for i in range(1, len(headers), 3):
            print("    {}".format(", ".join(headers[i:i+3])))
        return

    data = np.loadtxt(args.filename)

    if args.var:
        variables = []
        for v in args.var:
            if v in indices:
                variables.append(indices[v])
            elif v + "x" in indices:
                variables.append(indices[v + "x"])
                variables.append(indices[v + "y"])
                variables.append(indices[v + "z"])
            else:
                raise IndexError(v)
    else:
        variables = range(1, data.shape[1])

    t = data[:,0]
    for v in variables:
        d = data[:,v]
        plt.plot(t, d, label=headers[v])

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
