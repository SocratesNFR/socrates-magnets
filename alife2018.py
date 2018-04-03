#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
from itertools import cycle

from states import load_stats
from state_graph import load_graph, label_nodes, color_nodes, write_dotfig
# from mx3util import *

plt.style.use('publish')

textwidth = 7 # 7in
gr = (np.sqrt(5)-1.0)/2.0 # golden ratio

variables = ['m.region{}x'.format(i) for i in range(1,41,2)] + \
            ['m.region{}y'.format(i) for i in range(2,41,2)]

def savefig(basename):
    print(basename + ".{pdf,svg,png}")
    plt.savefig(basename + ".pdf")
    plt.savefig(basename + ".svg")
    plt.savefig(basename + ".png", dpi=600)


def fig_states():
    plt.figure(figsize=(textwidth*0.7, textwidth*0.7*gr))

    filenames = [
        '/data/socrates/mx3/si-square-fixed-4x4-220x80x25-ls320-phi45-sin-200MHz-sweep-B-100p-detailed/run_info.pickle',
        '/data/socrates/mx3/si-square-fixed-4x4-220x80x25-ls320-phi45-sin-sweep-B-100p-detailed/run_info.pickle',
        '/data/socrates/mx3/si-square-fixed-4x4-220x80x25-ls320-phi45-sin-50MHz-sweep-B-100p-detailed/run_info.pickle',
        '/data/socrates/mx3/si-square-fixed-4x4-220x80x25-ls320-phi45-sin-10MHz-sweep-B-100p-detailed/run_info.pickle',
        ]

    labels = [
        '200 MHz',
        '100 MHz',
        '50 MHz',
        '10 MHz',
        ]

    for filename, label in zip(filenames, labels):
        sp, sv, st = load_stats(filename, variables, 'state_count', spp=100, skip=1)
        sv = np.array(sv) * 1e3 # mT
        sv = sv[5:] # skip 60-64
        st = st[5:] # skip 60-64
        plt.plot(sv, st, label=label)

    plt.xlabel('Field strength $A$ [mT]')
    plt.ylabel('Unique states $S$')
    plt.legend()

    plt.tight_layout(pad=0)
    savefig("states")

def fig_graphs():
    filenames = [
        '/data/socrates/mx3/si-square-fixed-4x4-220x80x25-ls320-phi45-sin-10MHz-sweep-B-100p-detailed/run_info.pickle',
        '/data/socrates/mx3/si-square-fixed-4x4-220x80x25-ls320-phi45-sin-50MHz-sweep-B-100p-detailed/run_info.pickle',
        ]

    run_indices = [
        11,
        21
        ]

    outputs = [
        'graph-10MHz-r11',
        'graph-50MHz-r21',
        ]

    for filename, run_index, out in zip(filenames, run_indices, outputs):
        G = load_graph(filename, variables, spp=100, skip=0, run_index=run_index)
        label_nodes(G, False, False)
        color_nodes(G)

        print(out + ".{pdf,svg,png}")
        write_dotfig(G, out + ".pdf")
        write_dotfig(G, out + ".svg")
        write_dotfig(G, out + ".png")

def fig_bitstream():
    plt.figure(figsize=(textwidth*0.7, textwidth*0.7*gr))

    filenames = [
        '/data/socrates/mx3/si-square-fixed-bitstream-220x80x25-ls320-phi45-sin-B_lo70-B_hi76-sweep-nbits/run_info.pickle',
        '/data/socrates/mx3/si-square-fixed-bitstream-220x80x25-ls320-phi45-sin-B_lo70-B_hi79-sweep-nbits/run_info.pickle',
        '/data/socrates/mx3/si-square-fixed-bitstream-220x80x25-ls320-phi45-sin-B_lo70-B_hi81-sweep-nbits/run_info.pickle',
        '/data/socrates/mx3/si-square-fixed-bitstream-220x80x25-ls320-phi45-sin-B_lo70-B_hi84-sweep-nbits/run_info.pickle',
        ]

    labels = [
        '$A_{hi}=76$ mT',
        '$A_{hi}=79$ mT',
        '$A_{hi}=81$ mT',
        '$A_{hi}=84$ mT',
        ]

    for filename, label in zip(filenames, labels):
        sp, sv, st = load_stats(filename, variables, 'final_count', spp=100, skip=0)
        plt.plot(sv, st, label=label)

    plt.plot(sv, 2**np.array(sv), label="$2^N$", color="black", ls='--')

    plt.xlabel('Number of bits $N$')
    plt.ylabel('Unique final states $S$')
    plt.legend()

    plt.tight_layout(pad=0)
    savefig("states-bitstream")

def fig_encoding():
    # plt.figure(figsize=(textwidth*0.7, textwidth*0.7*gr))

    B_lo = 0.050
    B_hi = 0.070
    bits = [0, 1, 0, 1]
    N = len(bits)
    spp = 1000
    t = np.linspace(0, N, N * spp)
    A = np.where(bits, B_hi, B_lo)
    A = np.repeat(A, spp)
    B = A * np.sin(2 * np.pi * t)

    plt.xlabel('Time')
    plt.ylabel('External field $B$')

    plt.yticks([-B_hi, -B_lo, 0, B_lo, B_hi], ['$-A_{hi}$', '$-A_{lo}$', '0', '$A_{lo}$', '$A_{hi}$'])
    plt.xticks(np.arange(N+1))
    plt.tick_params(axis='x', which='both', bottom='off', labelbottom='off')

    plt.grid(True, axis='x')
    plt.axhline(color='black', lw=0.75)

    plt.axhline(-B_hi, color='gray', lw=0.75, ls='dashed')
    plt.axhline(-B_lo, color='gray', lw=0.75, ls='dashed')
    plt.axhline( B_lo, color='gray', lw=0.75, ls='dashed')
    plt.axhline( B_hi, color='gray', lw=0.75, ls='dashed')


    colors = cycle(['gainsboro', 'whitesmoke'])
    for i, bit in enumerate(bits):
        t0 = t[spp * i]
        t1 = t[spp * (i + 1) - 1]
        plt.text(t0 + 0.45, B_hi*1.2, str(bit), {'fontsize': 'large', 'color': 'black' })
        plt.axvspan(i, i+1, color=next(colors))


    plt.plot(t, B)

    plt.tight_layout(pad=0)
    plt.subplots_adjust(top=0.9)
    savefig("encoding")
    plt.show()

if __name__ == '__main__':
    fig_states()
    fig_graphs()
    fig_bitstream()
    fig_encoding()
