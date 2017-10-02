#!/usr/bin/env python
import sys
import os
import time
import argparse
import numpy as np
from mx3util import gen_job, run_local, run_dist, StoreKeyValue, Template


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
        self.tpl = Template(template, params)
        self.outdir = outdir

        root, ext = os.path.splitext(os.path.basename(template))
        self.outfile = root + "_%d" + ext

        self.runtype = runtype

    def get_outfile(self, config):
        return self.outfile % (config)

    def gen_job(self, config):
        filename = self.get_outfile(config)
        filename = os.path.join(self.outdir, filename)

        print("gen_job: {}".format(filename))

        params = {}
        config_array = bit_array(config, 12)

        for i, bit in enumerate(config_array):
            k = "mi{}".format(i+1)
            params[k] = -1 + bit * 2

        self.tpl.write(filename, **params)

        return filename

    def get_jobdir(self, config):
        base, _ = os.path.splitext(self.get_outfile(config))
        jobdir = os.path.join(self.outdir, base + ".out")
        return jobdir

    def analyze_job(self, config, jobdir):
        print("analyze_job", config, jobdir)

        tablefile = os.path.join(jobdir, "table.txt")
        while not os.path.exists(tablefile):
            print("waiting for {}...".format(jobdir))
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

        print("states=", states)

        states = list(map(array_bit, states))

        print("states=", states)

        for s in states:
            if s not in self.finished and s not in self.queue and s not in self.running:
                print("new state:", s)
                self.queue.append(s)

        # Update edgelist
        for s, phi in zip(states, phis):
            self.edgelist.append((config, s, phi))

    def write_edgelist(self, filename):
        print("write_edgelist", filename)

        f = open(filename, 'w')
        for n1, n2, phi in self.edgelist:
            f.write("{} {} {}\r\n".format(n1, n2, phi))
        f.close()

    def poll(self, interval=1):
        # Look for completed jobs, iterating over a copy of the running list
        for config in list(self.running):
            if self.procs[config].poll() is None:
                # Not finished yet
                continue

            jobdir = self.get_jobdir(config)
            self.running.remove(config)
            self.finished.append(config)
            self.analyze_job(config, jobdir)

        print("poll queued={} running={} finished={}".format(self.queue, self.running, self.finished))

        time.sleep(interval)

    def dequeue(self, n):
        configs = self.queue[0:n]
        del self.queue[0:n]
        return configs

    def run(self):
        while self.queue or self.running:
            while self.queue:
                configs = self.dequeue(self.ngpus)
                self.running.extend(configs)

                jobs = []
                for config in configs:
                    job = self.gen_job(config)
                    jobs.append(job)

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

        print("Finished!")
        # TODO: runtime
        print("{} states discovered:".format(len(self.finished)))
        print(" ".join(map(str, self.finished)))



def main(args):
    # Default params
    params = {
            "phiMax": "360 * pi / 180",
            "phiStep": "45 * pi / 180",
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
