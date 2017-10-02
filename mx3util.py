import copy
import subprocess
import os
import argparse
try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'w')

class Template(object):
    def __init__(self, template, params={}):
        self.template = template
        self.params = dict(params)

    def generate(self, **kwargs):
        tpl = open(self.template).read()

        params = copy.deepcopy(self.params)
        params.update(kwargs)

        mx3 = tpl.format(**params)

        return mx3

    def write(self, filename, **kwargs):
        mx3 = self.generate(**kwargs)
        with open(filename, 'w') as f:
            f.write(mx3)

def gen_job(template, outfile, **params):
    tpl = Template(template, params)
    tpl.write(outfile)

def run_local(jobs, wait=True, quiet=False):
    cmd = ['mumax3']
    # mumax3 can handle and queue multiple jobs
    cmd.extend(jobs)
    if quiet:
        p = subprocess.Popen(cmd, stdout=DEVNULL, stderr=DEVNULL)
    else:
        p = subprocess.Popen(cmd)

    if wait:
        p.wait()

    return p

DEFAULT_JOB_SCRIPT_TEMPLATE = os.path.join(
        os.path.dirname(__file__),
        "templates/mumax3.pbs.sh")

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

    tpl = Template(job_script_template)
    tpl.write(job_script, jobs=jobs_param, job_script_dir=job_script_dir)

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
            setattr(namespace, self.dest, {})
        d = getattr(namespace, self.dest)
        d[k] = v
