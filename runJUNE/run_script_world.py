#!/usr/bin/env python

import os
import time
import json
import argparse
import psutil

import warnings
warnings.filterwarnings('ignore')

import grid_functions as gf

from june.world import generate_world_from_hdf5
from june.hdf5_savers import load_geography_from_hdf5
from june.groups.leisure import *
from june import World
from june.demography.geography import Geography
from june.demography import Demography
from june.interaction import ContactAveraging
from june.infection import Infection
from june.infection.symptoms import SymptomsConstant
from june.infection.transmission import TransmissionConstant
from june.groups import Hospitals, Schools, Companies, Households, CareHomes, Cemeteries
from june.groups.leisure import Cinemas, Pubs, Groceries
from june.simulator import Simulator
from june.seed import Seed
from june import paths
from june.infection.infection import InfectionSelector
from june.groups.commute import *
from june.commute import *

parser = argparse.ArgumentParser()

parser.add_argument(
    '--world',
    help='world to run simulation on',
    type=str
)

parser.add_argument(
    '--latin_hypercube',
    help='name of latin hypercube array',
    type=str
)

parser.add_argument(
    '--idx',
    help='row idx for latin hypercube sampling',
    type=int
)

args, unknowns = parser.parse_known_args()

CONFIG_PATH = "JUNE/configs/config_example.yaml"
SAVE_PATH = "JUNE/results"

def get_size(bytes, suffix="B"):
    """
    Scale bytes to its proper format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

def generate_parameters_from_lhs(lhs_array, idx):
    '''Generates a parameter dictionary from latin hypercube array.
       idx is an integer that should be passed from each run,
       i.e. first run will have idx = 0, second run idx = 1...
       This will index out the row from the latin hypercube.'''
    
    names = ['pub', 'grocery', 'cinema', 'commute_unit', 'commute_city_unit', 'hospital', 'care_home', 'company', 'school', 'household', 'alpha_physical']
    
    parameters = {'betas': {}, 'alpha_physical': 0}
    for i, name in enumerate(names):
        # alpha is always the last so betas are always the first (n-1) elements
        if name in names[:-1]:
            parameters['betas'][name] = lhs_array[idx][i]
        else:
            parameters['alpha_physical'] = lhs_array[idx][i]
    return parameters

def set_interaction_parameters(parameters, interaction):
    '''Sets interaction parameters for the simulation from parameter dictionary.'''
    for key in parameters['betas']:
        interaction.beta[key] = parameters['betas'][key]
    interaction.alpha_physical = parameters['alpha_physical']
    return interaction

def simulation(args):
    gf.print_flush(args)

    print("Physical cores:", psutil.cpu_count(logical=False))
    print("Total cores:", psutil.cpu_count(logical=True))

    print("="*20, "Memory Information", "="*20)
    # get the memory details
    svmem = psutil.virtual_memory()
    print(f"Total: {get_size(svmem.total)}")
    print(f"Available: {get_size(svmem.available)}")
    print(f"Used: {get_size(svmem.used)}")
    print(f"Percentage: {svmem.percent}%")

    pid = os.getpid()
    py = psutil.Process(pid)
    memoryUse = py.memory_info()[0]

    # initialise world from file
    gf.print_flush("Initialising world...")
    world_file = "{}.hdf5".format(args.world)
    world = generate_world_from_hdf5(world_file, chunk_size=1_000_000)
    gf.print_flush("World loaded successfully...")
    geography = load_geography_from_hdf5(world_file)

    # leisure
    gf.print_flush("Initialising leisure...")
    world.pubs = Pubs.for_geography(geography)
    world.cinemas = Cinemas.for_geography(geography)
    world.groceries = Groceries.for_super_areas(geography.super_areas)

    # cemeteries
    gf.print_flush("Initialising cemeteries...")
    world.cemeteries = Cemeteries()

    # commute
    gf.print_flush("Initialising commute...")
    world.initialise_commuting()

    # infection selector
    gf.print_flush("Selecting infection...")

    selector = InfectionSelector.from_file()
    interaction = ContactAveraging.from_file(selector=selector)

    lhs_array = np.load("lhs_array.npy")
    parameters = generate_parameters_from_lhs(lhs_array, args.idx)
    interaction = set_interaction_parameters(parameters, interaction)

    gf.print_flush("Betas = {}, alpha = {}".format(interaction.beta, interaction.alpha_physical))

    if not os.path.exists(SAVE_PATH):
        os.makedirs(SAVE_PATH)
    # save out parameters for later
    with open(SAVE_PATH + '/parameters.json', 'w') as f:
        json.dump(parameters, f)

    # seed infections
    seed = Seed.from_file(super_areas=world.super_areas, 
        selector=selector,)

    print(f"Memory used by JUNE's world: {get_size(memoryUse)}")

    simulator = Simulator.from_file(
        world,
        interaction,
        selector,
        seed=seed,
        config_filename = CONFIG_PATH,
        save_path = SAVE_PATH
    )

    simulator.run()

    # read = ReadLogger(SAVE_PATH)
    # world_df = read.world_summary()
    # ages_df = read.age_summary([0,10,20,30,40,
    #               50,60,70,80,90,100])
    # loc_df = read.get_locations_infections()
    # r_df = read.get_r()

    # world_df.to_csv(SAVE_PATH + '/world_df.csv')
    # ages_df.to_csv(SAVE_PATH + '/ages_df.csv')
    # loc_df.to_csv(SAVE_PATH + '/loc_df.csv')
    # r_df.to_csv(SAVE_PATH + '/r_df.csv')

    gf.print_flush("Simulation finished!!!!")

    return None

if __name__ == "__main__":
    simulation(args)
