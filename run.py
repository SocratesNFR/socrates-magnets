#!/usr/bin/env python3
import argparse
from mx3util import gen_job, run_local

def main(args):
    gen_job(args.template, args.out, **args.param)
    if args.run == 'local':
        procs = run_local([args.out])

    elif args.run == 'dist':
        raise NotImplementedError('not yet implemented')

class StoreKeyValue(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        k, v = values.split('=')
        if getattr(namespace, self.dest) is None:
            setattr(namespace, self.dest, {})
        d = getattr(namespace, self.dest)
        d[k] = v

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run mx3 job')
    parser.add_argument('-r', '--run', choices=['local', 'dist'], default='local',
                        help='run locally or distributed on a cluster')
    parser.add_argument('-p', '--param', action=StoreKeyValue,
                        help='set template parameter key=value')
    parser.add_argument('template', help='job template')
    parser.add_argument('out', help='output job file')

    args = parser.parse_args()
    main(args)
