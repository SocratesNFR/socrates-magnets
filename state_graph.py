#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import write_dot
from mx3util import parse_table_header, load_table, match_vars, array_bit

from states import load_run_info, get_tablefile, load_data

def state_label(s):
    # return ('0x{:0' + str(len(s)) + 'x}').format(array_bit(s))
    return hex(array_bit(s))

def load_graph(filename, var, spp, skip, run_index=0, input_param=None):
    print("Loading {}...".format(filename))
    basedir = os.path.dirname(filename)
    info = load_run_info(filename)
    run_info = info['run_info']
    sweep_spec = info['sweep_spec']
    assert len(sweep_spec) == 1, "Sweep must be 1D"
    sweep_spec = sweep_spec[0]
    sweep_param = sweep_spec[0][0]
    sweep_values = [sp[1] for sp in sweep_spec]

    print("#Parameter values: {}".format(len(sweep_values)))
    print("#Runs per value: {}".format(list(map(len, run_info))))
    print("Sweep parameter: {}".format(sweep_param))
    print("Parameter range: {}..{} [{}]".format(
        np.min(sweep_values), np.max(sweep_values),
        sweep_values[1] - sweep_values[0]))

    # Learn available variables from first run
    mx3_filename = os.path.join(basedir, run_info[0][0]['filename'])
    tablefile = get_tablefile(mx3_filename)
    headers, _ = parse_table_header(tablefile)
    variables = match_vars(var, headers)

    print("Variables: {}".format(", ".join(variables)))

    n_vars = len(variables)

    G = nx.DiGraph()
    # G = nx.MultiDiGraph()

    for i, run in enumerate(run_info[run_index]):
        mx3_filename = os.path.join(basedir, run['filename'])
        tablefile = get_tablefile(mx3_filename)
        print(tablefile)
        X = load_data(tablefile, variables, spp, skip)
        states = list(map(state_label, X))
        attrs = [{}]*(len(states)-1)
        if input_param:
            input = run['params'][input_param]
            attrs = [{'label': i} for i in input]
            # attrs = [{'label': input[:i+1]} for i in range(len(input))]
            # attrs = [{'label': input} for i in input]
            print(attrs)

        for u, v, attr in zip(states[:-1], states[1:], attrs):
            print("{}->{} {}".format(u, v, attr))
            G.add_edge(u, v, **attr)

    return G


def main(args):
    G = load_graph(args.filename, args.variables, args.spp, args.skip, args.run, args.input_param)

    if args.dot:
        write_dot(G, args.dot)
    else:
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True)
        edge_labels = nx.get_edge_attributes(G, 'label')
        nx.draw_networkx_edge_labels(G, pos, edge_labels)
        plt.show()

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-f', '--filename', required=True, help='run_info file')
    parser.add_argument('-r', '--run', type=int, default=0, help='run index')
    parser.add_argument('-v', '--variables', nargs='+',
            help='list of variables to graph')
    parser.add_argument('-c', '--combine', action='store_true', default=False,
            help='Combine input files to single plot')
    parser.add_argument('-s', '--spp', type=int, default=100,
            help='Samples per period')
    parser.add_argument('-k', '--skip', type=float, default=0,
            help='Periods to skip')
    parser.add_argument('-I', '--input-param', help='Name of input parameter for edge labels')
    parser.add_argument('-o', '--savefig', help='Save figure(s) to file')
    parser.add_argument('-d', '--dot', help='Save Graphviz dotfile')
    parser.add_argument('-l', '--label', nargs='+')
    parser.add_argument('--title')

    args = parser.parse_args()

    main(args)
