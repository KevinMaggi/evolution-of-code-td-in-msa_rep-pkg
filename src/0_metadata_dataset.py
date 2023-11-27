#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Author: Kevin Maggi
Email: kevin.maggi@stud.unifi.it / kevin.maggi@edu.unifi.it

This script allows to extract metadata of interest from a GitHub repository and returns the results printed on console
and saved on file and the evolution in the number of microservices as plot.
"""
import csv
import time
from datetime import timedelta
import dateutil.utils
from pathlib import Path
from statistics import mean, median, pvariance

import git  # GitPython
import numpy as np
from github import Github  # PyGithub
from pydriller import Repository  # PyDriller
from matplotlib import pyplot

from src.dc_analysis import determine_microservices, dc_collect_services, process_services, choose_dc
from src.config import COMMIT_DEADLINE
from src.utils.print_utils import print_progress, print_major_step, print_info, printable_time
from src.utils.repo import clear_repo


KEYS = ["URL", "STARS", "FORKS", "CONTRIBUTORS", "CURRENT_LANGS", "COMMITS", "COMMITS_WITH_MICROSERVICES",
        "FROM_DATE", "TO_DATE", "FROM_HASH", "TO_HASH", "MEAN_MS", "MEDIAN_MS", "MAX_MS", "VARIANCE_MS", "EVOLUTION"]


def analyze_repo(url: str, ds_writer: csv.DictWriter) -> None:
    """
    Run the analysis of a single repo

    :param url: url of the repository
    :param ds_writer: CSV writer to write the results of analysis at dataset level
    :return: None
    """
    name = url.split('/')[-2] + '.' + url.split('/')[-1]
    print_major_step(f'# Start repo analysis ({name}) [{url}]')
    workdir = 'temp/clones/' + name
    gh = Github()

    number_of_microservices: list[int] = []

    try:
        print_info('  Cloning repo')
        repository = Repository(url + ".git", to=COMMIT_DEADLINE)  # Pydriller: useful to traverse commits history
        git_repo = git.Repo.clone_from(url, workdir)  # GitPython: useful to work with repo
        gh_repo = gh.get_repo(url.split('/')[-2] + '/' + url.split('/')[-1])  # PyGithub: useful to get statistics

        num_of_commits = len(list(repository.traverse_commits()))

        count, num_commits_with_ms = 0, 0
        first_commit, last_commit = (None, None), (None, None)
        for commit in repository.traverse_commits():  # Apparently traverse commits returns only main branch commits
            count += 1
            print(f'\r{printable_time()}  {count}/{num_of_commits}', end="" if count != num_of_commits else "\r")

            git_repo.git.checkout(commit.hash, force=True)

            if count == 1:
                first_commit = (commit.committer_date, commit.hash)
            last_commit = (commit.committer_date, commit.hash)

            dc = choose_dc(workdir)
            if dc:
                containers = process_services(dc_collect_services(Path(workdir).joinpath(dc)), Path(workdir))
                microservices = determine_microservices(name.split('.')[0], name.split('.')[1], workdir, containers)

                number_of_microservices.append(len(microservices))

                if len(microservices):
                    num_commits_with_ms += 1
            else:
                number_of_microservices.append(0)

        print(f'        ---------- '
              f'[{url}] at {str(dateutil.utils.today())[0:10]} '
              f'(until {str(COMMIT_DEADLINE - timedelta(days=1))[0:10]}) '
              f'----------')
        print(f'         STARS: {gh_repo.stargazers_count}')
        print(f'         FORKS: {gh_repo.forks_count}')
        print(f'        ----------')
        print(f'         CONTRIBUTORS: {gh_repo.get_contributors().totalCount}')
        print(f'        ----------')
        print(f'         CURRENT_LANGS (bytes): {str(gh_repo.get_languages())[1:-1]}')
        print(f'        ----------')
        print(f'         COMMITS: {num_of_commits}')
        print(f'         COMMITS_WITH_MICROSERVICES: {num_commits_with_ms}')
        print(f'         FROM: {str(first_commit[0])[0:10]} ({first_commit[1]})')
        print(f'         TO: {str(last_commit[0])[0:10]} ({last_commit[1]})')
        print(f'        ----------')
        print(f'         MEAN_MS: {mean(number_of_microservices)}')
        print(f'         MEDIAN_MS: {median(number_of_microservices)}')
        print(f'         MAX_MS: {max(number_of_microservices)}')
        print(f'         VARIANCE_MS: {pvariance(number_of_microservices)}')
        print(f'        ----------  ----------')

        ds_writer.writerow({
            "URL": url,
            "STARS": gh_repo.stargazers_count,
            "FORKS": gh_repo.forks_count,
            "CONTRIBUTORS": gh_repo.get_contributors().totalCount,
            "CURRENT_LANGS": str(gh_repo.get_languages())[1:-1],
            "COMMITS": num_of_commits,
            "COMMITS_WITH_MICROSERVICES": num_commits_with_ms,
            "FROM_DATE": str(first_commit[0])[0:10],
            "TO_DATE": str(last_commit[0])[0:10],
            "FROM_HASH": first_commit[1],
            "TO_HASH": last_commit[1],
            "MEAN_MS": mean(number_of_microservices),
            "MEDIAN_MS": median(number_of_microservices),
            "MAX_MS": max(number_of_microservices),
            "VARIANCE_MS": pvariance(number_of_microservices),
            "EVOLUTION": number_of_microservices
        })

        pyplot.suptitle(f'Evolution in number of microservices', size=16, color='blue')
        pyplot.title(f'[ {url[19:]} ]', size=14, style='italic', color='dimgray')
        pyplot.ylabel('# uS', size=12, style='italic')
        pyplot.xlabel('commits', size=12, style='italic')
        pyplot.grid(axis='y')
        us = pyplot.subplot()
        us.set_ylim(ymin=0, ymax=max(number_of_microservices)+0.5)
        us.set_xlim(xmin=0, xmax=num_of_commits)
        us.set_yticks(np.arange(0, max(number_of_microservices) + 1, 1))
        us.spines['top'].set_visible(False)
        us.spines['right'].set_visible(False)
        pyplot.plot(number_of_microservices, linewidth=1.75, color='blue')
        pyplot.savefig(f'../data/dataset/plots/{name}.png')
        pyplot.show()
    except Exception:
        raise
    finally:
        print_info('  Clearing temporary directories')
        clear_repo(Path(workdir))


def analyze_repos() -> None:
    """
    Run the analysis of all the repos contained in the input file

    :return: None
    """
    print_major_step("# Start repositories analysis")

    dataset_file = Path(__file__).parent / '../data/dataset/dataset.csv'

    repos_count = -1  # We don't want to count header
    for _ in open(dataset_file):
        repos_count += 1

    with open(dataset_file) as dataset:
        repos = csv.DictReader(dataset, delimiter=',')

        ds_output_file = Path(__file__).parent / '../data/dataset/evolution.csv'

        with open(ds_output_file, 'w+', newline='') as ds_output:
            writer = csv.DictWriter(ds_output, KEYS)
            writer.writeheader()

            for repo in repos:  # type: dict[str, str]
                print_progress(f'   [{repos.line_num - 1}/{repos_count}]')

                analyze_repo(repo["URL"], writer)

                time.sleep(60)  # to not exceed the rate limit of GitHub API of 30 search per minute


if __name__ == "__main__":
    print_major_step(' Start script execution')
    start_time = time.time()

    print_info(' Performing analysis')
    analyze_repos()

    print_info(' Terminating script execution')
    stop_time = time.time()
    print_progress(f' Total execution time: {str(timedelta(seconds=(stop_time - start_time)))}')
