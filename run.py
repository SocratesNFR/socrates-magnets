#!/usr/bin/env python
import argparse
from mx3util import gen_job, run_local, run_dist, StoreKeyValue

def main(args):
    gen_job(args.template, args.out, **args.param)

    if args.run == 'local':
        run_local([args.out], interactive=args.interactive)

    elif args.run == 'dist':
        assert not args.interactive
        run_dist([args.out])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run mx3 job')
    parser.add_argument('-r', '--run', choices=['local', 'dist'], default='local',
                        help='run locally or distributed on a cluster')
    parser.add_argument('-i', '--interactive', action='store_true',
                        help='run mumax3 interactively')
    parser.add_argument('-p', '--param', action=StoreKeyValue, default={},
                        help='set template parameter key=value')
    parser.add_argument('template', help='job template')
    parser.add_argument('out', help='output job file')

    args = parser.parse_args()
    main(args)
