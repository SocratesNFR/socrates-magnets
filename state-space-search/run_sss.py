#!/usr/bin/env python
import sys
import os
import time
import datetime
import argparse
import numpy as np
from mx3util import gen_job, run_local, run_dist, StoreKeyValue


def bit_array(x, n_bits):
    """ Convert number x to array of bits """
    return np.array([(x & (1 << bit)) >> bit for bit in range(n_bits)])

def array_bit(a):
    """ Convert bit array a to number """
    return sum([(b << bit) for (bit, b) in enumerate(a)])


"""
1. Generate jobs
2. Wait for their completion
3. Analyze results
4. Exit when done
"""
class StateSpaceSearch(object):

    def __init__(self, template, initial, params, outdir, runtype='local', ngpus=2):
        self.queue = [initial]
        self.running = []
        self.finished = []
        self.edgelist = []
        self.procs = {}

        self.ngpus = ngpus
        if runtype == 'local':
            self.ngpus = 1

        self.template = template
        self.params = params
        self.outdir = outdir

        root, ext = os.path.splitext(os.path.basename(template))
        self.outfile = root + "_%d" + ext

        self.runtype = runtype

    def get_outfile(self, config):
        return self.outfile % (config)

    def gen_job(self, config):
        filename = self.get_outfile(config)
        filename = os.path.join(self.outdir, filename)

        params = dict(self.params) # copy
        config_array = bit_array(config, 12)

        for i, bit in enumerate(config_array):
            k = "mi{}".format(i+1)
            params[k] = -1 + bit * 2

        gen_job(self.template, filename, **params)

        return filename

    def get_jobdir(self, config):
        base, _ = os.path.splitext(self.get_outfile(config))
        jobdir = os.path.join(self.outdir, base + ".out")
        return jobdir

    def analyze_job(self, config, jobdir):
        print("Analyzing job: {}".format(jobdir))

        tablefile = os.path.join(jobdir, "table.txt")
        while not os.path.exists(tablefile):
            print("Waiting for {}...".format(tablefile))
            time.sleep(1)

        table = np.loadtxt(tablefile)

        # x components for horizontal nanomagnets
        horiz = table[:,4:20:3]

        # y components for vertical nanomagnets
        vert = table[:,23:40:3]

        # angles
        phis = table[:,-1]

        # Convert state vectors to number
        states = np.concatenate([horiz, vert], axis=1)
        states = np.round(states)
        states[states < 0] = 0
        states = states.astype(int)

        states = list(map(array_bit, states))

        print("State {} -> {}".format(config, np.unique(states)))

        for s in states:
            if s not in self.finished and s not in self.queue and s not in self.running:
                print("New state: {}".format(s))
                self.queue.append(s)

        # Update edgelist
        for s, phi in zip(states, phis):
            self.edgelist.append((config, s, phi))

    def write_edgelist(self, filename):
        print("Writing edgelist to {}".format(filename))

        f = open(filename, 'w')
        for n1, n2, phi in self.edgelist:
            f.write("{} {} {}\r\n".format(n1, n2, phi))
        f.close()

    prev_s = ""
    def print_new(self, s):
        if s != self.prev_s:
            print(s)
            self.prev_s = s

    def poll(self, interval=1):
        # Look for completed jobs, iterating over a copy of the running list
        for config in list(self.running):
            if self.procs[config].poll() is None:
                # Not finished yet
                continue

            jobdir = self.get_jobdir(config)
            self.running.remove(config)
            self.finished.append(config)

            print("Job finished: {}".format(jobdir))

            self.analyze_job(config, jobdir)

        self.print_new("Poll: {} queued, {} running, {} finished".format(
            len(self.queue), len(self.running), len(self.finished)))

        time.sleep(interval)

    def dequeue(self, n):
        configs = self.queue[0:n]
        del self.queue[0:n]
        return configs

    def run(self):
        t0 = time.time()
        print("Started on {}".format(time.asctime()))

        while self.queue or self.running:
            while self.queue:
                configs = self.dequeue(self.ngpus)
                self.running.extend(configs)

                jobs = []
                for config in configs:
                    job = self.gen_job(config)
                    jobs.append(job)

                print("Starting jobs: {}".format(" ".join(jobs)))

                if self.runtype == 'local':
                    p = run_local(jobs, wait=True, quiet=True)
                else:
                    p = run_dist(jobs, wait=False)

                for config in configs:
                    self.procs[config] = p

            self.poll()

        base, _ = os.path.splitext(os.path.basename(self.template))
        filename = os.path.join(self.outdir, base + "-edgelist.txt")
        self.write_edgelist(filename)

        t1 = time.time()
        dt = t1 - t0
        delta = datetime.timedelta(seconds=dt)

        print("Completed on {}".format(time.asctime()))
        print("Duration: {}".format(delta))
        print("{} states found".format(len(self.finished)))
        print("See {} for details".format(filename))



def main(args):
    # Default params
    params = {
            "phiMax": "360",
            "phiStep": "1",
            "pst": "0.0",
    }

    if args.param:
        params.update(args.param)

    sss = StateSpaceSearch(args.template, args.initial, params, args.outdir, args.run, args.ngpus)
    sss.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run mx3 job')
    parser.add_argument('-r', '--run', choices=['local', 'dist'], default='local',
                        help='run locally or distributed on a cluster')
    parser.add_argument('-n', '--ngpus', type=int, default=2,
                        help='number of gpus available on each node')
    parser.add_argument('-p', '--param', action=StoreKeyValue,
                        help='set template parameter key=value')
    parser.add_argument('-i', '--initial', metavar='N', type=int, default=0xfff,
            help='initial configuration (default: 0x%(default)x)')
    parser.add_argument('template', help='job template')
    parser.add_argument('outdir', help='output directory for job files')

    args = parser.parse_args()
    main(args)
