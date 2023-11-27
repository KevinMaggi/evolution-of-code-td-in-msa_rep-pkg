# Analysis of the Evolution of Code Techinical Debt in Microservices Architectures

Replication package for the master thesis work entitled:
> Kevin Maggi. 2023. "Analysis of the Evolution of Code Techinical Debt in Microservices Architectures".

in Computer Engineering at University of Florence, under the supervision of Ph.D. Roberto Verdecchia and Prof. Enrico Vicario and co-supervision of Ph.D. Leonardo Scommegna

It contains all the material required for replicating the study, including: scripts and configurations for the dataset selection, scripts and configurations for the data mining (i.e. dataset code quality analysis via Sonar tool suite), and scripts for statistical data analysis.

## How to cite me

```
@mastersthesis{MaggiEvolution,
  author  = {Kevin Maggi},
  title   = {Analysis of the {E}volution of {C}ode {T}echinical {D}ebt in {M}icroservices {A}rchitectures},
  school  = {Università degli Studi di Firenze},
  year    = {2023},
  type    = {Master Thesis},
  month   = {Dec}
}
```

## Quick start
Here a documentation on how to use the replication material should be provided.

### Getting started

- Creating dataset:

        python3 -m src.0_dataset_creation

- Mining repositories:

        python3 -m src.1_mining

- Analyzing data:

        Rscript src/2_data_analysis.R

## Repository Structure
This is the root directory of the repository. The directory is structured as follows:

    code-quality-evolution-in-microservices-context_rep-pkg
     .
     |
     |--- data/                              Raw data from middle phases and final outcomes
     |      |
     |      |--- dataset/                    Raw results from queries, filtered lists and final dataset
     |      |      |
     |      |      |--- plots/               Preliminary number of microservices plots
     |      |      |
     |      |      |--- dataset.csv          Final dataset
     |      |      |
     |      |      |--- evolution.csv        Dataset stats
     |      |
     |      |--- raw/                        Results from the repository mining phase
     |      |      |
     |      |      |--- analysis/            Raw results from mining
     |      |      |
     |      |      |--- analysis_cleaned/    Cleaned results
     |      |
     |      |--- final/                      Outcomes from the data analysis phase
     |      |
     |      |--- utility/                    Utility data results
     |
     |--- src/                               Scripts used in the paper
            |
            |--- dataset_creation/           Scripts used for the repositories selection
            |
            |--- utils/                      Small utility "libraries"
            |
            |--- config.py                   Configurations parameters
            |
            |--- 0_dataset_creation.py       Script for the creation of dataset
            |
            |--- 1_mining.py                 Script for the mining of repositories
            |
            |--- 2_data_analysis.r           Script for statistical analysis of results
            |
            |--- dc_analysis.py              Library implementing method for microservices detection


## License
The source code is licensed under the MIT license, which you can find in the [LICENSE file](LICENSE).

All graphical/text assets are licensed under the [Creative Commons Attribution 4.0 (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
