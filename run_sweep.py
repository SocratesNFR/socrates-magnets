#!/usr/bin/env python
import os
import time
import argparse
import re
import itertools
import pickle
import numpy as np
from collections import OrderedDict
from mx3util import gen_job, run_local, run_dist, StoreKeyValue

n_gpus_dist = 2

def func_bin(values):
    values = np.array(values, dtype=int)
    max_value = np.max(values)
    assert max_value >= 0, "Values must be unsigned"
    if max_value == 0:
        n_bits = 1
    else:
        n_bits = int(np.floor(np.log2(max_value)) + 1)
    fmt = '{:0' + str(n_bits) + 'b}' # ugh
    bits = list(map(fmt.format, values))
    return bits

funcs = {
    'bin': func_bin,
}

spec_globals = {
    'arange': np.arange,
    'linspace': np.linspace,
    'pow': np.power,
    'bin': func_bin,
}

def parse_spec(spec, ctx=None):
    return eval(spec, spec_globals, ctx)

def parse_sweep_spec(specs, ctx=None):
    sweep_spec = []
    for k, v in specs.items():
        sweep_spec.append([(k, vi) for vi in parse_spec(v, ctx)])
    return sweep_spec

def enumerate_sweep_spec(sweep_spec):
    return list(itertools.product(*sweep_spec))

def main(args):
    queue = []

    sweep_spec = parse_sweep_spec(args.sweep)
    sweep_list = enumerate_sweep_spec(sweep_spec)
    # print('sweep_spec', sweep_spec)
    # print('sweep_list', sweep_list)
    repeat = OrderedDict()
    if args.repeat_spec:
        repeat.update(args.repeat_spec)
    if args.repeat > 1 and 'repeat_index' not in repeat:
        repeat['repeat_index'] = 'range({})'.format(args.repeat)

    base, ext = os.path.splitext(os.path.basename(args.template))

    info = []

    if os.path.exists(args.outdir):
        print("WARNING: Path exists: {}".format(args.outdir))
    else:
        os.makedirs(args.outdir)

    repeat_specs = []
    repeat_lists = []

    for i, sweep_params in enumerate(sweep_list):
        params = dict(args.param)
        params.update(sweep_params)
        info.append([])

        repeat_spec = parse_sweep_spec(repeat, ctx=params)
        repeat_list = enumerate_sweep_spec(repeat_spec)
        # print('repeat_spec', repeat_spec)
        # print('repeat_list', repeat_list)
        repeat_specs.append(repeat_spec)
        repeat_lists.append(repeat_list)

        for j, repeat_params in enumerate(repeat_list):
            if len(repeat_list) > 1:
                outfile = "{}.{:06d}.{:06d}{}".format(base, i, j, ext)
            else:
                outfile = "{}.{:06d}{}".format(base, i, ext)
            params.update(repeat_params)
            out = os.path.join(args.outdir, outfile)
            gen_job(args.template, out, **params)
            queue.append(out)
            d = {'params': params, 'filename': outfile}
            info[-1].append(d)

    print("Generated {} jobs in {}".format(len(queue), args.outdir))

    info_filename = os.path.join(args.outdir, 'run_info.pickle')
    run_info = {
        'type': 'sweep',
        'args': args,
        'sweep_spec': sweep_spec,
        'sweep_list': sweep_list,
        'repeat': repeat,
        'repeat_specs': repeat_specs,
        'repeat_lists': repeat_lists,
        'run_info': info
    }
    with open(info_filename, 'wb') as f:
        pickle.dump(run_info, f)

    if args.run == 'local':
        run_local(queue)

    elif args.run == 'dist':
        # Submit jobs in chunks of n_gpus_dist
        procs = []
        while queue:
            jobs = queue[0:n_gpus_dist]
            del queue[0:n_gpus_dist]
            p = run_dist(jobs, wait=False)
            procs.append(p)

        # Wait for all jobs to finish
        while not all([p.poll() is not None for p in procs]):
            time.sleep(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run mx3 job')
    parser.add_argument('-r', '--run', choices=['local', 'dist', 'none'], default='local',
                        help='run locally or distributed on a cluster')
    parser.add_argument('-p', '--param', action=StoreKeyValue, default={},
                        help='set template parameter key=value')
    parser.add_argument('-s', '--sweep', action=StoreKeyValue, required=True, metavar='key=SPEC',
                        help='set sweep parameter key=SPEC')
    parser.add_argument('-n', '--repeat', type=int, default=1, metavar='N',
                        help='repeat each experiment N times (default: %(default)s)')
    parser.add_argument('-ns', '--repeat-spec', action=StoreKeyValue, metavar='key=SPEC',
                        help='repeat each according to key=SPEC')
    parser.add_argument('template', help='job template')
    parser.add_argument('outdir', help='output directory for job files')

    args = parser.parse_args()
    main(args)
