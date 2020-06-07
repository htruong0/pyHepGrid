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
    '--idx',
    help='row idx for latin hypercube sampling',
    type=int
)

args, unknowns = parser.parse_known_args()

CONFIG_PATH = "JUNE/configs/config_example.yaml"
SAVE_PATH = "JUNE/results"

# def simulation(num_runs, base_idx, idx):
def simulation(args):
    gf.print_flush(args)

    msoaslist = [
    "E02005702",
    "E02005704",
    "E02005736",
    "E02005734",
    "E02001697",
    "E02001701",
    "E02001704",
    "E02001702",
    "E02001812",
    "E02001803",
    "E02001806",
    "E02001796",
    "E02001801",
    "E02001802",
    "E02001795",
    "E02001818",
    "E02001821",
    "E02001814",
    "E02001808",
    "E02001817",
    "E02001816",
    "E02001819",
    "E02001813",
    "E02001804",
    "E02001811",
    "E02001805",
    "E02001791",
    "E02001794",
    "E02001792",
    "E02004320",
    "E02004321",
    "E02004322",
    "E02004325",
    "E02004327",
    "E02004329",
    "E02004330",
    "E02004328",
    "E02001798",
    "E02001793",
    "E02005706",
    "E02002496",
    "E02002498",
    "E02002500",
    "E02002503",
    "E02002504",
    "E02002515",
    "E02002516",
    "E02006910",
    "E02002518",
    "E02002519",
    "E02002513",
    "E02002550",
    "E02002555",
    "E02002549",
    "E02002542",
    "E02002547",
    "E02002545",
    "E02002543",
    "E02002537",
    "E02002544",
    "E02002541",
    "E02002523",
    "E02002540",
    "E02002536",
    "E02002538",
    "E02002535",
    "E02006909",
    "E02002489",
    "E02002484",
    "E02002487",
    "E02002485",
    "E02002483",
    "E02002493",
    "E02002490",
    "E02002492",
    "E02002494",
    "E02002488",
    "E02002491",
    "E02004332",
    "E02002505",
    "E02002497",
    "E02002502",
    "E02006812",
    "E02002499",
    "E02002506",
    "E02006811",
    "E02002509",
    "E02002501",
    "E02002508",
    "E02002507",
    "E02002529",
    "E02002514",
    "E02002512"]

    gf.print_flush("Generating world from msoalist...")

    geography = Geography.from_file({"msoa" : msoaslist})
    print('memory % used:', psutil.virtual_memory()[2])

    geography.hospitals = Hospitals.for_geography(geography)
    geography.schools = Schools.for_geography(geography)
    geography.companies = Companies.for_geography(geography)
    geography.care_homes = CareHomes.for_geography(geography)
    demography = Demography.for_geography(geography)
    gf.print_flush("Geography and demography generated...")
    world = World(geography, demography, include_households=True, include_commute=False)

    gf.print_flush("World generated...")
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

    simulator = Simulator.from_file(
        world, interaction, selector, 
        config_filename = CONFIG_PATH,
        save_path= SAVE_PATH
    )

    print('memory % used:', psutil.virtual_memory()[2])

    simulator.run()

    gf.print_flush("Simulation finished!!!!")

    return None

if __name__ == "__main__":
    simulation(args)

