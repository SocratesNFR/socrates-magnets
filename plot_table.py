#!/usr/bin/env python3
import sys
import re
import numpy as np
from numpy.linalg import norm
import matplotlib.pyplot as plt
from mx3util import parse_table_header, load_table, match_vars

line_highlight = False

def func_norm(x):
    if np.all(x[:,1] == 0):
        d = x[:,0] # x direction
    else:
        d = x[:,1] # y direction
    return (norm(x, axis=1) * np.where(d >= 0, 1, -1)).reshape((-1, 1))

def func_atan(x):
    return np.rad2deg(np.arctan(x[:,1] / x[:,0])).reshape((-1, 1))

funcs = {
    'norm': func_norm,
    'atan': func_atan
}

def parse_var(var, headers):
    m = re.match(r'(\w+)\((.*)\)', var)
    if m:
        fn = funcs[m.group(1)]
        v = list(map(str.strip, m.group(2).split(',')))
        v = tuple(match_vars(v, headers))
        yield (var, fn) + v

    else:
        for v in match_vars([var], headers):
            yield (v, None, v)

def main(args):
    # get header
    headers, _ = parse_table_header(args.filename)

    if args.list:
        print("Available variables from {}:".format(args.filename))
        print("    {}".format(headers[0]))
        for i in range(1, len(headers), 3):
            print("    {}".format(", ".join(headers[i:i+3])))
        return

    # assert args.x in headers, "Unknown variable '{}'".format(args.x)
    varmap = list(parse_var(args.x, headers))

    if args.var:
        for v in args.var:
            varmap.extend(list(parse_var(v, headers)))
    else:
        varmap.extend((var, None, var) for var in headers if var != args.x)

    # flatten
    variables = [v for var in varmap for v in var[2:]]

    t0 = args.t0
    t1 = args.t1
    data = load_table(args.filename, variables)
    data = data[t0:t1]

    xlabel = args.x

    if args.poincare:
        data = data[::args.poincare]

    # Apply funcs
    data2 = []
    i = 0
    for var in varmap:
        fn = var[1]
        count = len(var[2:])
        d = data[:,i:i+count]
        if fn:
            d = fn(d)
        else:
            assert d.shape[1] == 1
        data2.append(d)
        i += count

    data2 = np.concatenate(data2, axis=1)

    n_rows = 1
    if args.digitize:
        n_rows += 1
    fig, axes = plt.subplots(n_rows, 1, sharex=True, sharey=False)
    axes = np.atleast_1d(axes)
    axes = axes.flatten()

    x = data2[:,0]
    lines = []
    dlines = []
    for i, var in enumerate(varmap[1:], start=1):
        d = data2[:,i]
        label = var[0]
        line, = axes[0].plot(x, d, label=label)
        lines.append(line)

        dlines.append(None)
        if args.digitize:
            dd = np.where(d > 0, 1, 0)
            dlines[-1], = axes[1].plot(x, dd - 1.1*(i - 1), color=line.get_color())


    # Shrink current axis by 10%
    for ax in axes:
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])

    if args.ylim:
        axes[0].set_ylim(args.ylim)

    fig.suptitle(args.filename)
    leg = axes[0].legend(loc='upper left', bbox_to_anchor=(1.0, 1.0))

    axes[-1].set_xlabel(xlabel)
    if args.digitize:
        axes[1].get_yaxis().set_visible(False)

    artist_group = []
    for line, dline, legline, legtext in zip(lines, dlines, leg.get_lines(), leg.get_texts()):
        #line.set_picker(5) # 5 pts tolerance
        legline.set_picker(5)
        legtext.set_picker(5)

        group = [line, legline, legtext]
        if dline:
            group.append(dline)

        artist_group.append(group)

    def onpick(event):
        global line_highlight
        line_highlight = not line_highlight
        artist = event.artist
        alpha = 1.0
        if line_highlight:
            alpha = 0.1

        for g in artist_group:
            if line_highlight and artist in g:
                continue
            for a in g:
                a.set_alpha(alpha)
        fig.canvas.draw()

    fig.canvas.mpl_connect('pick_event', onpick)

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
    parser.add_argument('-t1', type=int, default=None,
                        help='stop at sample')
    parser.add_argument('-x', default='t',
                        help='x axis variable')
    parser.add_argument('--ylim', nargs=2, type=float, metavar=('YMIN', 'YMAX'),
                        help='set ylim')
    parser.add_argument('-p', '--poincare', type=int, metavar='N',
                        help='apply poincare map (plot every N samples)')
    parser.add_argument('var', nargs='*',
                        help='list of variables to plot')

    args = parser.parse_args()
    main(args)
