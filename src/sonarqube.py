#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Author: Kevin Maggi
Email: kevin.maggi@stud.unifi.it / kevin.maggi@edu.unifi.it

Small library to manage SonarQube analysis via SonarScanner. It supports multiple SonarScanner version: CLI, for Maven
and for .NET. It provides functions for all the workflow of a Sonar analysis.
It just needs the correct value of parameters in the macros at the top of the file.
"""

import logging
import re
import shutil
import subprocess
import time
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Optional, List

import requests
from src.utils.print_utils import print_appendable
from requests import RequestException
from requests.auth import HTTPBasicAuth


SQ_USER = 'admin'
SQ_PASSWORD = 'admin'  # FIXME change pw
SQ_TOKEN = ''
SQ_TOKEN_NAME = 'mining_script'  # FIXME change token name

SS_DOTNET_DIR = '/home/kevin/Desktop/sonar-scanner-dotnet-5.13.1'  # FIXME change directory
SS_MAVEN_VER = '3.9.1.2184'  # FIXME update version


def sq_start_up() -> None:
    """
    Starts SonarQube server with Docker compose and creates an user token

    :return: None
    """
    cmd = ['docker', 'compose', 'up']
    subprocess.Popen(cmd, cwd=Path(__file__).parent, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print_appendable('Starting Docker container')
    while True:
        time.sleep(5)
        try:
            print_appendable('.')
            response = sq_get('api/system/status')
            if response['status'] == 'UP':
                print(' SonarQube is operational')
                break
        except RequestException:
            continue

    global SQ_TOKEN
    SQ_TOKEN = sq_post('api/user_tokens/generate', {'name': SQ_TOKEN_NAME})['token']


def sq_shut_down(remove: bool = False) -> None:
    """
    Shuts down SonarQube server instance (also revoking the user token)

    :param remove: if True it removes the containers
    :return: None
    """
    sq_post('api/user_tokens/revoke', {'name': SQ_TOKEN_NAME})
    global SQ_TOKEN
    SQ_TOKEN = None

    if remove:
        cmd = ['docker', 'compose', 'down']
    else:
        cmd = ['docker', 'compose', 'stop']

    subprocess.run(cmd, cwd=Path(__file__).parent, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def sq_token() -> str:
    """
    Returns the current user token

    :return: user token
    """
    return SQ_TOKEN


def sq_get(url: str, params: dict[str, str] = None) -> Any:
    """
    Performs a get request to SonarQube server through Web API

    :param url: API
    :param params: parameters
    :return: response
    """
    if params is None:
        params = {}
    response = requests.get('http://localhost:9000/' + url,
                            auth=HTTPBasicAuth(username=SQ_USER, password=SQ_PASSWORD),
                            verify=False,
                            params=params)
    return response.json()


def sq_post(url: str, params: dict[str, str]) -> Any:
    """
    Performs a post request to SonarQube server through Web API

    :param url: API
    :param params: parameters
    :return: response
    """
    response = requests.post('http://localhost:9000/' + url,
                             auth=HTTPBasicAuth(username=SQ_USER, password=SQ_PASSWORD),
                             verify=False,
                             params=params)
    try:
        return response.json()
    except JSONDecodeError:
        return None


def sq_scanner_cli(project: str,
                   docker: bool, verbose: bool = False, debug: bool = False,
                   java: bool = False) -> bool:
    """
    Performs the sonar scanner analysis on the project using SonarScanner CLI

    :param project: project's key
    :param docker: True if you want to run scanner as Docker container, False if you want to run local executable
    :param verbose: True if you want the stdout of sonar scanned to be print on console
    :param debug: True if you want to run sonar scanner in debug/verbose mode. Make sense only if verbose is active
    :param java: True if you want to analyze a Java project (without compilation), so it is necessary to fake the
    compilation directory

    :return: True if the analysis succeed, False otherwise. N.B. if verbose=True, the detection of build success could
    be less accurate
    """
    # Setting up analysis options
    extra_options = '-Dsonar.sourceEncoding=UTF-8 -Dsonar.cpd.exclusions=** -Dsonar.scm.disabled=true'  # fast analysis

    if debug:
        debug_options = '-Dsonar.verbose=true'
    else:
        debug_options = '-Dsonar.verbose=false'

    # Creating a fake dir to make fun on SonarJava Plugin and analyze Java without compiling
    if java and not Path(__file__).parent.joinpath(f'temp/clones/{project}/fakedir').exists():
        subprocess.run('mkdir "fakedir"', cwd=Path(__file__).parent.joinpath("temp/clones/" + project),
                       stdout=subprocess.PIPE, shell=True)

    java_options = '-Dsonar.java.binaries=/fakedir' if java else ''

    # Defining the command for the analysis
    if not docker:
        cmd = f'sonar-scanner -Dsonar.login={SQ_TOKEN} ' \
              f'-Dsonar.projectKey={project} -Dsonar.projectBaseDir=temp/clones/{project} ' \
              f'{debug_options} {extra_options} {java_options} -Dsonar.java.binaries=**/*.'
    else:
        cmd = f'docker run --rm --network="host" ' \
              f'-e SONAR_SCANNER_OPTS="-Dsonar.projectKey={project} {debug_options} {extra_options} {java_options}" ' \
              f'-e SONAR_LOGIN="{SQ_TOKEN}" ' \
              f'-v "{Path(__file__).parent.joinpath("temp/clones/" + project)}:/usr/src" ' \
              f'sonarsource/sonar-scanner-cli'

    # Running the analysis
    if verbose:
        sonar_scanner = subprocess.run(cmd, cwd=Path(__file__).parent, shell=True)
        return True if sonar_scanner.returncode == 0 else False
    else:
        sonar_scanner = subprocess.run(cmd, cwd=Path(__file__).parent, shell=True, stdout=subprocess.PIPE, text=True)
        return True if sonar_scanner.returncode == 0 and "EXECUTION SUCCESS" in sonar_scanner.stdout else False


def sq_scanner_dotnet(project: str, solution: str = '',
                      verbose: bool = False, debug: bool = False,
                      all_builds: bool = True) -> bool:
    """
    Performs the sonar scanner analysis on the C# project using SonarScanner for .NET. SonarScanner for .NET will
    analyze only the file listed in .sonarqube/out/sonar-project.properties after the dotnet build (so, for projects
    with .NET Core and .NET 5+ all files of supported language, while for old-style projects only C# and VB files)

    :param project: project's key
    :param solution: solution file for building (the default value will take the only project/solution file in the
    directory, if more are present, the build will fail)
    :param verbose: True if you want the stdout of sonar scanned to be print on console
    :param debug: True if you want to run sonar scanner in debug/verbose mode. Make sense only if verbose is active
    :param all_builds: True if you want to analyze also failing build

    :return: True if the analysis succeed, False otherwise. N.B. if verbose=True, the detection of build success could
    be less accurate
    """
    # Setting up analysis options
    extra_options = '/d:sonar.sourceEncoding="UTF-8" /d:sonar.cpd.exclusions="**" ' \
                    '/d:sonar.scm.provider="git"'  # faster analysis

    if debug:
        debug_options = '/d:sonar.verbose="true"'
    else:
        debug_options = '/d:sonar.verbose="false"'

    # Defining the command for the analysis
    begin_cmd = f'dotnet {SS_DOTNET_DIR}/SonarScanner.MSBuild.dll begin ' \
                f'/k:"{project}" /d:sonar.login="{SQ_TOKEN}" /d:sonar.host.url=http://localhost:9000 ' \
                f'{debug_options} {extra_options}'
    build_cmd = f'dotnet build {solution} '
    end_cmd = f'dotnet {SS_DOTNET_DIR}/SonarScanner.MSBuild.dll end ' \
              f'/d:sonar.login="{SQ_TOKEN}"'

    # Running the analysis
    if verbose:
        begin = subprocess.run(begin_cmd, cwd=Path(__file__).parent.joinpath('temp/clones/' + project), shell=True)
        print('----------')
        build = subprocess.run(build_cmd, cwd=Path(__file__).parent.joinpath('temp/clones/' + project), shell=True)
        print('----------')
        end = subprocess.run(end_cmd, cwd=Path(__file__).parent.joinpath('temp/clones/' + project), shell=True)

        shutil.rmtree(Path(__file__).parent.joinpath('temp/clones/' + project + '/.sonarqube'))

        return True if (begin.returncode == 0 and
                        (build.returncode == 0 if not all_builds else True) and
                        end.returncode == 0
                        ) else False
    else:
        begin = subprocess.run(begin_cmd, cwd=Path(__file__).parent.joinpath('temp/clones/' + project), shell=True,
                               stdout=subprocess.PIPE, text=True, stderr=subprocess.PIPE)
        build = subprocess.run(build_cmd, cwd=Path(__file__).parent.joinpath('temp/clones/' + project), shell=True,
                               stdout=subprocess.PIPE, text=True, stderr=subprocess.PIPE)
        end = subprocess.run(end_cmd, cwd=Path(__file__).parent.joinpath('temp/clones/' + project), shell=True,
                             stdout=subprocess.PIPE, text=True, stderr=subprocess.PIPE)

        shutil.rmtree(Path(__file__).parent.joinpath('temp/clones/' + project + '/.sonarqube'))

        return True if (begin.returncode == 0 and "Pre-processing succeeded" in begin.stdout and
                        ((build.returncode == 0 and "0 Error(s)" in build.stdout) if not all_builds else True) and
                        end.returncode == 0 and "EXECUTION SUCCESS" in end.stdout and
                        "Post-processing succeeded" in end.stdout
                        ) else False


def sq_scanner_maven(project: str,
                     verbose: bool = False, debug: bool = False,
                     all_builds: bool = True, compilation: bool = True,
                     old_strings: List[str] = None, new_strings: List[str] = None, poms: List[Path] = None,
                     add_params: str = '') -> bool:
    """
    Performs the sonar scanner analysis on the project using SonarScanner for Maven. SonarScanner for Maven will
    analyze only the Java file.

    :param project: project's key
    :param verbose: True if you want the stdout of sonar scanned to be print on console
    :param debug: True if you want to run sonar scanner in debug/verbose mode. Make sense only if verbose is active
    :param all_builds: True if you want to analyze also failing build
    :param compilation: True if you want to compile before analyze
    :param old_strings: strings in POM to be substituted with new_strings
    :param new_strings: strings in POM that have to substitute old_strings
    :param poms: list of POMs where to apply substitutions
    :param add_params: parameters to add to the Maven invocation

    :return: True if the analysis succeed, False otherwise. N.B. if verbose=True, the detection of build success could
    be less accurate
    """
    try:
        # Setting up analysis options
        if debug:
            debug_options = '-Dsonar.verbose=true -X'
        else:
            debug_options = '-Dsonar.verbose=false'

        # Modifying the POMs
        if not poms:
            poms_file = [Path(__file__).parent.joinpath(f'temp/clones/{project}/pom.xml')]
        else:
            poms_file = poms

        for pom_file in poms_file:
            if pom_file.exists():
                with open(pom_file, 'r') as pom:
                    pom_content = pom.read()

                for (old_string, new_string) in zip(old_strings, new_strings):
                    pom_content = re.sub(old_string, new_string, pom_content)

                with open(pom_file, 'w') as pom:
                    pom.write(pom_content)

        # Creating a fake dir to make fun on SonarJava Plugin and analyze Java without compiling
        # if compilation and not Path(__file__).parent.joinpath(f'temp/clones/{project}/fakedir').exists():
        #     subprocess.run('mkdir "fakedir"', cwd=Path(__file__).parent.joinpath("temp/clones/" + project),
        #                    stdout=subprocess.PIPE, shell=True)

        # Selecting Maven or Maven Wrapper
        if not Path(Path(__file__).parent.joinpath(f'temp/clones/{project}/.mvn')).exists():
            mvn = 'mvn'
        else:
            mvn = './mvnw'

        # Defining the command for the analysis
        cmd = f'{mvn} clean ' \
              f'{"compile" if compilation else ""} ' \
              f'org.sonarsource.scanner.maven:sonar-maven-plugin:{SS_MAVEN_VER}:sonar ' \
              f'-Dsonar.host.url=http://localhost:9000 -Dsonar.login={SQ_TOKEN} -Dsonar.projectKey={project} ' \
              f'-U -B {debug_options} ' \
              f'{"-Dmaven.compiler.failOnError=false" if all_builds else ""} ' \
              f'{"-Dsonar.java.binaries=/fakedir" if not compilation else ""} ' \
              f'{add_params} '

        # Running the analysis
        if verbose:
            mvn = subprocess.run(cmd,
                                 cwd=Path(__file__).parent.joinpath("temp/clones/" + project),
                                 shell=True)
            return True if mvn.returncode == 0 else False
        else:
            mvn = subprocess.run(cmd,
                                 cwd=Path(__file__).parent.joinpath("temp/clones/" + project),
                                 shell=True, stdout=subprocess.PIPE, text=True)
            return True if mvn.returncode == 0 and "BUILD SUCCESS" in mvn.stdout else False

    except Exception as e:
        logging.error("Error building with Maven", exc_info=e)
        return False


def sq_wait_ce(component: str) -> bool:
    """
    Checks if the current task has finished running or not and if it has succeeded

    :param component: the component of which we are interested in task
    :return: True if task succeeds, False otherwise
    """
    while True:
        time.sleep(5)
        try:
            response = sq_get('api/ce/component', {'component': component})
            if len(response['queue']):
                print_appendable('.')
            elif response['current']['status'] == 'SUCCESS':
                print(' Processing ended')
                return True
            else:
                print(' Processing ended')
                return False
        except RequestException:
            continue


def sq_measure(component: str, metric: str) -> Optional[str | int]:
    """
    Queries the server to get the measurement of a metric

    :param component: component to which look up
    :param metric: metric to retrieve
    :return: the value of measure or None if the metric has not been calculated
    """
    # noinspection PyBroadException
    try:
        response = sq_get('api/measures/component', {'component': component, 'metricKeys': metric})
        measures = response['component']['measures']
        if not measures:
            return None

        return measures[0]['value']
    except Exception:
        return ''
