#!/usr/bin/env python3
import sys
import os
import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt

edgelists = [
        "si3x3-0pst-edgelist.txt",
        "si3x3-1pst-edgelist.txt",
        "si3x3-2pst-edgelist.txt",
        "si3x3-3pst-edgelist.txt",
        "si3x3-4pst-edgelist.txt",
        "si3x3-5pst-edgelist.txt",
        "si3x3-6pst-edgelist.txt",
        "si3x3-7pst-edgelist.txt",
        "si3x3-8pst-edgelist.txt",
        "si3x3-9pst-edgelist.txt",
        "si3x3-10pst-edgelist.txt",
]


def read_edgelist(filename):
    data = np.loadtxt(filename)
    return data

def unique_states(data):
    states = set()
    for state_from, state_to, phi in data:
        states.add(state_from)
        states.add(state_to) # needed?
    return states

def main(args):
    if args.load:
        data = np.loadtxt(args.load)
        pst = data[:,0] * 100
        n_states = data[:,1]
    else:
        n_states = []
        for (i, edgelist) in enumerate(edgelists):
            filename = os.path.join('results', edgelist)
            data = read_edgelist(filename)
            states = unique_states(data)
            n_states.append(len(states))
            print(edgelist, n_states[-1])
        pst = np.arange(0, len(n_states)) / 100


    if args.style:
        plt.style.use(args.style)

    plt.title("State space search")
    plt.plot(pst, n_states, 'o-')
    plt.xlabel("Local perturbation (\%) ")
    plt.ylabel("Number of states")

    if args.dump:
        data = np.vstack([pst, n_states]).T
        np.savetxt(args.dump, data, fmt=('%.4f', '%d'), header='pst, n_states')

    if args.output:
        plt.savefig(args.output)
    else:
        plt.show()

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Plot #states from edgelist.')
    parser.add_argument('-o', '--output', metavar='FILE',
                        help='save plot to file')
    parser.add_argument('--dump', metavar='FILE', help='Save result to csv')
    parser.add_argument('--load', metavar='FILE', help='Load result from csv')
    parser.add_argument('--style', default=None)
    # parser.add_argument('edgelist', nargs='+', metavar='FILE',
                        # help='edgelists')

    args = parser.parse_args()
    main(args)
