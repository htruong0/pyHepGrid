#!/bin/bash
#SBATCH -o {stdoutfile}

cd {runcard_dir}
OMP_NUM_THREADS={threads} ./NNLOJET -run {runcard}

exit 0