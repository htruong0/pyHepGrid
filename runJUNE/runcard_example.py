import pyHepGrid.src.dbapi as dbapi
import os

print("Sourcing runcard")
dictCard = {
    # folder       :   config file / runcard
    "june": "JUNE"
}
# for the example, keep everything in 'example' folder.
juneDir = os.path.dirname(os.path.realpath(__file__))

# Run Variables

# run-specific variables (overrides header.py variables)
runcardDir = juneDir
# number of concurrent jobs to submit
producRun = 1
# ARC jobname to appear in squeue output
jobName = "JUNE"
count = 8 # number of cores
countpernode = 8

# ARC's jobs database: put this wherever you want
arcbase = os.path.expanduser("~/.arc/jobs.dat")
# pyHepGrid SQL database
dbname = F"{juneDir}/ARCdb_JUNE.dat"


# user-specific global variables (could go in user's header)
copy_log = True

# automatically pick next unused seed
# baseSeed = dbapi.get_next_seed(dbname=dbname) + 1
baseSeed = 0  # (setting seed manually)

# Project-level Variables

# Your custom subclass of `ProgramInterface` class in
# "src/pyHepGrid/src/program_interface.py"
# import should be relative to this runcard
runmode = "backend_example.ExampleProgram"

runfile = juneDir+"/simplerun.py"

world_list = ["test_world"]
world = "test_world"

# path to your executable: src_dir/exe
executable_src_dir = juneDir
if 'world' not in globals():
    executable_exe = "run_script.py"
else:
    executable_exe = "run_script_world.py"

grid_input_dir = "JUNE/input"
grid_output_dir = "JUNE/output"
# grid_warmup_dir = "example/warmup" # not used

provided_warmup_dir = runcardDir

# Path to executable on gfal (non-standard/custom setting)
grid_executable = "JUNE/executable.tar.gz"

# User Variables

# your DIRAC username: only needed if you run on DIRAC.
# dirac_name = "your.username"

# custom post-run local download (and processing) script
# finalisation_script = "path/to/your/script.py"
