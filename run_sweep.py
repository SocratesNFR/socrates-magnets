#!/usr/bin/env python
import os
import time
import argparse
from mx3util import gen_job, run_local, run_dist, StoreKeyValue
import numpy as np

n_gpus_dist = 2

def params_iter():
    for f in np.linspace(1e9, 1e8, 10):
        yield {'B': 83e-3, 'f': f, 'pst': '0.0'}

def main(args):
    queue = []

    for i, params in enumerate(params_iter()):
        base, ext = os.path.splitext(os.path.basename(args.template))
        outfile = "{}.{:03d}{}".format(base, i, ext)
        out = os.path.join(args.outdir, outfile)
        gen_job(args.template, out, **params)
        queue.append(out)

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
    parser.add_argument('-r', '--run', choices=['local', 'dist'], default='local',
                        help='run locally or distributed on a cluster')
    parser.add_argument('-p', '--param', action=StoreKeyValue,
                        help='set template parameter key=value')
    parser.add_argument('template', help='job template')
    parser.add_argument('outdir', help='output directory for job files')

    args = parser.parse_args()
    main(args)
