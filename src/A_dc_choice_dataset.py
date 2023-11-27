#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Author: Kevin Maggi
Email: kevin.maggi@stud.unifi.it / kevin.maggi@edu.unifi.it

This script allows to find the list of docker-compose files in every commit and the chosen one, grouped by consecutive
commits with same list, so it is easy to identify the commits that have touched the position/name of docker-compose
files.
"""

import csv
import time
import traceback

import dateutil.utils
from datetime import timedelta
from pathlib import Path

import dateutil
import git  # GitPython
from pydriller import Repository  # PyDriller

from dc_analysis import locate_files, choose_dc, DOCKER_COMPOSE_NAMES
from src.config import COMMIT_DEADLINE
from src.utils.print_utils import print_progress, print_major_step, print_info, printable_time
from src.utils.repo import clear_repo


KEYS = ["FROM_N", "FROM_H", "TO_N", "TO_H", "DCFs", "DC"]


def analyze_repo(url: str) -> list[dict[str, int | list[str] | str]]:
    """
    Run the analysis of a single repo

    :param url: url of the repository
    :return: list of chunks of consecutive commits with same docker-compose files
    """
    name = url.split('/')[-2] + '.' + url.split('/')[-1]
    print_major_step(f'## Start repo analysis ({name}) [{url}]')
    workdir = 'temp/clones/' + name

    results: list[dict[str, int | list[str] | str]] = []

    try:
        print_info('   Cloning repo')
        repository = Repository(url + ".git", to=COMMIT_DEADLINE)  # Pydriller: useful to traverse commits history
        git_repo = git.Repo.clone_from(url, workdir)  # GitPython: useful to work with repo

        num_of_commits = len(list(repository.traverse_commits()))

        count = 0
        chunk_docker_composes = set()
        first_chunk_commit_num, first_chunk_commit_hash = 1, None
        last_chunk_commit_hash = None
        last_docker_compose = None
        for commit in repository.traverse_commits():  # Apparently traverse commits returns only main branch commits
            count += 1
            print(f'\r{printable_time()}   {count}/{num_of_commits}', end="" if count != num_of_commits else "\r")

            git_repo.git.checkout(commit.hash, force=True)

            if count == 1:
                first_chunk_commit_hash = commit.hash

            current_docker_composes = set()
            for dc_name in DOCKER_COMPOSE_NAMES:
                current_docker_composes.update(locate_files(workdir, dc_name))

            if current_docker_composes != chunk_docker_composes:
                result = dict.fromkeys(KEYS)
                result["FROM_N"] = first_chunk_commit_num
                result["FROM_H"] = first_chunk_commit_hash
                result["TO_N"] = count - 1
                result["TO_H"] = last_chunk_commit_hash
                result["DCFs"] = chunk_docker_composes
                result["DC"] = last_docker_compose
                results.append(result)
                first_chunk_commit_num, first_chunk_commit_hash = count, commit.hash
                chunk_docker_composes = current_docker_composes

            last_chunk_commit_hash = commit.hash
            last_docker_compose = choose_dc(workdir)

        result = dict.fromkeys(KEYS)
        result["FROM_N"] = first_chunk_commit_num
        result["FROM_H"] = first_chunk_commit_hash
        result["TO_N"] = count
        result["TO_H"] = last_chunk_commit_hash
        result["DCFs"] = chunk_docker_composes
        result["DC"] = last_docker_compose
        results.append(result)

    except Exception as e:
        print(traceback.format_exc())
        raise e
    finally:
        print_info('   Clearing temporary directories')
        clear_repo(Path(workdir))
        return results


def print_results(url: str, chunks: list[dict[str, int | list[str] | str]]) -> None:
    """
    Print the list of chunks of consecutive commits with same docker-compose files

    :param url: url of the repository
    :param chunks: list of chunks of consecutive commits with same docker-compose files
    :return: None
    """
    print(f'        ---------- '
          f'[{url}] at {str(dateutil.utils.today())[0:10]} '
          f'(until {str(COMMIT_DEADLINE - timedelta(days=1))[0:10]}) '
          f'----------')

    for chunk in chunks:
        print(f'')
        print(f'         • from {"{:5d}".format(chunk["FROM_N"])} to {"{:5d}".format(chunk["TO_N"])}: {chunk["DCFs"]}')
        print(f'         |     (ends with {url}/tree/{chunk["TO_H"]} )')
        print(f'         |-> {chunk["DC"]}')

    print(f'        ----------  ----------')


def save_results(url: str, chunks: list[dict[str, int | list[str] | str]]) -> None:
    """
    Save the list of chunks of consecutive commits with same docker-compose files to a csv file

    :param url: url of the repository
    :param chunks: list of chunks of consecutive commits with same docker-compose files
    :return: None
    """
    name = url.split("/")[-2] + "." + url.split("/")[-1]

    results_file = Path(__file__).parent / f'../data/utility/dc_choice/{name}.csv'

    with open(results_file, 'w+', newline='') as results_output:
        ds_writer = csv.DictWriter(results_output, KEYS)
        ds_writer.writeheader()
        for chunk in chunks:  # type: dict[str, int | list[str] | str]
            ds_writer.writerow(chunk)


def analyze_dataset():
    print_major_step("# Start dataset analysis")

    dataset_file = Path(__file__).parent / '../data/dataset/05_filtered_msa_only.csv'

    total_repos = -1  # We don't want to count header
    for _ in open(dataset_file):
        total_repos += 1

    with open(dataset_file) as dataset:
        repos = csv.DictReader(dataset, delimiter=',')

        for repo in repos:  # type: dict[str, str]
            print_progress(f'   [{repos.line_num - 1}/{total_repos}]')

            res = analyze_repo(repo["URL"])
            print_results(repo["URL"], res)
            save_results(repo["URL"], res)


if __name__ == "__main__":
    print_major_step(' Start script execution')
    start_time = time.time()

    print_info(' Locating docker-compose files')
    analyze_dataset()

    print_info(' Terminating script execution')
    stop_time = time.time()
    print_progress(f' Total execution time: {str(timedelta(seconds=(stop_time - start_time)))}')
