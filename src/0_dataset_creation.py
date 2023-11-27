#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Author: Kevin Maggi
Email: kevin.maggi@stud.unifi.it / kevin.maggi@edu.unifi.it

This script executes all the steps of dataset creation, from the query execution on GitHub, to the final dataset through
all the filtering steps. Some of them are manual, so the script waits for your signal to proceed to the next step.
"""
import shutil
import subprocess
from pathlib import Path

if __name__ == "__main__":
    print('\n\n########## Step 0: running query_github script ##########\n')
    subprocess.run(["python3", "-m", "src.dataset_creation.00_query_github"],
                   cwd=Path(__file__).parent.parent)

    print('\n\n########## Step 1: running detect_dc_dataset script ##########\n')
    subprocess.run(["python3", "-m", "src.dataset_creation.01_detect_dc_dataset"],
                   cwd=Path(__file__).parent.parent)

    print('\n\n########## Step 2: running filter_long_life_dataset script ##########\n')
    subprocess.run(["python3", "-m", "src.dataset_creation.02_filter_long_life_dataset"],
                   cwd=Path(__file__).parent.parent)

    print('\n\n########## Step 3: running filter_multi_dev_dataset script ##########\n')
    subprocess.run(["python3", "-m", "src.dataset_creation.03_filter_multi_dev_dataset"],
                   cwd=Path(__file__).parent.parent)

    print('\n\n########## Step 4: running filter_long_time_dc_dataset script ##########\n')
    subprocess.run(["python3", "-m", "src.dataset_creation.04_filter_long_time_dc_dataset"],
                   cwd=Path(__file__).parent.parent)

    print('\n\n########## Step 5: applying filter_msa_dataset filter ##########\n')
    input('You should filter manually the current dataset in order to keep only real MSA. All the instruction at '
          './dataset_creation/05_filter_msa_dataset.md \n Press enter when you have finished...')

    print('\n\n########## Step 6: running filter_consistent_us_dataset script ##########\n')
    subprocess.run(["python3", "-m", "src.dataset_creation.06_filter_consistent_ms_dataset"],
                   cwd=Path(__file__).parent.parent)

    print('\n\n########## End: you can find the final dataset in ../data/dataset/dataset.csv')
    shutil.copyfile('../data/dataset/06_filtered_consistent_ms.csv', '../data/dataset/dataset.csv')
