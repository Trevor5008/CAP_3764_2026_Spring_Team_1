# CAP 3764 Final Project

## Table of Contents

---

- [1. Problem Statement](#1-problem-statement)
- [2. Data Source (FDOT)](#2-data-source-fdot)
- [3. Feature Engineering (risk_proxy)](#3-feature-engineering-risk_proxy)
- [4. EDA Findings](#4-eda-findings)
- [5. Modeling Approach](#5-modeling-approach)
- [6. Key Insight: Data Leakage](#6-key-insight-data-leakage)
- [7. Conclusion](#7-conclusion)
- [8. Future Work](#8-future-work)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Data Lifecycle](#data-lifecycle)
- [Data Dictionary](#data-dictionary)
- [Developer Reference](#developer-reference)

---

## 1. Problem Statement

Transportation construction in Miami-Dade impacts network performance and mobility. This project investigates which work program segments are **more exposed or potentially impactful**, using only structural and program-level metadata.

We approach this through:

- **Primary objective:** Construct an interpretable **risk proxy** to rank construction segments based on scale and phase
- **Secondary objective:** Evaluate the recoverability of this proxy using supervised modeling, while identifying potential **data leakage**
- This formulation assumes that larger segments and later construction phases correspond to greater operational impact.

## 2. Data Source (FDOT)

Data come from the Florida Department of Transportation (**FDOT**) **Work Program** via the public **ArcGIS REST API**. The pipeline script `src/ingest_work_program.py` downloads Miami-Dade construction segments, validates geometry and location flags, and keeps records where `**LOC_ERROR == "NO ERROR"`**.

**Artifacts used in analysis and modeling:**


| Artifact                                                 | Role                                                                             |
| -------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `src/data/processed/fdot_work_program_construction.gpkg` | GeoPackage after ingest input to `analysis/risk-proxy.ipynb`                    |
| `construction_with_risk_proxy.csv`                       | Tabular export (geometry dropped) with engineered columns including `risk_proxy` |


CRS is **EPSG:4326** (WGS84) $\rightarrow$ *Full field definitions in*: [Data Dictionary](#data-dictionary).

## 3. Feature Engineering (risk_proxy)

Engineering follows `analysis/risk-proxy.ipynb` and the README data dictionary.

- `**Normalized_Length`**: `Shape__Length / max(Shape__Length)` 
- `**PHASE_WEIGHT**`: mapped from `WPPHAZTP` / `WPPHAZTP_DESC` 
- `**risk_proxy**`= Normalized_Length × PHASE_WEIGHT**`  
  - Main engineered signal for ranking and for the baseline model’s **target**.

Optional extensions (e.g. spatial density) are noted in the notebooks but are not required for the current proxy or baseline.

## 4. EDA Findings

Summary of conclusions from `**analysis/risk-proxy.ipynb`** 

- **Temporal coverage:** Fiscal years 2023-2030 are present, project volume is concentrated up to 2026
- **Phase impact:** Mean `risk_proxy` is highest for **Active Construction** and lower for earlier phases (ex. "Contract Executed")
- **Work mix:**: Infrastructure-intensive work types (ex. interchange, lane additions) exhibit higher average `risk_proxy` than maintenance categories (ex. "Landscaping")
- **Correlation / multicollinearity:** Strong linear relationship between `Normalized_Length` and `risk_proxy` (~0.94)
- **Interpretation:** The proxy is dominated by segment length *suggesting that segment scale is the primary driver of the engineered risk signal.*

## 5. Modeling Approach

### 5.1 Initial **Baseline** [model](src/models/baseline_risk_proxy.ipynb)

- A Random Forest Regressor was trained to evaluate the `risk_proxy` target using:
- Data: `construction_with_risk_proxy.csv` (~6,942 rows)
- Feature engineering:
  - Reduced `WPWKMIXN` to top 12 categories (others grouped)
  - 1-hot encoding on **phase type** and **work mix**
- Features used:
  - Numeric: `FISCALYR`, `Shape_Length`
  - Categorical: phase type, reduced work mix
- Model: Random Forest Regressor (200 trees, 80/20 split)
  - $RMSE \approx 0.005$
  - $R^2 \approx 0.997$
- **Segment length** dominates the model, followed by phase-type indicators

### 5.2 $\rightarrow$ Adjusted Baseline [model](src/models/baseline_no_length.ipynb) (leakage mitigation)

> To address leakage, a second baseline model was trained excluding `Shape_Length`, isolating the predictive contribution of contextual features:

- Fiscal Year (`FISCALYR`)
- Construction Phase (`WPPHAZTP_DESC`)
- Work Mix (reduced categories)

**Result:**

- $R^2 \approx$ 0.14

This significant drop in performance confirms that most of the variance in `risk_proxy` is driven by project scale, while contextual features provide limited independent predictive power.

## 6. Key Insight: Data Leakage

> The target variable is defined as: `risk_proxy = Normalized_Length * PHASE_WEIGHT`

Although `Normalized_Length` and `PHASE_WEIGHT` were excluded from the feature matrix, their underlying components (`Shape_Length`, phase-type categories) were included.

As a result:

- The model effectively reconstructs the target function
- The **near-perfect** performance ($R^2 \approx 0.997$) reflects **deterministic structure**, not predictive power
- This is a case of **indirect data leakage**.

### Takeaway

This result confirms that the model is reconstructing the engineered target rather than learning independent relationships. 

> The baseline model therefore serves as a **validation of feature construction**, not a predictive model of real-world outcomes.

## 7. Conclusion

This project demonstrates a complete data science workflow using FDOT construction data using:

- A reproducible FDOT construction dataset
- A transparent and interpretable `risk_proxy`
- EDA validating variance, structure and ranking behavior
- A baseline model that exposes the **deterministic** relationship between engineered features and the target

While an engineered risk proxy enabled ranking and exploratory analysis, modeling revealed that predictive performance is highly sensitive to feature-target relationships.

> After correcting for data leakage, the final baseline model (`baseline_no_length.ipynb`) provides a more realistic estimate of predictive capability.

This reinforces that project scale is the dominant driver of the engineered risk signal, while contextual metadata alone is insufficient for strong prediction.

The project highlights the importance of aligning feature selection with target construction to avoid misleading model performance.

## 8. Future Work

- Introduce external outcome variables (e.g., delays, incidents) to enable true predictive modeling
- Explore alternative baselines (e.g., linear regression, regularized models)
- Incorporate spatial features (e.g., density, network proximity)
- Improve feature engineering beyond direct exposure measures

---
## Project Structure

```text
/analysis
  └── eda.ipynb
  └── analysis_template.ipynb
  └── risk-proxy.ipynb
  └── pca_exploration.ipynb
/docs
  └── DEVELOPER.md
/src
  └── ingest_work_program.py
  └── data/processed/                    # outputs from ingest + EDA export
      └── fdot_work_program_construction.gpkg   # written by ingest_work_program.py
      └── construction_with_risk_proxy.csv      # written by analysis/risk-proxy.ipynb
  └── models/
      └── baseline_risk_proxy.ipynb      # RF baseline with length + categoricals
      └── baseline_no_length.ipynb       # same target; FISCALYR + phase + work mix only
      └── xgboost.ipynb                  # same target and exclusion of length
/data                                    # optional mirror (e.g. raw/ or processed/)
  └── raw/
  └── processed/
LICENSE
team1-ads-env.yml
```
---

## Getting Started

### Environment Setup

**This project requires Anaconda/Conda** — Python 3.11 is recommended.

**Note:** This project is configured for conda environments. Using virtual environments (venv) may cause conflicts with package management and path resolution.

The repository includes a `team1-ads-env.yml` file that defines the full environment (conda and pip dependencies) for consistent setup across the team.

```bash
# Create and activate the environment from .yml file
conda env create -f team1-ads-env.yml
conda activate advds
```

Run notebooks from the repo root (e.g. `jupyter notebook analysis/risk-proxy.ipynb`) after ingesting data.

## Data Lifecycle

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
Processed construction data is written under `src/data/processed/` (e.g. `fdot_work_program_construction.gpkg`). The risk-proxy notebook can export `construction_with_risk_proxy.csv` alongside it.

### Data Dictionary

The ingested dataset comes from FDOT's **Work Program** (planned construction projects). Records represent construction work program item segments. The data is filtered to Miami-Dade County and to records with valid geometry (`LOC_ERROR == "NO ERROR"`). CRS is EPSG:4326 (WGS84).

Current `risk-proxy.ipynb` findings used by this dictionary:

- `WPPHAZGP` has no variance in the construction extract (all `5`), so it is not useful as a risk feature.
- `WPPHAZTP` is used as the phase signal and mapped to interpretable phase categories/weights.
- `Shape_Length` / `Shape__Length` should be **normalized** before contributing to risk score to avoid scale dominance.


| Field                     | Alias / Description             | Type        | Notes                                                                                                                               | Model Role                                       |
| ------------------------- | ------------------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| **Identifiers**           |                                 |             |                                                                                                                                     |                                                  |
| OBJECTID                  | Object ID                       | OID         | Unique feature identifier                                                                                                           | -                                                |
| WPITEM                    | Work Program Item               | string (6)  | Work program item code                                                                                                              | -                                                |
| WPITMSEG                  | Work Program Item Segment       | string (1)  | Segment code                                                                                                                        | -                                                |
| ITMSEG                    | Item And Segment                | string (7)  | Combined item + segment                                                                                                             | -                                                |
| FINPROJ                   | Financial Project Number        | string (11) | Financial project ID                                                                                                                | Join Key Only                                    |
| FINPRJSQ                  | Financial Project Sequence      | string (2)  | Project sequence                                                                                                                    | -                                                |
| **Location / Roadway**    |                                 |             |                                                                                                                                     |                                                  |
| RDWYLOC                   | Roadway Location                | integer     | Roadway location code                                                                                                               | -                                                |
| BEGSECPT                  | Beginning Roadway Section Point | double      | Start milepost                                                                                                                      | -                                                |
| ENDSECPT                  | Ending Roadway Section Point    | double      | End milepost                                                                                                                        | -                                                |
| RDWYSIDE                  | Roadway Side                    | string (1)  | Side of roadway                                                                                                                     | -                                                |
| RDWYID                    | Roadway Id                      | string (8)  | Roadway identifier                                                                                                                  | Grouping / Aggregation Key                       |
| CONTYDOT                  | County DOT Number               | string (2)  | County DOT code                                                                                                                     | -                                                |
| CONTYNAM                  | County Name                     | string (20) | County (e.g. MIAMI-DADE)                                                                                                            | -                                                |
| **Program / Phase**       |                                 |             |                                                                                                                                     |                                                  |
| WPWKMIX                   | Work Program Work Mix Code      | string (4)  | Work mix code                                                                                                                       | -                                                |
| WPWKMIXN                  | Work Mix Name                   | string (20) | Work mix description                                                                                                                | 20-char limit leaves names abbreviated           |
| WPITSTAT                  | Work Program Item Status        | string (3)  | Item status code                                                                                                                    | -                                                |
| WPITSTNM                  | Work Program Item Status Name   | string (20) | Status description                                                                                                                  | -                                                |
| WPPHAZGP                  | Work Program Phase Group        | string (1)  | Phase group (used in risk `phase_weight`)                                                                                           | All == 5 (not usable)                            |
| WPPHAZTP                  | Work Program Phase Type         | string (1)  | Phase type                                                                                                                          | Core feature for risk analysis (needs 1-hot enc) |
| PRPLCCDE                  | Program Plan Category           | string (1)  | Program plan category                                                                                                               | -                                                |
| PRPLCODE                  | Program Plan Subcategory        | string (2)  | Program plan subcategory                                                                                                            | Categorical Feature (Optional)                   |
| MANDISDV                  | Managing District Division      | string (2)  | Managing district/division                                                                                                          | -                                                |
| **Fiscal / Metadata**     |                                 |             |                                                                                                                                     |                                                  |
| FISCALYR                  | Fiscal Year                     | integer     | Fiscal year                                                                                                                         | Temporal Feature                                 |
| ITSEGMAN                  | Manager Name                    | string (20) | Segment manager                                                                                                                     | -                                                |
| **Descriptions**          |                                 |             |                                                                                                                                     |                                                  |
| LOCALFULL                 | Full Description                | string (70) | Full location description                                                                                                           | Unused (Future NLP)                              |
| **Validation / Geometry** |                                 |             |                                                                                                                                     |                                                  |
| LOC_ERROR                 | Location Error                  | string (50) | Only `"NO ERROR"` kept after ingestion                                                                                              | -                                                |
| Shape_Length              | Shape length                    | double      | Segment length (ArcGIS: `Shape_Length`; GeoPackage may use `Shape__Length`); normalize before scoring (`normalized_segment_length`) | Core Feature (Exposure Proxy, normalized)        |
| geometry                  | Geometry                        | geometry    | Spatial features (lines/points/polygons) in EPSG:4326                                                                               | -                                                |


### Analysis & risk scoring

For exploratory analysis aimed at **risk scoring**, use the starter notebooks:

- `**analysis/eda.ipynb`** — Starter EDA: load data, schema, missingness, variance, distributions, correlations, geospatial.
- `**analysis/analysis_template.ipynb**` — Reusable template for iterating on feature hypotheses; copy and fill in for each focused analysis.
- `**analysis/risk-proxy.ipynb**` — Risk proxy construction, EDA, and CSV export for modeling.
- `**src/models/baseline_risk_proxy.ipynb**` — Baseline Random Forest on `risk_proxy`.
- `**src/models/baseline_no_length.ipynb**` — Adjusted Baseline Random Forest on `risk_proxy` (addresses data leakage)

## Developer Reference

For detailed technical documentation, code architecture, API references, and development guidelines, see the **[Developer Reference](docs/DEVELOPER.md)**.