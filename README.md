# CAP 3764 Final Project

## Overview
...

## Table of Contents
- [Project Goals](#project-goals)
- [Project Structure](#project-structure)
- [Workflow](#workflow)
- [Getting Started](#getting-started)
- [Data Lifecycle](#data-lifecycle)
- [Developer Reference](#developer-reference)
- [Contributing](#contributing)
- [Notes](#notes)

## Project Goals
...

## Project Structure
```text
/analysis
  └── eda.ipynb
  └── modeling.ipynb
/app
  └── streamlit_app.py
/data
  └── raw/
  └── processed/
    └── fdot_work_program_construction.gpkg
/docs
  └── DEVELOPER.md
/notebooks
/src
  └── ingest_work_program.py
environment.yml
```

## Workflow
This project follows an **Agile sprint-based workflow**:
- Work is tracked using GitHub Issues and Projects
- Each sprint includes planning, daily scrums, review and retrospective
- Tickets define **scope**, **ownership**, and **definitions of done**

## Getting Started

### Environment Setup
**This project requires Anaconda/Conda** - Python 3.11 is recommended.

**Note:** This project is configured for conda environments. Using virtual environments (venv) may cause conflicts with package management and path resolution.

The repository includes an `environment.yml` file that defines the full environment (conda and pip dependencies) for consistent setup across the team.


```bash
# Create and activate the environment from `environment.yml`
conda env create -f environment.yml
conda activate advds
```

## Data Lifecycle
...

### FDOT Work Program Construction Data

The `ingest_work_program.py` script fetches, validates, and cleans construction work program data from the Florida Department of Transportation (FDOT) ArcGIS REST API.

**Features:**
- **Data Ingestion**: Fetches Miami-Dade County construction work program data from FDOT's public ArcGIS FeatureServer
- **Validation**: Performs basic data quality checks including:
  - Empty geometry detection
  - Null geometry detection
  - Location error validation
- **Data Cleaning**: Filters out invalid records by:
  - Removing rows with empty geometries
  - Removing rows with location errors (keeps only records where `LOC_ERROR == "NO ERROR"`)

**Usage:**
```bash
python src/ingest_work_program.py
```

**Output:**
The processed data is saved to `data/processed/fdot_work_program_construction.gpkg` as a GeoPackage file.

## Developer Reference

For detailed technical documentation, code architecture, API references, and development guidelines, see the **[Developer Reference](docs/DEVELOPER.md)**.

The developer documentation includes:
- **Module Documentation**: Detailed function and API documentation
- **Architecture Overview**: Project structure and design principles
- **Data Pipeline**: Ingestion flow and validation rules
- **Development Workflow**: Setup, testing, and code review guidelines
- **Common Tasks**: Examples and code snippets for frequent operations
- **Troubleshooting**: Solutions to common issues

This reference is intended for developers working on the project and future collaborators who need to understand or extend the codebase.

## Contributing
...

## Notes
...
