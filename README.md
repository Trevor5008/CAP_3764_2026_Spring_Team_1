# CAP 3764 Final Project

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
/notebooks
/src
  └── ingest_work_program.py
environment.yml
```

## Recreate environment
```bash
conda env create -f environment.yml
conda activate advds
```

## Data Ingestion

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
