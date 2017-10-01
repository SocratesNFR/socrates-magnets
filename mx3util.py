import copy
import subprocess

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

    def write(self, filename, **kwargs):
        mx3 = self.generate(**kwargs)
        with open(filename, 'w') as f:
            f.write(mx3)

def gen_job(template, outfile, **params):
    mx3gen = MX3Generator(template, params)
    mx3gen.write(outfile)

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

def run_dist(jobs):
    # generate job script
    # submit job
    # (optionally) wait for completion
    raise NotImplementedError()
