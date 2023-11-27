#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Author: Kevin Maggi
Email: kevin.maggi@stud.unifi.it / kevin.maggi@edu.unifi.it

This script allows to select the repos that presents a consisted number of microservices. In this step of filtering
will be considered the maximum number of microservices, the longest chunk of commits with flat evolution in number of
microservices, the number of commits with no microservices and the number of times the number of microservices return
to zero.
"""


import csv
import itertools
import time
from datetime import timedelta
from pathlib import Path

import git
from pydriller import Repository

from src.dc_analysis import dc_collect_services, process_services, choose_dc, determine_microservices
from src.utils.print_utils import print_major_step, print_info, print_progress, printable_time
from src.utils.repo import clear_repo
from src.config import COMMIT_DEADLINE, MICROSERVICE_THRESHOLD, FLAT_RATIO_THRESHOLD, FLAT_ABS_THRESHOLD, \
    NO_MS_RATIO_THRESHOLD, RETURN_ZERO_REL_THRESHOLD


def check_number_us_repo(url: str) -> bool:
    """
    Check the condition on the number of microservices for a single repo.

    :param url: url of the repository
    :return: True if the repo meets the number of microservices, False otherwise
    """
    name = url.split('/')[-2] + '.' + url.split('/')[-1]
    print_major_step(f'## Start repo analysis ({name}) [{url}]')
    workdir = str(Path(__file__).parent.joinpath('../temp/clones/' + name))

    try:
        print_info('   Cloning repo')
        repository = Repository(url + ".git", to=COMMIT_DEADLINE)  # Pydriller: to traverse commits history
        git_repo = git.Repo.clone_from(url, workdir)  # GitPython: to work with repo

        print_info('   Analyzing repo')
        num_of_commits = len(list(repository.traverse_commits()))

        count, max_num_us = 0, 0
        num_of_microservices = []
        for commit in repository.traverse_commits():  # Apparently traverse_commits returns only main branch commits
            print(f'\r{printable_time()}   {count}/{num_of_commits}', end="" if count != num_of_commits else "\r")
            count += 1

            git_repo.git.checkout(commit.hash, force=True)

            dc = choose_dc(workdir)
            if dc:
                containers = process_services(dc_collect_services(Path(workdir).joinpath(dc)), Path(workdir))
                microservices = determine_microservices(name.split('.')[0], name.split('.')[1], workdir, containers)
                num_of_microservices.append(len(microservices))
            else:
                num_of_microservices.append(0)

        max_num_ms = max(num_of_microservices)
        if max_num_ms < MICROSERVICE_THRESHOLD:
            print('\r', end="")
            return False

        longest_flat = len(max([list(group) for _, group in itertools.groupby(num_of_microservices)], key=len))
        if longest_flat > FLAT_RATIO_THRESHOLD * num_of_commits or longest_flat > FLAT_ABS_THRESHOLD:
            print('\r', end="")
            return False

        no_ms = len([com for com in num_of_microservices if com == 0])
        if no_ms > NO_MS_RATIO_THRESHOLD * num_of_commits:
            print('\r', end="")
            return False

        num_ret_zero = len([list(group) for _, group in itertools.groupby(num_of_microservices) if list(group)[0] == 0])
        num_ret_zero = num_ret_zero - 1 if num_of_microservices[0] == 0 else num_ret_zero
        if num_ret_zero > RETURN_ZERO_REL_THRESHOLD * num_of_commits:
            print('\r', end="")
            return False

        print('\r', end="")
        return True
    except Exception:
        raise
    finally:
        print_info('   Clearing temporary directories')
        clear_repo(Path(workdir))


def filter_consistent_us_dataset() -> int:
    """
    Run the detection of repo with consistent number of microservices between all the repos contained in the input file

    :return: number of repos that meet the requirement on the number of microservices
    """
    print_major_step("# Start dataset analysis")

    dataset_file = Path(__file__).parent / '../../data/dataset/05_filtered_msa_only.csv'

    total_repos = -1  # We don't want to count header
    for _ in open(dataset_file):
        total_repos += 1

    count = 0
    with open(dataset_file) as dataset:
        repos = csv.DictReader(dataset, delimiter=',')

        ds_output_file = Path(__file__).parent / '../../data/dataset/06_filtered_consistent_ms.csv'

        with open(ds_output_file, 'w+', newline='') as ds_output:
            writer = csv.DictWriter(ds_output, ['URL'])
            writer.writeheader()
            for repo in repos:  # type: dict[str, str]
                print_progress(f'   [{repos.line_num - 1}/{total_repos}]')

                if check_number_us_repo(repo["URL"]):
                    print('   Yes')
                    count += 1
                    writer.writerow({'URL': repo["URL"]})
                else:
                    print('   No')

    return count


if __name__ == "__main__":
    print_major_step(' Start script execution')
    start_time = time.time()

    print_info(' Filtering consistent microservices dataset')
    res = filter_consistent_us_dataset()

    print(f'  => {res} repositories meet the requirement on the number of microservices')

    print_info(' Terminating script execution')
    stop_time = time.time()
    print_progress(f' Total execution time: {str(timedelta(seconds=(stop_time - start_time)))}')
