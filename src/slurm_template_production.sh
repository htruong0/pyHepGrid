#!/bin/bash
#SBATCH -o {stdoutfile}
#SBATCH --array=1-{producRun}

cd {runcard_dir}
OMP_NUM_THREADS=1 ./NNLOJET -run {runcard} -iseed $((${{SLURM_ARRAY_TASK_ID}} + {baseSeed}))

exit 0