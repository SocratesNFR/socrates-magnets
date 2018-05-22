#!/usr/bin/env python3
import os
import subprocess
import glob
from jinja2 import Template

def montage(output_file, input_files, labels=None):
    cmd = ['montage', '-background', 'black', '-fill', 'white']
    if labels:
        N = len(input_files)
        for i, l in zip(input_files, labels):
            cmd.extend(['-label', l, i])
    else:
        cmd.extend(input_files)
    cmd.append(output_file)

    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def gen_labels(input_files, fmt="{{i}}"):
    inds = [{'i': i} for i in range(len(input_files))]
    tpl = Template(fmt)
    return map(tpl.render, inds)

def montage_single(output_file, input_files, labels=True, label_template="{{i}}"):
    if labels:
        labels = gen_labels(input_files, label_template)

    print("montage {}".format(output_file))

    montage(output_file, input_files, labels)

def montage_dirs(output_dir, input_dirs, labels=True, label_template="{{i}}", glob_pattern='*.png'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    assert os.path.isdir(output_dir)

    first_dir = input_dirs[0]
    imgs = sorted(glob.glob(os.path.join(first_dir, glob_pattern)))
    for img in imgs:
        img = os.path.basename(img)
        input_files = [os.path.join(d, img) for d in input_dirs]
        output_file = os.path.join(output_dir, img)
        montage_single(output_file, input_files, labels, label_template)

def make_video(output_file, input_dir, img_pattern='m%06d.png'):
    cmd = ['ffmpeg',
           '-y',
           '-framerate', '24',
           '-i', os.path.join(input_dir, img_pattern),
           output_file]

    print("video {}".format(output_file))

    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(args):
    input_dirs = list(map(os.path.isdir, args.files))
    if all(input_dirs):
        # Multiple output images
        montage_dirs(args.output, args.files, args.labels, args.label_template)

        if args.video:
            make_video(args.video, args.output)

    elif not any(input_dirs):
        # Single output image
        montage_single(args.output, args.files, args.labels, args.label_template)
    else:
        print("ERROR: Can't mix directories and files as input")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='+',
                        help='list of input files or directories')
    parser.add_argument('-o', '--output', required=True,
            help='output file or directory')
    parser.add_argument('-m', '--video', help='make video')
    parser.add_argument('-l', '--labels', action='store_true', default=False,
            help='enable labels')
    parser.add_argument('-f', '--label-template', default='{{i}}',
            help='label template string')

    args = parser.parse_args()

    main(args)

