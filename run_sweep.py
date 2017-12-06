#!/usr/bin/env python
import os
import time
import argparse
import re
import itertools
import pickle
import numpy as np
from mx3util import gen_job, run_local, run_dist, StoreKeyValue

n_gpus_dist = 2

def parse_sweep_spec(spec):
    # start:stop:step = arange
    if ':' in spec:
        m = re.match('(.*):(.*):(.*)', spec)
        if not m:
            raise ValueError("Expected start:stop:step for arange")
        start, stop, step = map(float, m.groups())
        return np.arange(start, stop, step)

    # [start,stop,num] = linspace
    if spec.startswith('['):
        m = re.match('\[(.*),(.*),(.*)\]', spec)
        if not m:
            raise ValueError("Expected [start,stop,num] for linspace")
        start, stop, num = map(float, m.groups())
        return np.linspace(start, stop, num)

    # a,b,c,... = list
    if ',' in spec:
        values = re.split(',', spec)
        return values

    raise ValueError("Invalid sweep spec", spec)


def main(args):
    queue = []

    sweep_spec = []
    for k, v in args.sweep.items():
        sweep_spec.append([(k, vi) for vi in parse_sweep_spec(v)])
    # print(sweep_spec)
    sweep_list = list(itertools.product(*sweep_spec))

    base, ext = os.path.splitext(os.path.basename(args.template))

    info = []

    for i, sweep_params in enumerate(sweep_list):
        params = dict(args.param)
        params.update(sweep_params)
        info.append([])
        print("{:03d}: {}".format(i, params))
        for j in range(args.repeat):
            if args.repeat > 1:
                outfile = "{}.{:03d}.{:03d}{}".format(base, i, j, ext)
            else:
                outfile = "{}.{:03d}{}".format(base, i, ext)
            out = os.path.join(args.outdir, outfile)
            print(out)
            gen_job(args.template, out, **params)
            queue.append(out)
            d = {'params': params, 'filename': outfile}
            info[-1].append(d)

    info_filename = os.path.join(args.outdir, 'run_info.pickle')
    run_info = {
        'type': 'sweep',
        'args': args,
        'sweep_spec': sweep_spec,
        'sweep_list': sweep_list,
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
    parser.add_argument('-s', '--sweep', action=StoreKeyValue, required=True,
                        help='set sweep parameter key=SPEC')
    parser.add_argument('-n', '--repeat', type=int, default=1, metavar='N',
                        help='repeat each experiment N times (default: %(default)s)')
    parser.add_argument('template', help='job template')
    parser.add_argument('outdir', help='output directory for job files')

    args = parser.parse_args()
    main(args)
