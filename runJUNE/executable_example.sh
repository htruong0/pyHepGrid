#!/usr/bin/env bash

export PYTHONPATH=$PYTHONPATH:`pwd`/JUNE/
cd JUNE/scripts
echo Installing anaconda...
bash Miniconda3-latest-Linux-x86_64.sh -b -p ./miniconda
mkdir -p JUNE_env
echo Unpacking conda environment
tar -xzf JUNE_env.tar.gz -C JUNE_env
source JUNE_env/bin/activate
echo Beginning simulation...
python run_script.py --seed=$1
echo Cleaning up environment...
source my_env/bin/deactivate
rm -rf ./JUNE_env
rm -rf ./miniconda
echo Finished.


# export PYTHONPATH=$PYTHONPATH:`pwd`/JUNE/
# cd JUNE/scripts
# python3 -m venv june_env
# source june_env/bin/activate
# echo Activated virtual environment!!!!!!
# pip install -r requirements.txt
# echo Finished installing all required packages!!!!!
# echo Running simulation now!!!!!!
# python run_script.py --seed=$1
# deactivate
# rm -r june_env
