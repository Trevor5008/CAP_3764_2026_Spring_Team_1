# CAP 3764 Final Project

## Overview

**Abstract**: Impact Analysis of FDOT Construction Projects on Miami-Dade Transportation to identify projects that present the greatest potential impact on navigation throughout the area.  Using geospatial features such as roadway length, construction phase and spatial density we construct an unsupervised risk proxy score that ranks projects based on structural characteristics.

**Introduction**: Transportation construction projects have had a dramatic impact on traffic flow across Miami-Dade county.  Identifying which projects are likely to have the greatest impact can help planners prioritize monitoring and mitigation efforts.

## Table of Contents
- [Project Goals](#project-goals)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Data Lifecycle](#data-lifecycle)
- [Data Dictionary](#data-dictionary)
- [Developer Reference](#developer-reference)
- [Contributing](#contributing)
- [Notes](#notes)

## Project Goals
Using project data from Florida Department of Transportation, our team aims to construct a risk-proxy score for specified projects.  

*We will accomplish this utlizing Unsupervised Learning.*

### The following prerequisites we've identified:
- Stable distributions
- Interpretable feature relationships
- Reasonable proxy construction
- Exploratory Data Analysis (EDA) must prove:
    - [ ] Feature variance
    - [ ] Non-pathological distributions (no single feature dominance)
    - [ ] Correlated structure
    - [ ] Interpretability

**Target**: Impact score / risk ranking
```python
# Proposed formula
# Aggregates normalized structural features (scale, effect)
impact_score = 
  normalized_segment_length
  + phase_weight
  + spatial_density
```

Our model will answer the question:
"Given the structure of the data, which projects look more extreme or potentially impactful?"

*We view this project as an unsupervised risk proxy analysis, where impact is inferred from spatial and temporal characteristics, rather than from labeled outcomes (supervised).* 

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
team1-ads-env.yml
```

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

### Data Dictionary

The ingested dataset comes from FDOT's **Work Program** (planned construction projects). Records represent construction work program item segments. The data is filtered to Miami-Dade County and to records with valid geometry (`LOC_ERROR == "NO ERROR"`). CRS is EPSG:4326 (WGS84).

| Field | Alias / Description | Type | Notes |
|-------|---------------------|------|-------|
| **Identifiers** | | | |
| OBJECTID | Object ID | OID | Unique feature identifier |
| WPITEM | Work Program Item | string (6) | Work program item code |
| WPITMSEG | Work Program Item Segment | string (1) | Segment code |
| ITMSEG | Item And Segment | string (7) | Combined item + segment |
| FINPROJ | Financial Project Number | string (11) | Financial project ID |
| FINPRJSQ | Financial Project Sequence | string (2) | Project sequence |
| **Location / Roadway** | | | |
| RDWYLOC | Roadway Location | integer | Roadway location code |
| BEGSECPT | Beginning Roadway Section Point | double | Start milepost |
| ENDSECPT | Ending Roadway Section Point | double | End milepost |
| RDWYSIDE | Roadway Side | string (1) | Side of roadway |
| RDWYID | Roadway Id | string (8) | Roadway identifier |
| CONTYDOT | County DOT Number | string (2) | County DOT code |
| CONTYNAM | County Name | string (20) | County (e.g. MIAMI-DADE) |
| **Program / Phase** | | | |
| WPWKMIX | Work Program Work Mix Code | string (4) | Work mix code |
| WPWKMIXN | Work Mix Name | string (20) | Work mix description |
| WPITSTAT | Work Program Item Status | string (3) | Item status code |
| WPITSTNM | Work Program Item Status Name | string (20) | Status description |
| WPPHAZGP | Work Program Phase Group | string (1) | Phase group (used in risk `phase_weight`) |
| WPPHAZTP | Work Program Phase Type | string (1) | Phase type |
| PRPLCCDE | Program Plan Category | string (1) | Program plan category |
| PRPLCODE | Program Plan Subcategory | string (2) | Program plan subcategory |
| MANDISDV | Managing District Division | string (2) | Managing district/division |
| **Fiscal / Metadata** | | | |
| FISCALYR | Fiscal Year | integer | Fiscal year |
| ITSEGMAN | Manager Name | string (20) | Segment manager |
| **Descriptions** | | | |
| LOCALFULL | Full Description | string (70) | Full location description |
| **Validation / Geometry** | | | |
| LOC_ERROR | Location Error | string (50) | Only `"NO ERROR"` kept after ingestion |
| Shape_Length | Shape length | double | Segment length (ArcGIS: `Shape_Length`; GeoPackage may use `Shape__Length`) |
| geometry | Geometry | geometry | Spatial features (lines/points/polygons) in EPSG:4326 |

### Analysis & risk scoring

For exploratory analysis aimed at **risk scoring**, use the EDA guide and starter notebook:

- **[EDA for risk scoring](docs/EDA_RISK_SCORING.md)** — Checklist for feature variance, distribution quality, and modeling feasibility.
- **`analysis/eda.ipynb`** — Starter EDA: load data, schema, missingness, variance, distributions, correlations, geospatial.

Run the notebook from the repo root (e.g. `jupyter notebook analysis/eda.ipynb`) after ingesting data.

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
In-progress...

## Notes
In-progress...