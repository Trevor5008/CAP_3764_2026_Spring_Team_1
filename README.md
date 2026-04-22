# CAP 3764 Final Project

## Table of Contents

---

- [1. Project Goal](#1-project-goal)
- [2. Problem Statement](#2-problem-statement)
- [3. Risk Proxy Justification](#3-risk-proxy-justification)
- [4. Data Source (FDOT)](#4-data-source-fdot)
- [5. Feature Engineering (risk_proxy)](#5-feature-engineering-risk_proxy)
- [6. EDA Findings](#6-eda-findings)
- [7. Modeling Approach](#7-modeling-approach)
- [8. Conclusion](#8-conclusion)
- [9. Future Work](#9-future-work)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [FastAPI Backend](#fastapi-backend)
- [Data Lifecycle](#data-lifecycle)
- [Data Dictionary](#data-dictionary)
- [Developer Reference](#developer-reference)

---
## 1. Project Goal

The objective of this project is to develop and evaluate a **proxy-based** risk scoring framework for FDOT construction segments using available structural and categorical features.

Given the absence of outcome-based variables (e.g. delays, cost overruns), this project also assesses whether the dataset supports predictive modeling of the constructed risk proxy.

## 2. Problem Statement

This project evaluates whether structural and program-level metadata alone can meaningfully explain variation in an engineered proxy for construction risk.

We approach this through:

- **Primary objective:** Construct an interpretable **risk proxy** to rank construction segments based on scale (geographic) and project phase.

## 3. Risk Proxy Justification

**Risk Proxy Definition**: In the absence of direct outcome measures, risk is approximated as exposure.
- Segment Length (`Shape__Length`) reflects the spatial scope of potential disruption, while construction phase (`WPPHAZTP`) represents operational intensity
- This proxy is intended for ranking and exploratory analysis rather than representing a true outcome variable.

## 4. Data Source (FDOT)

Data come from the Florida Department of Transportation (**FDOT**) **Work Program** via the public **ArcGIS REST API**. 
- The pipeline script `src/ingest_work_program.py` downloads Miami-Dade construction segments, validates geometry and location flags, and keeps records where **`LOC_ERROR == "NO ERROR"`**.

**Artifacts used in analysis and modeling:**


| Artifact                                                 | Role                                                                             |
| -------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `src/data/processed/fdot_work_program_construction.gpkg` | GeoPackage after ingest input to `analysis/risk-proxy.ipynb`                    |
| `construction_with_risk_proxy.csv`                       | Tabular export (geometry dropped) with engineered columns including `risk_proxy` |


CRS is **EPSG:4326** (WGS84) $\rightarrow$ *Full field definitions in*: [Data Dictionary](#data-dictionary).

## 5. Feature Engineering (risk_proxy)

Engineering follows `analysis/risk-proxy.ipynb` and the README data dictionary.

- **`Normalized_Length`**: `Shape__Length / max(Shape__Length)` (unitless scale within the extract).
- **`PHASE_WEIGHT`**: mapped from `WPPHAZTP` / `WPPHAZTP_DESC` (ordinal weights for phase intensity).
- **`risk_proxy`**: `Normalized_Length × PHASE_WEIGHT` — main engineered signal for ranking and the supervised **target**.

## 6. EDA Findings

Summary of conclusions from `analysis/risk-proxy.ipynb`.

- **Temporal coverage:** Fiscal years 2023-2030 are present, project volume is concentrated up to 2026
- **Phase impact:** Mean `risk_proxy` is highest for **Active Construction** and lower for earlier phases (ex. "Contract Executed")
- **Work mix:** Infrastructure-intensive work types (ex. interchange, lane additions) exhibit higher average `risk_proxy` than maintenance categories (ex. "Landscaping")
- **Correlation / multicollinearity:** Strong linear relationship between `Normalized_Length` and `risk_proxy` (~0.94)
- **Interpretation:** The proxy is dominated by segment length (`Shape__Length`), and indicates that segment scale is the dominant driver of our engineered risk signal.

## 7. Modeling Approach

### 7.1 Primary result: Random Forest **without** segment length [baseline_no_length.ipynb](src/models/baseline_no_length.ipynb)

- **Target:** `risk_proxy` (engineered from segment length and phase _length excluded from final random forest regressor model inputs_).
- **Data:** `construction_with_risk_proxy.csv` (~6,942 rows).
- **Features:** `FISCALYR`, construction phase (`WPPHAZTP_DESC`), work mix (reduced top categories, one-hot encoded with phase).
- **Initial holdout split:** $R^2 \approx 0.1416$.
- **5-fold cross-validated tuning (`GridSearchCV`)**: best mean CV score $R^2 \approx 0.135$ with `n_estimators=800`, `max_depth=None`.
- **Tuned model on holdout split:** $R^2 \approx 0.1431$.
- **Interpretation:** the CV score is slightly lower than the single-split score because CV is more conservative, but all values are close and tell the same story: metadata alone explains only a small fraction of proxy variance once **scale** (`Shape__Length`) is withheld.

### 7.2 Diagnostic: Random Forest **with** `Shape__Length` [baseline_risk_proxy.ipynb](src/models/baseline_risk_proxy.ipynb)

- **Result:** $R^2 \approx 0.997$, $RMSE \approx 0.005$.
- **Interpretation:** The target is deterministically constructed from segment length via normalization and phase, making it inherently predictable when those features are included.  

### 7.3 Advanced model [xgboost.ipynb](src/models/xgboost.ipynb)

Further method comparison (e.g. gradient boosting) on the same target and feature policy; see notebook for details.
- XGBoost produced only a marginal improvement over the no-length Random Forest (R² ~0.15 vs ~0.14), which was not large enough to materially change conclusions given the added model complexity.
- Because this comparison uses holdout scores, a shared cross-validation comparison (as in Section 7.1) is needed for a stronger model-selection claim.

## 8. Conclusion

This project demonstrates a complete data science workflow using FDOT construction data using...

- A reproducible FDOT construction dataset
- A transparent and interpretable `risk_proxy`
- EDA validating variance, structure and ranking behavior
- A baseline model that exposes the **deterministic** relationship between engineered features and the target

While an engineered risk proxy enabled ranking and exploratory analysis, modeling revealed that predictive performance is highly sensitive to feature-target relationships.

> After restricting features so the target is not trivially reconstructible from `Shape__Length`, the no-length baseline remains in the same low-signal range across evaluation methods (single split: $R^2 \approx 0.1416$; tuned 5-fold CV mean: $R^2 \approx 0.135$; tuned holdout: $R^2 \approx 0.1431$).

This reinforces that project scale is the dominant driver of the engineered risk signal, while contextual metadata alone is insufficient for strong prediction.

In conclusion, the dataset supports descriptive ranking of construction exposure, but does **not** currently provide sufficient signal for predictive modeling of independent risk outcomes.

## 9. Future Work

1. Introduce external outcome variables (e.g., delays, incidents) to enable true predictive modeling
2. Explore alternative baselines (e.g., linear regression, regularized models)
3. Incorporate spatial features (e.g., density, network proximity)
4. Improve feature engineering beyond direct exposure measures
5. Reframe problem as **classification** if applicable outcome labels become available (see point 1)

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

**Note:** This project is configured for conda environments. 
*Using virtual environments (venv) may cause conflicts with package management and path resolution.*

- The repository includes a `team1-ads-env.yml` file that defines the full environment (conda and pip dependencies) for consistent setup across the team.

```bash
# Create and activate the environment from .yml file
conda env create -f team1-ads-env.yml
conda activate advds
```

Run notebooks from the repo root (e.g. `jupyter notebook analysis/risk-proxy.ipynb`) after ingesting data.

## FastAPI Backend

The repository includes a FastAPI backend in `src/main.py` that loads the trained model from
`src/models/rf_model.pkl` and exposes service endpoints.

### Run the API locally

```bash
# From project root
cd src
uvicorn main:app --reload
```

Default local URL: `http://127.0.0.1:8000`

### Available endpoints

- `GET /` - Simple HTML landing page
- `GET /health` - Health check showing service status and model load status

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

- `analysis/eda.ipynb` — Starter EDA: load data, schema, missingness, variance, distributions, correlations, geospatial.
- `analysis/analysis_template.ipynb` — Reusable template for iterating on feature hypotheses; copy and fill in for each focused analysis.
- `analysis/risk-proxy.ipynb` — Risk proxy construction, EDA, and CSV export for modeling.
- `src/models/baseline_risk_proxy.ipynb` — Diagnostic Random Forest on `risk_proxy` (includes segment length).
- `src/models/baseline_no_length.ipynb` — Primary Random Forest on `risk_proxy` (no segment length; appropriate baseline for reporting).

## Developer Reference

For detailed technical documentation, code architecture, API references, and development guidelines, see the **[Developer Reference](docs/DEVELOPER.md)**.