import copy
import subprocess
import os
import argparse
import re
import fnmatch
import pickle
import numpy as np
from collections import OrderedDict
from jinja2 import Environment, FileSystemLoader, StrictUndefined
try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'w')

TEMPLATES_PATH = ['templates', '.']
DEFAULT_JOB_SCRIPT_TEMPLATE = 'mumax3.pbs.sh'


def get_template(template):
    loader = FileSystemLoader(TEMPLATES_PATH)
    env = Environment(loader=loader, trim_blocks=True, undefined=StrictUndefined)
    return env.get_template(template)

def gen_job(template, outfile, **params):
    tpl = get_template(template)
    mx3 = tpl.render(**params)
    with open(outfile, 'w') as f:
        f.write(mx3)

def run_local(jobs, wait=True, quiet=False, interactive=False):
    cmd = ['mumax3']
    if interactive:
        cmd.append('-i')
    # mumax3 can handle and queue multiple jobs
    cmd.extend(jobs)
    if quiet:
        p = subprocess.Popen(cmd, stdout=DEVNULL, stderr=DEVNULL)
    else:
        p = subprocess.Popen(cmd)

    if wait:
        p.wait()

    return p

def run_dist(jobs, wait=True, job_script_template=DEFAULT_JOB_SCRIPT_TEMPLATE):
    #
    # Generate job script
    #
    # Put job script in same directory as first jobs file
    job_script_dir = os.path.dirname(jobs[0])

    # Name job script as concatenation of job names
    job_names = [os.path.splitext(os.path.basename(job))[0] for job in jobs]
    job_script_name = "__".join(job_names) + ".pbs.sh"

    job_script = os.path.join(job_script_dir, job_script_name)
    jobs_param = " ".join(jobs)

    gen_job(job_script_template, job_script, jobs=jobs_param, job_script_dir=job_script_dir)

    #
    # Submit job
    #
    qsub = ['qsub', '-Wblock=true', job_script]
    p = subprocess.Popen(qsub)

    if wait:
        p.wait()

    return p

class StoreKeyValue(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        k, v = values.split('=')
        if getattr(namespace, self.dest) is None:
            setattr(namespace, self.dest, OrderedDict())
        d = getattr(namespace, self.dest)
        d[k] = v

def parse_table_header(filename):
    r = re.compile('(\S+) \((\S*)\)')
    with open(filename) as f:
        l = f.readline()
        l = l.strip('# \n')
        head = l.split('\t')
        head = [r.match(h).groups() for h in head]
        headers = [h[0] for h in head]
        units = [h[1] for h in head]
        # indices = OrderedDict([(headers[i], i) for i in range(len(headers))])
        # return indices
        return headers, units


def load_table(filename, columns=None):
    cols = None

    if columns:
        headers, units = parse_table_header(filename)
        vmap = dict(zip(headers, range(len(headers))))
        cols = []
        for v in columns:
            cols.append(vmap[v])

    return np.loadtxt(filename, usecols=cols)


def match_vars(patterns, variables):
    var = []
    for v in patterns:
        if v in variables:
            var.append(v)
        elif v + "x" in variables:
            var.append(v + "x")
            var.append(v + "y")
            var.append(v + "z")
        else:
            matches = fnmatch.filter(variables, v)
            if matches:
                var.extend(matches)
            else:
                raise IndexError(v)
    return var

def bit_array(x, n_bits):
    """ Convert number x to array of bits """
    return np.array([(x & (1 << bit)) >> bit for bit in range(n_bits)])

def array_bit(a):
    """ Convert bit array a to number """
    return sum([(b << bit) for (bit, b) in enumerate(a)])

def poincare(X, step, skip=10):
    step = int(step)
    skip = int(skip * step)
    return X[skip::step]

def digitize(X, threshold=0):
    return np.where(X > threshold, 1, 0)

def load_run_info(filename):
    return pickle.load(open(filename, "rb"), encoding='latin1')

def get_tablefile(mx3_filename):
    base, _ = os.path.splitext(mx3_filename)
    # print("base", base)
    # basedir = os.path.dirname(mx3_filename)
    # outdir = os.path.join(basedir, base + ".out")
    outdir = base + ".out"
    tablefile = os.path.join(outdir, "table.txt")
    return tablefile

class RunInfo(object):
    def __init__(self, filename, load=False):
        self.filename = filename
        self.info = {}
        if load:
            self.load()

    def load(self):
        self.info = load_run_info(self.filename)

    def save(self):
        with open(self.filename, 'wb') as f:
            pickle.dump(self.info, f)

    def __getitem__(self, i):
        return self.info[i]

    @property
    def basedir(self):
        return os.path.dirname(self.filename)

    @property
    def run_info(self):
        return self.info['run_info']

    @property
    def run_count(self):
        return len(self.run_info)

    def repeat_count(self, run_index):
        return len(self.run_info[run_index])

    def repeat_counts(self):
        return list(map(len, self.run_info))

    def get_mx3_filename(self, run_index, repeat_index):
        return os.path.join(self.basedir, self.run_info[run_index][repeat_index]['filename'])

    def get_table_filename(self, run_index, repeat_index):
        return get_tablefile(self.get_mx3_filename(run_index, repeat_index))

    def get_header(self, run_index=0, repeat_index=0):
        tablefile = self.get_table_filename(run_index, repeat_index)
        headers, _ = parse_table_header(tablefile)
        return headers

    def load_table(self, run_index, repeat_index, columns=None):
        tablefile = self.get_table_filename(run_index, repeat_index)
        return load_table(tablefile, columns)
