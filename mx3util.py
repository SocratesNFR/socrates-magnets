import copy
import subprocess
import os
import argparse

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

def run_local(jobs, wait=True):
    procs = []
    for i, job in enumerate(jobs):
        cmd = ['mumax3', '-gpu', str(i), job]
        print("run_local:", cmd)
        p = subprocess.Popen(cmd)
        procs.append(p)

    if wait:
        for p in procs:
            p.wait()

    return procs

def run_dist(jobs, wait=True, job_script_template="templates/mumax3.pbs.sh"):
    #
    # Generate job script
    #
    commands = []
    for i, job in enumerate(jobs):
        cmd = "mumax3 -gpu {} {} &".format(i, job)
        commands.append(cmd)
    commands = "\n".join(commands)

    # Put job script in same directory as first jobs file
    job_script_dir = os.path.dirname(jobs[0])

    # Name job script as concatenation of job names
    job_names = [os.path.splitext(os.path.basename(job))[0] for job in jobs]
    job_script_name = "__".join(job_names) + ".pbs.sh"

    job_script = os.path.join(job_script_dir, job_script_name)

    tpl = Template(job_script_template)
    tpl.write(job_script, commands=commands)

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
