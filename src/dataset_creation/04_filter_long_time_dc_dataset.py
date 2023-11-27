#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Author: Kevin Maggi
Email: kevin.maggi@stud.unifi.it / kevin.maggi@edu.unifi.it

This script allows to select the long-time docker-compose supporting repos (repos that make use of docker-compose for at
least a custom percentual of the total commits and at least a fixed number of them).
"""

import csv
import time
from datetime import timedelta
from pathlib import Path

import git
from pydriller import Repository

from src.dc_analysis import choose_dc
from src.utils.print_utils import print_major_step, print_info, print_progress, printable_time
from src.utils.repo import clear_repo
from src.config import COMMIT_THRESHOLD, COMMIT_DEADLINE, COMMIT_RATIO_THRESHOLD


def check_long_time_dc_repo(url: str) -> bool:
    """
    Check the long-time docker-compose supporting conditions on a single repo.

    :param url: url of the repository
    :return: True if the repo is long-time docker-compose supporting, False otherwise
    """
    name = url.split('/')[-2] + '.' + url.split('/')[-1]
    print_major_step(f'## Start repo analysis ({name}) [{url}]')
    workdir = str(Path(__file__).parent.joinpath('../temp/clones/' + name))

    try:
        print_info('   Cloning repo')
        repository = Repository(url + ".git",
                                to=COMMIT_DEADLINE, order='reverse')  # Pydriller: to traverse commits history
        git_repo = git.Repo.clone_from(url, workdir)  # GitPython: to work with repo

        print_info('   Analyzing repo')
        num_of_commits = len(list(repository.traverse_commits()))

        count, num_of_dc_commits = 0, 0
        for commit in repository.traverse_commits():  # Apparently traverse_commits returns only main branch commits
            print(f'\r{printable_time()}   {str(num_of_commits - count).ljust(len(str(num_of_commits)))} '
                  f'missing commits oo {num_of_commits}', end="")
            count += 1

            git_repo.git.checkout(commit.hash, force=True)

            dc = choose_dc(workdir)

            if dc:
                num_of_dc_commits += 1
                if (num_of_dc_commits >= num_of_commits * COMMIT_RATIO_THRESHOLD and
                        num_of_dc_commits >= COMMIT_THRESHOLD):
                    print('\r', end="")
                    return True
            else:
                if (count - num_of_dc_commits > num_of_commits * (1 - COMMIT_RATIO_THRESHOLD) or
                        count - num_of_dc_commits > num_of_commits - COMMIT_THRESHOLD):
                    print('\r', end="")
                    return False
    except Exception:
        raise
    finally:
        print_info('   Clearing temporary directories')
        clear_repo(Path(workdir))


def filter_long_time_dc_dataset() -> int:
    """
    Run the detection of long-time docker-compose supporting repo between all the repos contained in the input file

    :return: number of repos that are long-time docker supporting
    """
    print_major_step("# Start dataset analysis")

    dataset_file = Path(__file__).parent / '../../data/dataset/03_filtered_multi_dev.csv'

    total_repos = -1  # We don't want to count header
    for _ in open(dataset_file):
        total_repos += 1

    count = 0
    with open(dataset_file) as dataset:
        repos = csv.DictReader(dataset, delimiter=',')

        ds_output_file = Path(__file__).parent / '../../data/dataset/04_filtered_long_time_docker.csv'

        with open(ds_output_file, 'w+', newline='') as ds_output:
            writer = csv.DictWriter(ds_output, ['URL'])
            writer.writeheader()
            for repo in repos:  # type: dict[str, str]
                print_progress(f'   [{repos.line_num - 1}/{total_repos}]')

                if check_long_time_dc_repo(repo["URL"]):
                    print('   Yes')
                    count += 1
                    writer.writerow({'URL': repo["URL"]})
                else:
                    print('   No')

    return count


if __name__ == "__main__":
    print_major_step(' Start script execution')
    start_time = time.time()

    print_info(' Filtering long-time docker-compose dataset')
    res = filter_long_time_dc_dataset()

    print(f'  => {res} repositories meet the long-time docker-compose requirement')

    print_info(' Terminating script execution')
    stop_time = time.time()
    print_progress(f' Total execution time: {str(timedelta(seconds=(stop_time - start_time)))}')
