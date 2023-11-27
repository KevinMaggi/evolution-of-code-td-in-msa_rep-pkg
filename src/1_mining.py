#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Author: Kevin Maggi
Email: kevin.maggi@stud.unifi.it / kevin.maggi@edu.unifi.it

This script executes the analysis of the dataset with SonarScanner and SonarQube. Each repository is treated ad-hoc for
its analysis basing on language and build.
"""

import csv
import logging
import os
import re
import subprocess
import time
from datetime import timedelta
from pathlib import Path

import git  # GitPython
from pydriller import Repository  # PyDriller

from src.config import COMMIT_DEADLINE
from src.dc_analysis import choose_dc, dc_collect_services, determine_microservices, process_services, locate_files
from src.utils.print_utils import print_progress, print_major_step, print_minor_step, print_info
from src.utils.repo import clear_repo
from src.sonarqube import sq_start_up, sq_shut_down, sq_post, sq_scanner_cli, sq_measure, sq_wait_ce, sq_scanner_maven, \
    SQ_TOKEN, sq_scanner_dotnet

SQ_METRICS = ["COMPLEXITY", "COGNITIVE_COMPLEXITY",  # complexity
              "VIOLATIONS",  # issues
              "BLOCKER_VIOLATIONS", "CRITICAL_VIOLATIONS", "MAJOR_VIOLATIONS", "MINOR_VIOLATIONS", "INFO_VIOLATIONS",
              "CODE_SMELLS", "SQALE_RATING", "SQALE_INDEX", "SQALE_DEBT_RATIO",  # maintainability
              "ALERT_STATUS",  # quality gate
              "BUGS", "RELIABILITY_RATING", "RELIABILITY_REMEDIATION_EFFORT",  # reliability
              "VULNERABILITIES", "SECURITY_RATING", "SECURITY_REMEDIATION_EFFORT", "SECURITY_HOTSPOTS",  # security
              "CLASSES", "COMMENT_LINES", "COMMENT_LINES_DENSITY", "DIRECTORIES", "FILES",  # size
              "LINES", "NCLOC", "FUNCTIONS", "STATEMENTS"
              ]

DS_KEYS = ["REPO", "COMMIT",  # identifier
           "PARENT",  # topology info
           "AUTHOR_NAME", "AUTHOR_EMAIL", "AUTHOR_DATE", "AUTHORS",  # author info
           "COMMITTER_NAME", "COMMITTER_EMAIL", "COMMITTER_DATE", "COMMITTERS",  # committer info
           "MICROSERVICES"  # microservices
           # "LANGUAGES"
           ] + SQ_METRICS

# P_KEYS = ["COMMIT", "MICROSERVICE_NAME",  # identifier
#           "MICROSERVICE_PATH"   # additional info
#           ] + SQ_METRICS

# if language := True & (shutil.which('github-linguist') is not None):
#     import ghlinguist as ghl


def analyze_repo(url: str, ds_writer: csv.DictWriter, recurse: bool = False) -> None:
    """
    Run the analysis of a single repo

    :param url: url of the repository
    :param ds_writer: CSV writer to write the results of analysis at dataset level
    :param recurse: if True the cloning recurse on the submodules
    :return: None
    """
    name = url.split('/')[-2] + '.' + url.split('/')[-1]
    print_major_step(f'## Start repo analysis ({name}) [{url}]')
    workdir = 'src/temp/clones/' + name

    try:
        print_info('   Cloning repo and creating SQ project')
        repository = Repository(url + ".git", to=COMMIT_DEADLINE)  # Pydriller: useful to traverse commits history
        git_repo = git.Repo.clone_from(url, workdir)  # GitPython: useful to work with repo (git show, shortlog...)

        sq_post('api/projects/create', {'name': name, 'project': name})

        print_info('   Counting commits')
        num_of_commits = len(list(repository.traverse_commits()))

        count = 0
        for commit in repository.traverse_commits():  # Apparently traverse commits returns only main branch commits
            count += 1

            if count % 50 == 0:
                print_info("   Restarting SonarQube server")
                sq_shut_down()
                sq_start_up()

            print_minor_step(f'   Start commit analysis ({count}/{num_of_commits}) [{commit.hash}]')

            git_repo.git.checkout(commit.hash, force=True)

            repo_analysis: dict[str, str | int | None] = dict.fromkeys(DS_KEYS)

            repo_analysis['REPO'] = url
            repo_analysis['COMMIT'] = commit.hash

            print_info('   Analyzing Git history')
            recover_git_infos(git_repo, commit.hash, repo_analysis)

            print_info('   Analyzing microservices')
            compute_microservice_metric(name, workdir, repo_analysis)

            # if language:
            #     print_info('   Analysing languages')
            #     repo_analysis['LANGUAGES'] = ghl.linguist(Path(__file__).parent.joinpath(f'temp/clones/{name}'))

            print_info('   Analyzing SonarQube code quality')

            if name == "ThoreauZZ.spring-cloud-example":
                sonar_success = sq_scanner_thoreauzz(name, verbose=True)
            elif name == "geoserver.geoserver-cloud":
                sonar_success = sq_scanner_geoserver(name, verbose=True)
            elif name == "nashtech-garage.yas":
                sonar_success = sq_scanner_nashtechgarage(name, verbose=True)
            elif name == "jvalue.ods":
                sonar_success = sq_scanner_jvalue(name, verbose=True)
            elif name == "OpenCodeFoundation.eSchool":
                sonar_success = sq_scanner_opencodefoundation(name, verbose=True)
            elif name == "netcorebcn.quiz":
                sonar_success = sq_scanner_netcorebcn(name, verbose=True)
            elif name == "asc-lab.micronaut-microservices-poc":
                sonar_success = sq_scanner_asclab(name, verbose=True)
            elif name == "dotnet-architecture.eShopOnContainers":
                # sonar_success = sq_scanner_dotnetarchitecture(name, verbose=True)
                sonar_success = False
            else:
                # 1-Platform.one-platform, learningOrchestra.mlToolKits, microrealestate.microrealestate,
                # minos-framework.ecommerce-example, open-telemetry.opentelemetry-demo, bee-travels.bee-traverls-node
                # go-saas.kit
                sonar_success = sq_scanner_cli(name, docker=False, verbose=True)

            if sonar_success:
                print_info('   Waiting results\' availability and retrieving metrics\' measures')
                if sq_wait_ce(name):
                    retrieve_sq_metrics(name, repo_analysis)

            print_info('   Writing data')
            ds_writer.writerow(repo_analysis)
    except Exception:
        raise
    finally:
        print_info('   Clearing temporary directories')
        clear_repo(Path(workdir))


def sq_scanner_geoserver(project: str,
                         verbose: bool = False, debug: bool = False,
                         all_builds: bool = True, compilation: bool = True) -> bool:
    """
    Performs the analysis by building with Maven (with substitutions needed to compile successfully) and
    invoking SonarScanner for Maven

    :param project: project key on the SonarQube server
    :param verbose: if True all Maven log will be printed to the console
    :param debug: True if you want to run sonar scanner in debug/verbose mode
    :param all_builds: True if you want to analyze also failing build
    :param compilation: True if you want to compile before analyze

    :return: True if the build succeed, False otherwise. N.B. if verbose=True, the detection of build success could be
    less accurate
    """
    old_lombok_dep = "<groupId>org.projectlombok</groupId>\s*" \
                     "<artifactId>lombok</artifactId>\s*" \
                     "<version>((\$\{[a-zA-z.]*\})|[0-9.]+)</version>"
    new_lombok_dep = "<groupId>org.projectlombok</groupId>\n" \
                     "<artifactId>lombok</artifactId>\n" \
                     "<version>1.18.24</version>"
    old_lombok_var = "<lombok.version>[0-9.]+</lombok.version>"
    new_lombok_var = "<lombok.version>1.18.24</lombok.version>"
    old_spring_repo = "https://repo.spring.io/release"
    new_spring_repo = "https://repo.spring.io/milestone"
    old_gs_var = "<gs.version>2.2[0-9](.[0-9])*(-[A-Z]+)*</gs.version>"
    new_gs_var = "<gs.version>2.23.1</gs.version>"
    old_gs_com_var = "<gs.community.version>2.2[0-9](.[0-9])*(-[A-Z]+)*</gs.community.version>"
    new_gs_com_var = "<gs.community.version>2.22.0</gs.community.version>"
    old_gs_prof = "<id>geoserver</id>\s*" \
                  "<activation>\s*<activeByDefault>true</activeByDefault>\s*</activation>"
    new_gs_prof = "<id>geoserver</id>\n" \
                  "<activation>\n<activeByDefault>false</activeByDefault>\n</activation>"
    old_dep = "<groupId>org.geoserver.community</groupId>\s*" \
              "<artifactId>gs-datadir-catalog-loader</artifactId>\s*" \
              "<version>\$\{gs.community.version\}</version>"
    new_dep = "<groupId>org.geoserver.community</groupId>\n" \
              "<artifactId>gs-datadir-catalog-loader</artifactId>\n" \
              "<version>2.24-SNAPSHOT</version>"
	old_enforced = "<goals>\s*" \
                   "<goal>enforce</goal>\s*" \
                   "</goals>"
    new_enforced = ""

    return sq_scanner_maven(project, verbose, debug, all_builds, compilation,
                            old_strings=[old_lombok_dep, old_lombok_var, old_spring_repo, old_gs_var, old_gs_com_var,
                                         old_gs_prof, old_dep, old_enforced],
                            new_strings=[new_lombok_dep, new_lombok_var, new_spring_repo, new_gs_var, new_gs_com_var,
                                         new_gs_prof, new_dep, new_enforced],
                            poms=[Path(__file__).parent.joinpath(f'temp/clones/{project}/pom.xml'),
                                  Path(__file__).parent.joinpath(f'temp/clones/{project}/src/pom.xml')],
                            add_params="")


def sq_scanner_thoreauzz(project: str,
                         verbose: bool = False, debug: bool = False,
                         all_builds: bool = True, compilation: bool = True) -> bool:
    """
    Performs the analysis by building with Maven and invoking SonarScanner for Maven

    :param project: project key on the SonarQube server
    :param verbose: if True all Maven log will be printed to the console
    :param debug: True if you want to run sonar scanner in debug/verbose mode
    :param all_builds: True if you want to analyze also failing build
    :param compilation: True if you want to compile before analyze

    :return: True if the build succeed, False otherwise. N.B. if verbose=True, the detection of build success could be
    less accurate
    """
    if Path(__file__).parent.joinpath(f'temp/clones/{project}/cloud-service-comx/pom.xml').exists():
        with open(Path(__file__).parent.joinpath(f'temp/clones/{project}/cloud-service-comx/pom.xml'), 'r') as ext_pom:
            ext_content = ext_pom.read()

        old_par = "<groupId>com.gomeplus.oversea</groupId>\s*" \
                  "<artifactId>bs-cloud-parent</artifactId>"
        new_par = "<groupId>com.erdaoya</groupId>\n" \
                  "<artifactId>spring-cloud-example-parent</artifactId>"

        old_dep = "<groupId>com.gomeplus.oversea</groupId>\s*" \
                  "<artifactId>bs-common-exception</artifactId>"
        new_dep = "<groupId>com.erdaoya</groupId>\n" \
                  "<artifactId>cloud-common-exception</artifactId>"

        ext_content = re.sub(old_par, new_par, ext_content)
        ext_content = re.sub(old_dep, new_dep, ext_content)

        with open(Path(__file__).parent.joinpath(f'temp/clones/{project}/cloud-service-comx/pom.xml'), 'w') as ext_pom:
            ext_pom.write(ext_content)

    old_lombok_var = "<lombok.version>[0-9.]+</lombok.version>"
    new_lombok_var = "<lombok.version>1.18.24</lombok.version>"

    old_lombok_lat = "<dependency>\s*" \
                     "<groupId>org.projectlombok</groupId>\s*" \
                     "<artifactId>lombok</artifactId>\s*" \
                     "</dependency>"
    new_lombok_lat = "<dependency>\n" \
                     "<groupId>org.projectlombok</groupId>\n" \
                     "<artifactId>lombok</artifactId>\n" \
                     "<version>1.18.24</version>\n" \
                     "</dependency>"

    old_gmaven_dep = "<dependency>\s*" \
                     "<groupId>org.codehaus.groovy.maven.runtime</groupId>\s*" \
                     "<artifactId>gmaven-runtime-1.0</artifactId>\s*" \
                     "<version>1.0</version>\s*" \
                     "<scope>test</scope>\s*" \
                     "</dependency>"
    new_gmaven_dep = ""

    old_turbine_mod = "<module>cloud-turbine-dashboard</module>"
    new_turbine_mod = "<module>cloud-turbine-dashboard</module>" if (
        Path(__file__).parent.joinpath(f'temp/clones/{project}/cloud-turbine-dashboard/pom.xml').exists()) else ""

    old_user_mod = "<module>cloud-user-api</module>"
    new_user_mod = "<module>cloud-user-api</module>" if (
        Path(__file__).parent.joinpath(f'temp/clones/{project}/cloud-user-api/pom.xml').exists()) else ""

    old_bscomm_mod = "<module>bs-common-exception</module>"
    new_bscomm_mod = "<module>bs-common-exception</module>" if (
        Path(__file__).parent.joinpath(f'temp/clones/{project}/cloud-user-api/pom.xml').exists()) else ""

    return sq_scanner_maven(project, verbose, debug, all_builds, compilation,
                            old_strings=[old_lombok_var, old_lombok_lat, old_gmaven_dep, old_turbine_mod, old_user_mod,
                                         old_bscomm_mod],
                            new_strings=[new_lombok_var, new_lombok_lat, new_gmaven_dep, new_turbine_mod, new_user_mod,
                                         new_bscomm_mod],
                            poms=[Path(__file__).parent.joinpath(f'temp/clones/{project}/pom.xml'),
                                  Path(__file__).parent.joinpath(f'temp/clones/{project}/cloud-service-comx/pom.xml'),
                                  Path(__file__).parent.joinpath(f'temp/clones/{project}/cloud-comx/pom.xml')],
                            add_params='-Dmdep.skip=true')


def sq_scanner_nashtechgarage(project: str, verbose: bool = False) -> bool:
    """
    Performs the analysis by building with Maven and then invoking SonarScanner CLI (due to other languages present).
    When an aggregator POM isn't available, it will be created by looking for modules.

    :param project: project key on the SonarQube server
    :param verbose: if True all Maven log will be printed to the console

    :return: True if the build succeed, False otherwise. N.B. if verbose=True, the detection of build success could be
    less accurate
    """
    if not Path(__file__).parent.joinpath(f'temp/clones/{project}/pom.xml').exists():
        modules = locate_files(str(Path(__file__).parent.joinpath(f'temp/clones/{project}')), 'pom.xml')

        pom_content = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' \
                      '<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">\n' \
                      '<modelVersion>4.0.0</modelVersion>\n' \
                      '<groupId>com.yas</groupId>\n' \
                      '<artifactId>yas</artifactId>\n' \
                      '<version>0.0.1-SNAPSHOT</version>\n' \
                      '<packaging>pom</packaging>\n' \
                      '<name>yas</name>\n' \
                      '<modules>\n'
        for module in modules:
            pom_content += f'{"<module>" + module.split("/")[-2] + "</module>"}\n'
        pom_content += '</modules>\n' \
                       '</project>'

        with open(Path(__file__).parent.joinpath(f'temp/clones/{project}/pom.xml'), 'w') as f:
            f.write(pom_content)

    cmd = f'mvn clean compile -U -B -Dmaven.compiler.failOnError=false'

    if verbose:
        mvn = subprocess.run(cmd,
                             cwd=Path(__file__).parent.joinpath("temp/clones/" + project),
                             shell=True)
        compilation_completed = True if mvn.returncode == 0 else False
    else:
        mvn = subprocess.run(cmd,
                             cwd=Path(__file__).parent.joinpath("temp/clones/" + project),
                             shell=True, stdout=subprocess.PIPE, text=True)
        compilation_completed = True if mvn.returncode == 0 and "BUILD SUCCESS" in mvn.stdout else False

    os.remove(Path(__file__).parent.joinpath(f'temp/clones/{project}/pom.xml'))

    if compilation_completed:
        cmd = f'sonar-scanner -Dsonar.login={SQ_TOKEN} ' \
              f'-Dsonar.projectKey={project} -Dsonar.projectBaseDir=temp/clones/{project} ' \
              f'-Dsonar.sources=. -Dsonar.java.binaries=.'

        if verbose:
            sonar_scanner = subprocess.run(cmd, cwd=Path(__file__).parent, shell=True)
            return True if sonar_scanner.returncode == 0 else False
        else:
            sonar_scanner = subprocess.run(cmd, cwd=Path(__file__).parent, shell=True, stdout=subprocess.PIPE,
                                           text=True)
            return True if sonar_scanner.returncode == 0 and "EXECUTION SUCCESS" in sonar_scanner.stdout else False
    else:
        return False


def sq_scanner_jvalue(project: str, verbose: bool = False) -> bool:
    """
    Performs the analysis by building with Gradle and then invoking SonarScanner CLI.

    :param project: project key on the SonarQube server
    :param verbose: if True all Maven log will be printed to the console

    :return: True if the build succeed, False otherwise. N.B. if verbose=True, the detection of build success could be
    less accurate
    """
    if Path(__file__).parent.joinpath(f'temp/clones/{project}/adapter').exists():
        with open(Path(__file__).parent.joinpath(
                f'temp/clones/{project}/adapter/gradle/wrapper/gradle-wrapper.properties'), 'r') as f:
            content = f.read()

        content = re.sub("gradle-[0-9a-zA-Z._-]*.zip", "gradle-7.6.3-bin.zip", content)

        with open(Path(__file__).parent.joinpath(
                f'temp/clones/{project}/adapter/gradle/wrapper/gradle-wrapper.properties'), 'w') as f:
            f.write(content)

        with open(Path(__file__).parent.joinpath(f'temp/clones/{project}/adapter/build.gradle'), 'r') as f:
            content = f.read()

        content = re.sub("id 'io.freefair.lombok' version '[0-9a-zA-Z._-]*'", "id 'io.freefair.lombok' version '8.4'",
                         content)

        with open(Path(__file__).parent.joinpath(f'temp/clones/{project}/adapter/build.gradle'), 'w') as f:
            f.write(content)

        cmd = f'./gradlew clean classes'

        if verbose:
            gradle = subprocess.run(cmd,
                                    cwd=Path(__file__).parent.joinpath("temp/clones/" + project + "/adapter"),
                                    shell=True)
            compilation_completed = True if gradle.returncode == 0 else False
        else:
            gradle = subprocess.run(cmd,
                                    cwd=Path(__file__).parent.joinpath("temp/clones/" + project + "/adapter"),
                                    shell=True, stdout=subprocess.PIPE, text=True)
            compilation_completed = True if gradle.returncode == 0 and "BUILD SUCCESSFUL" in gradle.stdout else False
    else:
        compilation_completed = True

    if compilation_completed:
        cmd = f'sonar-scanner -Dsonar.login={SQ_TOKEN} ' \
              f'-Dsonar.projectKey={project} -Dsonar.projectBaseDir=temp/clones/{project} ' \
              f'-Dsonar.sources=. -Dsonar.java.binaries=.'

        if verbose:
            sonar_scanner = subprocess.run(cmd, cwd=Path(__file__).parent, shell=True)
            return True if sonar_scanner.returncode == 0 else False
        else:
            sonar_scanner = subprocess.run(cmd, cwd=Path(__file__).parent, shell=True, stdout=subprocess.PIPE,
                                           text=True)
            return True if sonar_scanner.returncode == 0 and "EXECUTION SUCCESS" in sonar_scanner.stdout else False
    else:
        return False


def sq_scanner_opentelemetry(project: str, verbose: bool = False) -> bool:
    """
    Performs the analysis by building with Gradle a portion and then invoking SonarScanner CLI.

    :param project: project key on the SonarQube server
    :param verbose: if True all Maven log will be printed to the console

    :return: True if the build succeed, False otherwise. N.B. if verbose=True, the detection of build success could be
    less accurate
    """
    if Path(__file__).parent.joinpath(f'temp/clones/{project}/c').exists():
        cmd = f'./gradlew clean classes'

        if verbose:
            gradle = subprocess.run(cmd,
                                    cwd=Path(__file__).parent.joinpath("temp/clones/" + project + "/src/adservice"),
                                    shell=True)
            compilation_completed = True if gradle.returncode == 0 else False
        else:
            gradle = subprocess.run(cmd,
                                    cwd=Path(__file__).parent.joinpath("temp/clones/" + project + "/src/adservice"),
                                    shell=True, stdout=subprocess.PIPE, text=True)
            compilation_completed = True if gradle.returncode == 0 and "BUILD SUCCESSFUL" in gradle.stdout else False
    else:
        compilation_completed = True

    if compilation_completed:
        cmd = f'sonar-scanner -Dsonar.login={SQ_TOKEN} ' \
              f'-Dsonar.projectKey={project} -Dsonar.projectBaseDir=temp/clones/{project} ' \
              f'-Dsonar.sources=. -Dsonar.java.binaries=.'

        if verbose:
            sonar_scanner = subprocess.run(cmd, cwd=Path(__file__).parent, shell=True)
            return True if sonar_scanner.returncode == 0 else False
        else:
            sonar_scanner = subprocess.run(cmd, cwd=Path(__file__).parent, shell=True, stdout=subprocess.PIPE,
                                           text=True)
            return True if sonar_scanner.returncode == 0 and "EXECUTION SUCCESS" in sonar_scanner.stdout else False
    else:
        return False


def sq_scanner_opencodefoundation(project: str,
                                  verbose: bool = False, debug: bool = False,
                                  all_builds: bool = True) -> bool:
    """
    Performs the analysis by building with .NET and invoking SonarScanner for .NET.

    :param project: project key on the SonarQube server
    :param verbose: if True all .NET log will be printed to the console
    :param debug: True if you want to run sonar scanner in debug/verbose mode
    :param all_builds: True if you want to analyze also failing build

    :return: True if the build succeed, False otherwise. N.B. if verbose=True, the detection of build success could be
    less accurate
    """
    return sq_scanner_dotnet(project, solution='eSchool.sln',
                             verbose=verbose, debug=debug,
                             all_builds=all_builds)


def sq_scanner_asclab(project: str, verbose: bool = False) -> bool:
    """
    Performs the analysis by building with Maven and then invoking SonarScanner CLI (due to other languages present).
    An aggregator POM will be created by looking for modules because it doesn't exist.

    :param project: project key on the SonarQube server
    :param verbose: if True all Maven log will be printed to the console

    :return: True if the build succeed, False otherwise. N.B. if verbose=True, the detection of build success could be
    less accurate
    """
    modules = locate_files(str(Path(__file__).parent.joinpath(f'temp/clones/{project}')), 'pom.xml')
    modules = [module for module in modules if "example" not in module]

    pom_content = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' \
                  '<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">\n' \
                  '<modelVersion>4.0.0</modelVersion>\n' \
                  '<groupId>asc-lab</groupId>\n' \
                  '<artifactId>micronaut-microservices-poc</artifactId>\n' \
                  '<version>0.0.1-SNAPSHOT</version>\n' \
                  '<packaging>pom</packaging>\n' \
                  '<name>micronaut-microservices-poc</name>\n' \
                  '<modules>\n'
    for module in modules:
        with open(Path(__file__).parent.joinpath(f'temp/clones/{project}/{module}'), 'r') as module_pom:
            module_content = module_pom.read()

        old_lombok_dep = "<groupId>org.projectlombok</groupId>\s*" \
                         "<artifactId>lombok</artifactId>\s*" \
                         "<version>((\$\{[a-zA-z.]*\})|[0-9.]+)</version>"
        new_lombok_dep = "<groupId>org.projectlombok</groupId>\n" \
                         "<artifactId>lombok</artifactId>\n" \
                         "<version>1.18.24</version>"

        old_micronaut_ver0 = "<micronaut.version>1.0[0-9a-zA-Z.]+</micronaut.version>"
        new_micronaut_ver0 = "<micronaut.version>1.0.0</micronaut.version>"

        old_micronaut_ver1 = "<micronaut.version>1.1[0-9a-zA-Z.]+</micronaut.version>"
        new_micronaut_ver1 = "<micronaut.version>1.1.4</micronaut.version>"

        old_micronaut_ver2 = "<micronaut.version>1.2[0-9a-zA-Z.]+</micronaut.version>"
        new_micronaut_ver2 = "<micronaut.version>1.2.0</micronaut.version>"

        old_micronaut_ver3 = "<micronaut.version>1.3[0-9a-zA-Z.]+</micronaut.version>"
        new_micronaut_ver3 = "<micronaut.version>1.3.0</micronaut.version>"

        old_micronaut_ver2m = "<micronaut.version>2[0-9a-zA-Z.]+</micronaut.version>"
        new_micronaut_ver2m = "<micronaut.version>2.1.0</micronaut.version>"

        old_micronaut_name = "<groupId>io.micronaut</groupId>\s*" \
                             "<artifactId>(?!micronaut)"
        new_micronaut_name = "<groupId>io.micronaut</groupId>\n" \
                             "<artifactId>micronaut-"

        old_micronaut_conf_name = "<groupId>io.micronaut.configuration</groupId>\s*" \
                                  "<artifactId>(?!micronaut)"
        new_micronaut_conf_name = "<groupId>io.micronaut.configuration</groupId>\n" \
                                  "<artifactId>micronaut-"

        old_micronaut_par = "<artifactId>micronaut-parent</artifactId>\s*" \
                            "<version>2.4.0</version>"
        new_micronaut_par = "<artifactId>micronaut-parent</artifactId>\n" \
                            "<version>2.2.0</version>"

        old_kotlin_ver = "<kotlin.version>[0-9a-zA-Z.-]+</kotlin.version>"
        new_kotlin_ver = "<kotlin.version>1.8.22</kotlin.version>"

        old_kotlin_ver2 = "<kotlinVersion>[0-9a-zA-Z.-]+</kotlinVersion>"
        new_kotlin_ver2 = "<kotlinVersion>1.8.22</kotlinVersion>"

        module_content = re.sub(old_lombok_dep, new_lombok_dep, module_content)
        module_content = re.sub(old_micronaut_ver0, new_micronaut_ver0, module_content)
        module_content = re.sub(old_micronaut_ver1, new_micronaut_ver1, module_content)
        module_content = re.sub(old_micronaut_ver2, new_micronaut_ver2, module_content)
        module_content = re.sub(old_micronaut_ver3, new_micronaut_ver3, module_content)
        module_content = re.sub(old_micronaut_ver2m, new_micronaut_ver2m, module_content)
        module_content = re.sub(old_micronaut_name, new_micronaut_name, module_content)
        module_content = re.sub(old_micronaut_conf_name, new_micronaut_conf_name, module_content)
        module_content = re.sub(old_micronaut_par, new_micronaut_par, module_content)
        module_content = re.sub(old_kotlin_ver, new_kotlin_ver, module_content)
        module_content = re.sub(old_kotlin_ver2, new_kotlin_ver2, module_content)

        with open(Path(__file__).parent.joinpath(f'temp/clones/{project}/{module}'), 'w') as module_pom:
            module_pom.write(module_content)

        pom_content += f'{"<module>" + module.split("/")[-2] + "</module>"}\n'

    pom_content += '</modules>\n' \
                   '</project>'

    with open(Path(__file__).parent.joinpath(f'temp/clones/{project}/pom.xml'), 'w') as f:
        f.write(pom_content)

    cmd = f'mvn clean compile -U -B -Dmaven.compiler.failOnError=false'

    if verbose:
        mvn = subprocess.run(cmd,
                             cwd=Path(__file__).parent.joinpath("temp/clones/" + project),
                             shell=True)
        compilation_completed = True if mvn.returncode == 0 else False
    else:
        mvn = subprocess.run(cmd,
                             cwd=Path(__file__).parent.joinpath("temp/clones/" + project),
                             shell=True, stdout=subprocess.PIPE, text=True)
        compilation_completed = True if mvn.returncode == 0 and "BUILD SUCCESS" in mvn.stdout else False

    os.remove(Path(__file__).parent.joinpath(f'temp/clones/{project}/pom.xml'))

    if compilation_completed:
        cmd = f'sonar-scanner -Dsonar.login={SQ_TOKEN} ' \
              f'-Dsonar.projectKey={project} -Dsonar.projectBaseDir=temp/clones/{project} ' \
              f'-Dsonar.sources=. -Dsonar.java.binaries=.'

        if verbose:
            sonar_scanner = subprocess.run(cmd, cwd=Path(__file__).parent, shell=True)
            return True if sonar_scanner.returncode == 0 else False
        else:
            sonar_scanner = subprocess.run(cmd, cwd=Path(__file__).parent, shell=True, stdout=subprocess.PIPE,
                                           text=True)
            return True if sonar_scanner.returncode == 0 and "EXECUTION SUCCESS" in sonar_scanner.stdout else False
    else:
        return False


def sq_scanner_netcorebcn(project: str,
                          verbose: bool = False, debug: bool = False,
                          all_builds: bool = True) -> bool:
    """
    Performs the analysis by building with .NET and invoking SonarScanner for .NET. When the solution file is not
    present, it will be created with the ad-hoc script.

    :param project: project key on the SonarQube server
    :param verbose: if True all .NET log will be printed to the console
    :param debug: True if you want to run sonar scanner in debug/verbose mode
    :param all_builds: True if you want to analyze also failing build

    :return: True if the build succeed, False otherwise. N.B. if verbose=True, the detection of build success could be
    less accurate
    """
    if not Path(__file__).parent.joinpath(f'temp/clones/{project}/quiz.sln').exists():
        generation = True

        cmd = './dotnet-slngen'

        if verbose:
            gen = subprocess.run(cmd,
                                 cwd=Path(__file__).parent.joinpath("temp/clones/" + project),
                                 shell=True)
            generation_completed = True if gen.returncode == 0 else False
        else:
            gen = subprocess.run(cmd,
                                 cwd=Path(__file__).parent.joinpath("temp/clones/" + project),
                                 shell=True, stdout=subprocess.PIPE, text=True)
            generation_completed = True if gen.returncode == 0 and "BUILD SUCCESS" in gen.stdout else False

        if generation_completed:
            result = sq_scanner_dotnet(project, solution=f'{project}.sln',
                                       verbose=verbose, debug=debug,
                                       all_builds=all_builds)
            if generation:
                os.remove(Path(__file__).parent.joinpath(f'temp/clones/{project}/{project}.sln'))

            return result
    else:
        return sq_scanner_dotnet(project, solution='quiz.sln',
                                 verbose=verbose, debug=debug,
                                 all_builds=all_builds)


def sq_scanner_dotnetarchitecture(project: str,
                                  verbose: bool = False, debug: bool = False,
                                  all_builds: bool = True) -> bool:
    """
    Performs the analysis by building with .NET and invoking SonarScanner for .NET

    TODO it doesn't work... it seems to have some sort of incompatibility version problem with .NET (?)

    :param project: project key on the SonarQube server
    :param verbose: if True all .NET log will be printed to the console
    :param debug: True if you want to run sonar scanner in debug/verbose mode
    :param all_builds: True if you want to analyze also failing build

    :return: True if the build succeed, False otherwise. N.B. if verbose=True, the detection of build success could be
    less accurate
    """
    if Path(__file__).parent.joinpath(f'temp/clones/{project}/eShopOnContainers.sln').exists():
        glob_file = Path(__file__).parent.joinpath(f'temp/clones/{project}/global.json')
        if glob_file.exists():
            with open(glob_file, 'r') as glob:
                glob_content = glob.read()

            glob_content = re.sub("\"version\": \"[0-9a-zA-Z._-]*\"", "\"version\": \"7.0.114\"", glob_content)

            with open(glob_file, 'w') as pom:
                pom.write(glob_content)

        return sq_scanner_dotnet(project, solution='eShopOnContainers.sln',
                                 verbose=verbose, debug=debug,
                                 all_builds=all_builds)
    else:
        glob_file = Path(__file__).parent.joinpath(f'temp/clones/{project}/src/global.json')
        if glob_file.exists():
            with open(glob_file, 'r') as glob:
                glob_content = glob.read()

            glob_content = re.sub("\"version\": \"[0-9a-zA-Z._-]*\"", "\"version\": \"7.0.114\"", glob_content)

            with open(glob_file, 'w') as pom:
                pom.write(glob_content)

        return sq_scanner_dotnet(project, solution='src/eShopOnContainers-ServicesAndWebApps.sln',
                                 verbose=verbose, debug=debug,
                                 all_builds=all_builds)


def retrieve_sq_metrics(component: str, analysis: dict[str, str | int | None]) -> None:
    """
    Retrieves SonarQube metrics' measures from the SonarQube server

    :param component: project/component key
    :param analysis: dictionary where to save information
    :return: None
    """
    for metric in SQ_METRICS:
        analysis[metric] = sq_measure(component, metric.lower())


def recover_git_infos(git_repo: git.Repo, commit_hash: str, analysis: dict[str, str | int | None]) -> None:
    """
    Recovers information from the Git repository about a commit (author's name and email, committer's name and email
    and number of author and committers up to that commit)

    :param git_repo: Git repository
    :param commit_hash: Commit
    :param analysis: dictionary where to save information
    :return: None
    """
    analysis['PARENT'] = git_repo.git.execute(["git", "log", "-1", "--pretty=%P", commit_hash])
    analysis['AUTHOR_NAME'] = git_repo.git.execute(["git", "show", "-s", "--format='%an'", commit_hash])[1:-1]
    analysis['AUTHOR_EMAIL'] = git_repo.git.execute(["git", "show", "-s", "--format='%ae'", commit_hash])[1:-1]
    analysis['AUTHOR_DATE'] = git_repo.git.execute(["git", "show", "-s", "--format='%as'", commit_hash])[1:-1]
    analysis['COMMITTER_NAME'] = git_repo.git.execute(["git", "show", "-s", "--format='%cn'", commit_hash])[1:-1]
    analysis['COMMITTER_EMAIL'] = git_repo.git.execute(["git", "show", "-s", "--format='%ce'", commit_hash])[1:-1]
    analysis['COMMITTER_DATE'] = git_repo.git.execute(["git", "show", "-s", "--format='%cs'", commit_hash])[1:-1]
    analysis['AUTHORS'] = len(git_repo.git.execute(["git", "shortlog", "HEAD", "-s"]).splitlines())
    analysis['COMMITTERS'] = len(git_repo.git.execute(["git", "shortlog", "HEAD", "-s", "-c"]).splitlines())


def compute_microservice_metric(name: str, workdir: str, analysis: dict[str, str | int | None]) -> None:
    """
    Performs the analysis of the repository with the designed method.

    :param name: name of the repository
    :param workdir: directory of the repository
    :param analysis: dictionary where to save information
    :return: None
    """
    dc = choose_dc(workdir)

    if dc:
        containers = process_services(dc_collect_services(Path(workdir).joinpath(dc)), Path(workdir))
        microservices = determine_microservices(name.split('.')[0], name.split('.')[1], workdir, containers)

        if microservices:
            analysis['MICROSERVICES'] = len(microservices)
        else:
            analysis['MICROSERVICES'] = 0
    else:
        analysis['MICROSERVICES'] = 0


def analyze_all_repos() -> None:
    """
    Run the analysis of all the repos contained in the input file

    :return: None
    """
    print_major_step("# Start dataset analysis")

    dataset_file = Path(__file__).parent / '../data/dataset/dataset.csv'

    repos_count = -1  # We don't want to count header
    for _ in open(dataset_file):
        repos_count += 1

    with (open(dataset_file) as dataset):
        repos = csv.DictReader(dataset, delimiter=',')

        for repo in repos:  # type: dict[str, str]
            print_progress(f'   [{repos.line_num - 1}/{repos_count}]')

            name = repo["URL"].split("/")[-2] + "." + repo["URL"].split("/")[-1]

            ds_output_file = Path(__file__).parent / f'../data/raw/analysis/{name}_repo_analysis.csv'

            with open(ds_output_file, 'w+', newline='') as ds_output:
                ds_writer = csv.DictWriter(ds_output, DS_KEYS)
                ds_writer.writeheader()

                analyze_repo(repo["URL"], ds_writer)


if __name__ == "__main__":
    print_major_step(" Start script execution")
    start_time = time.time()

    print_info(' Starting up SonarQube server')
    sq_start_up()

    try:
        print_info(' Performing analysis')
        analyze_all_repos()
    except Exception as e:
        logging.error("Unexpected error", exc_info=e)
    finally:
        print_info(' Shutting down SonarQube server')
        sq_shut_down()

    print_info(' Terminating script execution')
    stop_time = time.time()
    print_progress(f' Total execution time: {str(timedelta(seconds=(stop_time - start_time)))}')
