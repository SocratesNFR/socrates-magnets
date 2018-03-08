#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import pickle
import numpy as np
import matplotlib.pyplot as plt

from states import load_stats
# from mx3util import *

plt.style.use('publish')

textwidth = 7 # 7in
gr = (np.sqrt(5)-1.0)/2.0 # golden ratio

variables = ['m.region{}x'.format(i) for i in range(1,41,2)] + \
            ['m.region{}y'.format(i) for i in range(2,41,2)]

def savefig(basename):
    print(basename + ".{pdf,svg,png}")
    plt.tight_layout(pad=0)
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
        sp, sv, st = load_stats(filename, variables, 'state_count', spp=100, skip=0)
        plt.plot(sv, st, label=label)

    plt.xlabel('Field strength $A$')
    plt.ylabel('Unique states $S$')
    plt.legend()

    savefig("states")

def fig_bitstream():
    plt.figure(figsize=(textwidth*0.7, textwidth*0.7*gr))

    filenames = [
        '/data/socrates/mx3/si-square-fixed-bitstream-220x80x25-ls320-phi45-sin-B_lo0-B_hi70-sweep-nbits/run_info.pickle',
        '/data/socrates/mx3/si-square-fixed-bitstream-220x80x25-ls320-phi45-sin-B_lo0-B_hi76-sweep-nbits/run_info.pickle',
        '/data/socrates/mx3/si-square-fixed-bitstream-220x80x25-ls320-phi45-sin-B_lo0-B_hi79-sweep-nbits/run_info.pickle',
        '/data/socrates/mx3/si-square-fixed-bitstream-220x80x25-ls320-phi45-sin-B_lo0-B_hi81-sweep-nbits/run_info.pickle',
        ]

    labels = [
        '$A_{hi}=0.070$',
        '$A_{hi}=0.076$',
        '$A_{hi}=0.079$',
        '$A_{hi}=0.081$',
        ]

    for filename, label in zip(filenames, labels):
        sp, sv, st = load_stats(filename, variables, 'final_count', spp=100, skip=0)
        plt.plot(sv, st, label=label)

    plt.plot(sv, 2**np.array(sv), label="$2^N$", color="black")

    plt.xlabel('Number of bits $N$')
    plt.ylabel('Unique final states $S$')
    plt.legend()

    savefig("states-bitstream")


if __name__ == '__main__':
    fig_states()
    fig_bitstream()
