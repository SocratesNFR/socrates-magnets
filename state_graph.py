#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import subprocess
from itertools import groupby
from operator import itemgetter
from networkx.drawing.nx_agraph import write_dot
from mx3util import parse_table_header, load_table, match_vars, array_bit

from states import load_run_info, get_tablefile, load_data

def state_label(s):
    # return ('0x{:0' + str(len(s)) + 'x}').format(array_bit(s))
    return '{:x}'.format(array_bit(s))
    # return hex(array_bit(s))

def group_consecutive(l):
    return [list(map(itemgetter(1), g)) for k, g in groupby(enumerate(l), (lambda i: i[0]-i[1]))]

def load_graph(filename, var, spp, skip, run_index=0, input_param=None):
    print("Loading {}...".format(filename))
    basedir = os.path.dirname(filename)
    info = load_run_info(filename)
    run_info = info['run_info']

    print("#Runs per value: {}".format(list(map(len, run_info))))
    print("Run index: {} ({} runs)".format(run_index, len(run_info[run_index])))

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
        X = load_data(tablefile, variables, spp, skip)
        states = list(map(state_label, X))
        attrs = [{}]*(len(states)-1)
        if input_param:
            input = run['params'][input_param]
            attrs = [{'label': i} for i in input]
            # attrs = [{'label': input[:i+1]} for i in range(len(input))]
            # attrs = [{'label': input} for i in input]
            # print(attrs)

        for u, v, attr in zip(states[:-1], states[1:], attrs):
            # print("{}->{} {}".format(u, v, attr))
            G.add_edge(u, v, **attr)

        for t, u in enumerate(states):
            c = G.nodes[u].setdefault('count', 0)
            G.nodes[u]['count'] += 1
            G.nodes[u].setdefault('t', [])
            G.nodes[u]['t'].append(t)

    # Add labels
    for u in G.nodes:
        # G.nodes[u]['label'] = '{} ({})'.format(u, G.nodes[u]['count'])
        t = group_consecutive(G.nodes[u]['t'])
        tl = ['{}-{}'.format(ti[0], ti[-1]) if len(ti) > 1 else '{}'.format(ti[0]) for ti in t]
        tl = ', '.join(tl)

        G.nodes[u]['label'] = '{} (t={})'.format(u, tl)

    print("Graph: {} nodes, {} edges".format(G.number_of_nodes(), G.number_of_edges()))

    return G

def write_dotpng(G, png):
    dot = args.savefig + '.dot'
    write_dot(G, dot)
    argv = ['dot', '-Tpng', dot]
    fd = open(png, 'wb')
    return subprocess.call(argv, stdout=fd)

def show_graph(G):
    pos = nx.spring_layout(G)
    # nx.draw(G, pos, with_labels=True)
    nx.draw(G, pos)
    # node_labels = {u: '{} ({})'.format(u, G.nodes[u]['count']) for u in G.nodes()}
    node_labels = nx.get_node_attributes(G, 'label')
    nx.draw_networkx_labels(G, pos, node_labels)
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels)
    plt.show()

def main(args):
    G = load_graph(args.filename, args.variables, args.spp, args.skip, args.run, args.input_param)

    if args.dot:
        write_dot(G, args.dot)
    if args.savefig:
        write_dotpng(G, args.savefig)
    else:
        show_graph(G)

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
