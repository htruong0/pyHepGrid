#!/usr/bin/env python
import datetime
import os
import sys

import grid_functions as gf

try:
    dirac = os.environ["DIRAC"]
    sys.path.append(
        "{0}/Linux_x86_64_glibc-2.12/lib/python2.6/site-packages".format(dirac))
except KeyError:
    pass


# This function must always be the same as the one in program.py
def warmup_name(runcard, rname):
    out = runcard + ".tar.gz"
    return out


# This function must always be the same as the one in program.py
def output_name(runcard, rname, seed):
    out = "output-" + runcard + "-" + seed + ".tar.gz"
    return out


def parse_arguments():
    from optparse import OptionParser

    parser = OptionParser(usage="usage: %prog [options]")
    # example of a custom simplerun.py variable
    parser.add_option(
        "--executable_location", default="",
        help="GFAL path to executable tarball, relative to gfaldir.")
    parser.add_option(
        "--world", default="",
        help="which world to run on")
    parser.add_option(
        "--latin_hypercube", default="lhs",
        help="name of latin hypercube array")
    # parser.add_option(
    #     "--base_idx", default="",
    #     help="initial idx (seed) of submission")
    return gf.parse_arguments(parser)


def set_environment(lhapdf_dir):
    gf.set_default_environment(args)
    # LHAPDF
    os.environ['LHAPDF_DATA_PATH'] = lhapdf_dir
    return 0


# ------------------------- Download executable -------------------------
def download_program(source):
    tar_name = os.path.basename(source)
    if not tar_name.endswith("tar.gz"):
        gf.print_flush("{0} is not a valid path to download".format(source))
        return 1
    stat = gf.copy_from_grid(source, tar_name, args)
    stat += gf.untar_file(tar_name)
    stat += gf.do_shell("rm {0}".format(tar_name))
    if gf.DEBUG_LEVEL > 2:
        gf.do_shell("ls -l")
    return stat


def download_runcard(input_folder, runcard, runname):
    tar = warmup_name(runcard, runname)
    gf.print_flush("downloading "+input_folder+"/"+tar)
    stat = gf.copy_from_grid(input_folder+"/"+tar, tar, args)
    gf.print_flush("finished copying from grid storage... untarring now")
    stat += gf.untar_file(tar)
    return gf.do_shell("rm {0}".format(tar))+stat


def download_world(input_folder, world):
    world_file = world + ".hdf5"
    gf.print_flush("downloading " + input_folder + "/worlds/" + world_file)
    stat = gf.copy_from_grid(input_folder + "/worlds/" + world_file, world_file, args)
    return stat

def download_latin_hypercube(input_folder, latin_hypercube):
    lhs = latin_hypercube + ".npy"
    gf.print_flush("downloading " + input_folder + "/" + lhs)
    stat = gf.copy_from_grid(input_folder + "/" + lhs, lhs, args)
    return stat

# ------------------------- Actual run commands -------------------------
def activate_environment():
    os.system("wget -O JUNE/scripts/miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh")
    os.system("bash JUNE/scripts/miniconda.sh -b -p ./miniconda")
    os.system("echo Unpacking virtual environment")
    os.system("mkdir -p JUNE_env")
    os.system("tar -xzf JUNE/scripts/JUNE_env.tar.gz -C JUNE_env")
    return None


def deactivate_environment(args):
    gf.print_flush("Cleaning up environment...")
    os.system("source JUNE_env/bin/deactivate")
    os.system("rm -rf JUNE_env")
    os.system("rm -rf JUNE")
    os.system("rm -rf miniconda")
    if args.world is not "":
        os.system("rm {}.hdf5".format(args.world))
    return None


def run_example(args):
    status = gf.do_shell("chmod +x {0}".format(args.executable))
    if status == 0:
        activate_environment()
        os.system("echo Attempting to activate venv and run simulation...")
        status += gf.run_command("source JUNE_env/bin/activate && export PYTHONPATH=$PYTHONPATH:`pwd`/JUNE/ && ./{executable} --idx={idx} --world={world} --latin_hypercube={latin_hypercube} {runcard} {outfile}".format(
            executable=args.executable,
            idx=args.seed,
            world=args.world,
            latin_hypercube=args.latin_hypercube,
            runcard=args.runname,
            outfile="{0}.out".format(args.seed)))
    return status


# ------------------------- MAIN -------------------------
if __name__ == "__main__":
    # Generic startup:
    start_time = datetime.datetime.now()
    gf.print_flush("Start time: {0}".format(
        start_time.strftime("%d-%m-%Y %H:%M:%S")))

    args = parse_arguments()

    # lhapdf_local = ""
    # if args.use_cvmfs_lhapdf:
    #     lhapdf_local = args.cvmfs_lhapdf_location
    # set_environment(lhapdf_local)

    if gf.DEBUG_LEVEL > -1:
        # Architecture info
        gf.print_flush("Python version: {0}".format(sys.version))
        gf.print_node_info("node_info.log")

    if args.copy_log:
        # initialise with node name
        gf.do_shell("hostname >> {0}".format(gf.COPY_LOG))

    # Debug info
    if gf.DEBUG_LEVEL > 16:
        gf.do_shell("env")
        gf.do_shell("voms-proxy-info --all")

    gf.do_shell("hostname")

    setup_time = datetime.datetime.now()

    # Download executable:
    if not args.executable_location:
        # if path to executable not provided, exit with error.
        gf.print_flush("Executable location not specified")
        gf.DEBUG_LEVEL = 99999
        gf.end_program(status=1)

    status = download_program(args.executable_location)
    status += download_runcard(args.input_folder, args.runcard, args.runname)
    if args.world is not '':
        status += download_world(args.input_folder, args.world)
        status += download_latin_hypercube(args.input_folder, args.latin_hypercube)

    if status != 0:
        gf.print_flush("download failed")
        gf.end_program(status)

    download_time = datetime.datetime.now()
    
    gf.print_flush("executing executable...")
    status += run_example(args)

    if status != 0:
        gf.print_flush("Executable failed")
        gf.end_program(status)

    run_time = datetime.datetime.now()

    local_out = output_name(args.runcard, args.runname, args.seed)
    print(local_out)
    output_file = args.output_folder + "/" + local_out
    print(output_file)

    gf.print_file("setup time:       "+str(setup_time-start_time))
    gf.print_file("download time:    "+str(download_time-setup_time))
    gf.print_file("total runtime:    "+str(run_time-download_time))

    status += gf.tar_this(local_out, "*.log {rc}/results".format(rc=args.runname))

    status += gf.copy_to_grid(local_out, output_file, args)
    deactivate_environment(args)

    if gf.DEBUG_LEVEL > 1:
        gf.do_shell("ls")

    if status == 0:
        gf.print_flush("Copied over to grid storage!")

    tarcopy_time = datetime.datetime.now()
    gf.print_file("tar&copy time:    "+str(tarcopy_time-run_time))
    gf.print_file("total time:       "+str(tarcopy_time-setup_time))

    gf.end_program(status)
