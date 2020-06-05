import numpy as np
import time
from SALib.sample import latin
import json
import argparse

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



def simulation(seed):
    geography = Geography.from_file({
                                "msoa":  ["E02002512", "E02001697"]
                                          #["E02001720",
                                          #"E00088544", 
                                          #"E02002560", 
                                          #"E02002559"]
                                }
                                )

    geography.hospitals = Hospitals.for_geography(geography)
    geography.schools = Schools.for_geography(geography)
    geography.companies = Companies.for_geography(geography)
    geography.care_homes = CareHomes.for_geography(geography)
    demography = Demography.for_geography(geography)
    world = World(geography, demography, include_households=True)

    # leisure
    world.cinemas = Cinemas.for_geography(geography)
    world.pubs = Pubs.for_geography(geography)
    world.groceries = Groceries.for_super_areas(world.super_areas,
                                                venues_per_capita=1/500)

    # commute
    world.initialise_commuting()

    # cemeteries
    world.cemeteries = Cemeteries()

    # infection selector
    selector = InfectionSelector.from_file()
    interaction = ContactAveraging.from_file(selector=selector)

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
        'bounds': [[0, 2] for _ in range(len(groups))]
    }

    # sample one time with random seed
    lhs = latin.sample(problem, N=1, seed=seed)[0]

    betas = {}
    for i, key in enumerate(groups):
        for sub_key in groups[key]:
            betas[sub_key] = lhs[i]
            
    # save out betas for later
    with open('../results/betas.json', 'w') as f:
        json.dump(betas, f)
            
    # set betas in simulation to sampled ones
    for key in betas:
        interaction.beta[key] = betas[key]

    # seed infections
    seed = Seed(world.super_areas, selector,)
    n_cases = 50
    seed.unleash_virus(n_cases)

    CONFIG_PATH = "../configs/config_example.yaml"

    simulator = Simulator.from_file(
        world, interaction, selector, 
        config_filename = CONFIG_PATH
    )

    simulator.run()

    print("Simulation finished!!!!")

    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--seed',
        help='random seed',
        type=int
    )

    args = parser.parse_args()
    seed = args.seed
    
    simulation(seed)
