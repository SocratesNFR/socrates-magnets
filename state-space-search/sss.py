#!/usr/bin/env python3
import sys
import os
import copy
import numpy as np
import time


def bit_array(x, n_bits):
    """ Convert number x to array of bits """
    return np.array([(x & (1 << bit)) >> bit for bit in range(n_bits)])

def array_bit(a):
    """ Convert bit array a to number """
    return sum([(b << bit) for (bit, b) in enumerate(a)])


"""
def mx3_status():
    # Look in jobs directory for any mx3 files that haven't been completed
    ls = set(os.listdir(MX3_OUTDIR))
    n_total, n_running, n_completed = 0, 0, 0
    for f in ls:
        base, ext = os.path.splitext(f)
        if ext == ".mx3":
            n_total += 1

            # look for exitstatus file in .out directory
            done_file = os.path.join(MX3_OUTDIR, base + ".out", "exitstatus")
            if os.path.exists(done_file):
                n_completed += 1
            else:
                n_running += 1

    return n_total, n_running, n_completed
"""

class MX3Generator(object):
    def __init__(self, template, params):
        self.template = template
        self.params = dict(params)

    def generate(self, **kwargs):
        tpl = open(self.template).read()

        params = copy.deepcopy(self.params)
        params.update(kwargs)

        mx3 = tpl.format(**params)

        return mx3


"""
1. Generate jobs
2. Wait for their completion
3. Analyze results
4. Exit when done
"""
class StateSpaceSearch(object):

    def __init__(self, template, initial, params, outdir):
        self.queue = [initial]
        self.running = []
        self.finished = []
        self.edgelist = []

        self.template = template
        self.mx3gen = MX3Generator(template, params)
        self.outdir = outdir

        root, ext = os.path.splitext(os.path.basename(template))
        self.outfile = root + "_%d" + ext

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

        mx3 = self.mx3gen.generate(**params)

        with open(filename, 'w') as f:
            f.write(mx3)

    def get_jobdir(self, config):
        base, _ = os.path.splitext(self.get_outfile(config))
        jobdir = os.path.join(self.outdir, base + ".out")
        return jobdir

    def analyze_job(self, config, jobdir):
        print("analyze_job", config, jobdir)

        tablefile = os.path.join(jobdir, "table.txt")
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
            jobdir = self.get_jobdir(config)
            done_file = os.path.join(jobdir, "exitstatus")
            if os.path.exists(done_file):
                self.running.remove(config)
                self.finished.append(config)
                self.analyze_job(config, jobdir)

        print("poll queued={} running={} finished={}".format(self.queue, self.running, self.finished))

        time.sleep(interval)

    def run(self):
        while self.queue or self.running:
            while self.queue:
                config = self.queue.pop(0)
                self.running.append(config)
                self.gen_job(config)

            self.poll()

        self.write_edgelist("edgelist.txt")


def main():
    # TODO: Add argparse
    params = {
            "phiMax": "360 * pi / 180",
            "phiStep": "45 * pi / 180",
    }

    sss = StateSpaceSearch("templates/si3x3.mx3", 0xfff, params, "jobs/joh")
    sss.run()

if __name__ == '__main__':
    main()
