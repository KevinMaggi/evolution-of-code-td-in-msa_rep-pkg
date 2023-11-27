#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Author: Kevin Maggi
Email: kevin.maggi@stud.unifi.it / kevin.maggi@edu.unifi.it

Global variables relatives to parameters to use in search, filter and analysis phases.
"""

import datetime


""" GitHub token """
GH_TOKEN: str = ''  # FIXME insert GitHub TOKEN

""" Queries to do on GitHub """
QUERIES: list[list[str]] = [  # Split by language in order to not reach the limit of 1000 results per query
                            ["language:Java topic:microservice stars:>=10",
                             "language:Python topic:microservice stars:>=10",
                             "language:C# topic:microservice stars:>=10",
                             "language:Go topic:microservice stars:>=10",
                             "language:TypeScript topic:microservice stars:>=10",
                             "language:JavaScript topic:microservice stars:>=10"],
                            ["language:Java topic:microservices stars:>=10",
                             "language:Python topic:microservices stars:>=10",
                             "language:C# topic:microservices stars:>=10",
                             "language:Go topic:microservices stars:>=10",
                             "language:TypeScript topic:microservices stars:>=10",
                             "language:JavaScript topic:microservices stars:>=10"],
                            ["language:Java topic:microservice-architecture stars:>=10",
                             "language:Python topic:microservice-architecture stars:>=10",
                             "language:C# topic:microservice-architecture stars:>=10",
                             "language:Go topic:microservice-architecture stars:>=10",
                             "language:TypeScript topic:microservice-architecture stars:>=10",
                             "language:JavaScript topic:microservice-architecture stars:>=10"],
                            ["language:Java topic:microservices-architecture stars:>=10",
                             "language:Python topic:microservices-architecture stars:>=10",
                             "language:C# topic:microservices-architecture stars:>=10",
                             "language:Go topic:microservices-architecture stars:>=10",
                             "language:TypeScript topic:microservices-architecture stars:>=10",
                             "language:JavaScript topic:microservices-architecture stars:>=10"],
                            ["language:Java microservice stars:>=100",
                             "language:Python microservice stars:>=100",
                             "language:C# microservice stars:>=100",
                             "language:Go microservice stars:>=100",
                             "language:TypeScript microservice stars:>=100",
                             "language:JavaScript microservice stars:>=100"]]

""" Repo to skip for some reason """
REPO_TO_SKIP: list[str] = ['https://github.com/oracle/coherence']  # this repo make git clone crash (too big?)

""" The day until which the commits should be considered (excluded) """
COMMIT_DEADLINE: datetime = datetime.datetime(2023, 9, 9)

""" Minimum number of commit """
COMMIT_THRESHOLD: int = 250

""" The minimum ratio of commit_with_dc/commit """
COMMIT_RATIO_THRESHOLD: float = 2 / 3

""" Minimum number of microservices """
MICROSERVICE_THRESHOLD: int = 5

""" Maximum relative length of chunk of commits with constant number of microservices """
FLAT_RATIO_THRESHOLD: float = 50 / 100

""" Maximum absolute length of chunk of commits with constant number of microservices """
FLAT_ABS_THRESHOLD: int = 750

""" Maximum ratio of commits with no microservices (on the total number of commits) """
NO_MS_RATIO_THRESHOLD: float = 30 / 100

""" Maximum number of times that return to 0 microservices (on the total number of commits) """
RETURN_ZERO_REL_THRESHOLD: float = 1 / 175

