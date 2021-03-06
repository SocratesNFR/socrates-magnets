#!/bin/bash
#SBATCH --job-name=mumax3
#SBATCH --partition=EPIC
#SBATCH --time=24:00:00
#SBATCH --gres=gpu:2
#SBATCH --output={{job_script_dir}}/{{job_script_name}}.slurm-%j.out

# TODO: switch partition to EPICALL when EPIC2 is fixed
# TODO: use --gres=gpu:1 when queue system properly supports this

set -e

module purge
module load CUDA
module load Go
export GOPATH=$HOME

set -x

env

#mumax3 -gpu $GPU_DEVICE_ORDINAL {{jobs}}
mumax3 {{jobs}}

