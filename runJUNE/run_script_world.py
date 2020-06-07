#!/usr/bin/env python

import numpy as np
import time
from SALib.sample import latin
import json
import argparse
import psutil

import grid_functions as gf

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
from june.logger.read_logger import ReadLogger
from june.infection.infection import InfectionSelector
from june.world import generate_world_from_hdf5
from june.hdf5_savers import load_geography_from_hdf5

parser = argparse.ArgumentParser()

parser.add_argument(
    '--num_runs',
    help='number of runs submitted',
    type=int
)

# parser.add_argument(
#     '--base_idx',
#     help='base idx to start seeding',
#     type=int
# )

parser.add_argument(
    '--world',
    help='world to run simulation on',
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

def simulation(args):
    gf.print_flush(args)

    # initialise world from file
    # gf.print_flush("Initialising world...")
    world_file = "{}.hdf5".format(args.world)
    world = generate_world_from_hdf5(world_file, chunk_size=1_000_000)
    gf.print_flush("World loaded successfully...")
    geography = load_geography_from_hdf5(world_file)

    print('memory % used:', psutil.virtual_memory()[2])

    # leisure
    world.cinemas = Cinemas.for_geography(geography)
    world.pubs = Pubs.for_geography(geography)
    world.groceries = Groceries.for_super_areas(world.super_areas,
                                                venues_per_capita=1/500)
    gf.print_flush("Initialised leisure...")

    # commute
    world.initialise_commuting()
    gf.print_flush("Initialised commute...")

    # cemeteries
    world.cemeteries = Cemeteries()
    gf.print_flush("Initialised cemeteries...")

    # infection selector
    selector = InfectionSelector.from_file()
    interaction = ContactAveraging.from_file(selector=selector)
    gf.print_flush("Infection selected...")

    # define groups for betas
    groups = {"leisure"   : ['pub', 'grocery', 'cinema'],
              "commute"   : ['commute_unit', 'commute_city_unit', 'travel_unit'],
              "hospital"  : ['hospital'],
              "care_home" : ['care_home'],
              "company"   : ['company'],
              "school"    : ['school'],
              "household" : ['household']}

    # define problem for latin hypercube sampling
    problem = {
        'num_vars': len(groups),
        'names': list(groups.keys()),
        'bounds': [[1, 2] for _ in range(len(groups))]
    }

    lhs = latin.sample(problem, N=args.num_runs, seed=1)[args.idx]

    betas = {}
    for i, key in enumerate(groups):
        for sub_key in groups[key]:
            betas[sub_key] = lhs[i]
    # save out betas for later
    with open(SAVE_PATH + '/betas.json', 'w') as f:
        json.dump(betas, f)
            
    # set betas in simulation to sampled ones
    for key in betas:
        interaction.beta[key] = betas[key]

    gf.print_flush(interaction.beta)

    # seed infections
    seed = Seed(world.super_areas, selector,)
    n_cases = int(len(world.people)/10)
    seed.unleash_virus(n_cases)

    print('memory % used:', psutil.virtual_memory()[2])

    simulator = Simulator.from_file(
        world, interaction, selector, 
        config_filename = CONFIG_PATH,
        save_path= SAVE_PATH
    )

    simulator.run()

    print('memory % used:', psutil.virtual_memory()[2])

    gf.print_flush("Simulation finished!!!!")

    return None

if __name__ == "__main__":
    gf.print_flush("Initialising world...")
    simulation(args)

