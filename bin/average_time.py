#!/usr/bin/env python3
from __future__ import division, print_function
import os
import sys
import argparse as ap
import importlib
import numpy as np
np.warnings.filterwarnings('ignore')
# Janky af, but allows script to be called from other directories
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from pyHepGrid.src.header import production_base_dir as rootdir  # noqa: E40
import pyHepGrid.src.gnuplot  # noqa: E40

partdirs = ["LO", "V", "R", "VV", "RV", "RRa", "RRb"]


def get_time_hrs(f):
    for line in f.readlines():
        if "Elapsed" in str(line):
            val, unit = line.split()[-2:]
            val = float(val)
            unit = str(unit)
            if "minutes" in unit:
                val = val/60
            elif "second" in unit:
                val = val/3600
            # print(val, unit)
            return val
    return None


def add_runcard_directories(args):
    runcard_loc = os.path.join(os.getcwd(), args.runcard)
    runcard_dir, runcard_name = os.path.split(runcard_loc)
    sys.path = [runcard_dir]+sys.path
    import_name = runcard_name.replace(".py", "")
    runcard_import = importlib.import_module(import_name)
    finalise = importlib.import_module("finalise")
    for runcard in runcard_import.dictCard:
        direc = finalise.get_output_dir_name(
            runcard)+"-{0}/log".format(runcard_import.dictCard[runcard])
        args.directories.append(direc)
    return args


def compile_time_info(directory):
    times = []
    skip_count = 0
    total_runs = 0
    for infile in os.listdir(directory):
        if infile.endswith(".log"):
            total_runs += 1
            full_infile = os.path.join(directory, infile)
            with open(full_infile, 'rb') as f:
                time_data = get_time_hrs(f)
            try:
                if time_data >= 0:
                    times.append(float(time_data))
                else:
                    skip_count += 1
            except (TypeError, ValueError):
                skip_count += 1
    times = np.array(times)
    return times, skip_count, total_runs


def print_full_output(directory, times, skip_count, total_runs, histogram):
    times = np.array(times)
    mean = np.mean(times)
    stdev = np.std(times)
    tot = np.sum(times)
    try:
        long_run = np.max(times)
        short_run = np.min(times)
    except ValueError:
        long_run = 0
        short_run = 0

    hr = " hrs"
    print("Input directory:    {0}".format(directory))

    print("=================================")
    print("Total time:         {0:<8.1f} {1}".format(tot, hr))
    print("Total no. runs:     {0:<8}".format(total_runs))
    print("No. +ve time runs:  {0:<8}".format(len(times)))
#    print("No. -ve time runs:  {0:<8}".format(skip_count))
    print("---------------------------------")
    print("Longest Run:        {0:<8.4f} {1}".format(long_run, hr))
    print("Shortest run:       {0:<8.4f} {1}".format(short_run, hr))
    print("Mean time:          {0:<8.4f} {1}".format(mean, hr))
    print("Standard Deviation: {0:<8.4f} {1}".format(stdev, hr))
    print("=================================")
    if histogram:
        y, x = np.histogram(times, bins=range(0, 72))
        x = (x[:-1]+x[1:])/2
        last_nonzero_index = None
        for idx, item in enumerate(y):
            if item != 0:
                last_nonzero_index = idx
        x = x[:last_nonzero_index+1]
        y = y[:last_nonzero_index+1]
        pyHepGrid.src.gnuplot.do_plot(x, y, xlabel="No. hours",
                                      title="Run time histogram")


def print_short_header():
    header = "{1:55} {0:17}      {2:17}".format(
        "Average time", "Runcard", "Total time")
    print(header)
    print("="*len(header))


def print_short_output(directory, times, skip_count, total_runs):
    times = np.array(times)
    tot = np.sum(times)
    mean = np.mean(times)
    stdev = np.std(times)
    directory = directory.split(
        "/")[-2].replace("results_", "").split(".run-")[0]
    hr = " hrs"
    print(
        "{4:55} {0:<5.2f} +/- {1:<5.2f} {2}   {5:<5.2f} {2} [{3} runs]".format(
            mean, stdev, hr, len(times), directory, tot))


def do_search(args, path):
    if args.search is not None:
        for searchstr in args.search:
            if args.case_insensitive:
                if searchstr.lower() not in path.lower():
                    return False
            else:
                if searchstr not in path:
                    return False
    return True


def do_reject(args, path):
    if args.reject is not None:
        for rejectstr in args.reject:
            if args.case_insensitive:
                if rejectstr.lower() in path.lower():
                    return False
            else:
                if rejectstr in path:
                    return False
    return True


def search_matches_path(args, path):
    if any(not i(args, path) for i in [do_search, do_reject]):
        return False
    return True


def get_dirs():
    dirs = []
    for thing in os.listdir(rootdir):
        fullpath = os.path.join(rootdir, thing)
        if thing in partdirs and os.path.isdir(fullpath):
            for subthing in os.listdir(fullpath):
                fullsubpath = os.path.join(fullpath, subthing)
                if search_matches_path(args, fullsubpath):
                    logpath = "{}/log".format(fullsubpath)
                    if os.path.isdir(logpath):
                        dirs.append(logpath)
        elif os.path.isdir(fullpath):
            if search_matches_path(args, fullpath):
                logpath = "{}/log".format(fullpath)
                if os.path.isdir(logpath):
                    dirs.append(logpath)
    return dirs


if __name__ == "__main__":
    parser = ap.ArgumentParser(description="Generate timing information from a "
                                           "directory of log files.")
    parser.add_argument('directories', metavar='dir',
                        help='Directories to search.',
                        nargs="*")
    parser.add_argument('--runcard', '-rc',
                        help='runcard.py file to use.')
    parser.add_argument('--verbose', '-v',
                        help='Outputs a much longer summary.',
                        action="store_true")
    parser.add_argument('--search', '-f', '-s',
                        help='search for specific string(s) in runcard dir.',
                        nargs='+')
    parser.add_argument('--reject', '-r',
                        help='reject specific string(s) in runcard dir.',
                        nargs='+')
    parser.add_argument('--case_insensitive', '-i',
                        help='case insensitive search/reject.',
                        action='store_true')
    parser.add_argument('--histogram', '-hs',
                        help='histogram output for verbose mode',
                        action='store_true')

    args = parser.parse_args()
    # args.directories = [os.path.join(rootdir, i, "log")
    #                       for i in args.directories]
    args.directories = get_dirs()

    if args.runcard is not None:
        args = add_runcard_directories(args)

    if not args.verbose:
        print_short_header()

    for directory in args.directories:
        times, skip_count, total_runs = compile_time_info(directory)
        if not args.verbose:
            print_short_output(directory, times, skip_count, total_runs)
        else:
            print_full_output(directory, times, skip_count,
                              total_runs, args.histogram)
