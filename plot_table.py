#!/usr/bin/env python3
import sys
import numpy as np
import matplotlib.pyplot as plt
from mx3util import parse_table_header, load_table, match_vars

line_highlight = False

def main(args):
    # get header
    headers, _ = parse_table_header(args.filename)

    if args.list:
        print("Available variables from {}:".format(args.filename))
        print("    {}".format(headers[0]))
        for i in range(1, len(headers), 3):
            print("    {}".format(", ".join(headers[i:i+3])))
        return

    assert args.x in headers, "Unknown variable '{}'".format(args.x)
    variables = [args.x]

    if args.var:
        matches = match_vars(args.var, headers)
        variables.extend(matches)
    else:
        variables.extend(filter(lambda v: v != args.x, headers))

    data = load_table(args.filename, variables)
    t0 = args.t0
    t1 = args.t1
    xlabel = args.x

    n_rows = 1
    if args.digitize:
        n_rows += 1
    fig, axes = plt.subplots(n_rows, 1, sharex=True, sharey=False)
    axes = np.atleast_1d(axes)
    axes = axes.flatten()

    x = data[t0:t1,0]
    lines = []
    dlines = []
    for i, v in enumerate(variables[1:], start=1):
        d = data[t0:t1,i]
        line, = axes[0].plot(x, d, label=v)
        lines.append(line)

        dlines.append(None)
        if args.digitize:
            dd = np.where(d > 0, 1, 0)
            dlines[-1], = axes[1].plot(x, dd - 1.1*(i - 1), color=line.get_color())


    # Shrink current axis by 10%
    for ax in axes:
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])

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
    parser.add_argument('var', nargs='*',
                        help='list of variables to plot')

    args = parser.parse_args()
    main(args)
