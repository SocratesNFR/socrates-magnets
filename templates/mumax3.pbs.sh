#!/bin/bash
#PBS -N mumax3
#PBS -q epic
#PBS -l walltime=24:00:00
#PBS -l select=1:ncpus=36
#PBS -o {{job_script_dir}}
#PBS -e {{job_script_dir}}

set -e

module load Go
export GOPATH=$HOME
export PATH=$PATH:/usr/local/cuda-8.0/bin

cd $PBS_O_WORKDIR

mumax3 {{jobs}}

