# Developer Reference

This document provides technical documentation for developers working on the CAP 3764 Final Project. It covers code architecture, module documentation, development workflows, and common tasks.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Module Documentation](#module-documentation)
- [Data Pipeline](#data-pipeline)
- [Development Workflow](#development-workflow)
- [Code Style & Standards](#code-style--standards)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)

## Architecture Overview

### Project Structure

```
CAP_3764_2026_Spring_Team_1/
├── src/                    # Source code modules
│   └── ingest_work_program.py
├── data/                   # Data storage
│   ├── raw/                # Raw, unprocessed data
│   └── processed/          # Cleaned, validated data
├── analysis/               # Analysis notebooks (EDA, modeling)
├── app/                    # Streamlit application
├── notebooks/              # Additional notebooks
├── docs/                   # Documentation
└── environment.yml         # Conda environment specification
```

### Design Principles

1. **Separation of Concerns**: Data ingestion, processing, and analysis are separated into distinct modules
2. **Data Validation**: All ingested data undergoes validation before persistence
3. **Reproducibility**: Environment and dependencies are version-controlled
4. **Geospatial-First**: Uses GeoPandas and GeoPackage format for spatial data

## Module Documentation

### `src/ingest_work_program.py`

**Purpose**: Fetches, validates, and cleans FDOT Work Program construction data from ArcGIS REST API.

#### Functions

##### `fetch_all(page_size=2000, where="1=1")`

Fetches all features from the FDOT ArcGIS FeatureServer using pagination.

**Parameters**:
- `page_size` (int, optional): Number of records per API request. Default: 2000
- `where` (str, optional): SQL WHERE clause for filtering. Default: "1=1" (all records)

**Returns**:
- `geopandas.GeoDataFrame`: GeoDataFrame containing all matching features with CRS EPSG:4326

**Behavior**:
- Implements pagination using `resultOffset` and `resultRecordCount` parameters
- Automatically stops when no more features are returned or fewer than `page_size` records are returned
- Raises HTTPError on API request failures
- Uses 60-second timeout for API requests

**Example**:
```python
# Fetch all Miami-Dade County records
gdf = fetch_all(where="CONTYNAM = 'MIAMI-DADE'")

# Fetch with custom page size
gdf = fetch_all(page_size=1000, where="CONTYNAM = 'BROWARD'")
```

#### Constants

- `BASE`: ArcGIS REST API endpoint URL
  - Value: `"https://gis.fdot.gov/arcgis/rest/services/Work_Program_Current/FeatureServer/2/query"`

#### Data Processing Pipeline

The script follows this workflow:

1. **Fetch**: Retrieve data from FDOT ArcGIS API
   - Filters for Miami-Dade County (`CONTYNAM = 'MIAMI-DADE'`)
   - Uses pagination to handle large datasets

2. **Validate**: Perform data quality checks
   - Checks for empty geometries
   - Checks for null geometries
   - Validates `LOC_ERROR` field values

3. **Clean**: Filter invalid records
   - Removes rows with empty geometries
   - Removes rows where `LOC_ERROR != "NO ERROR"`

4. **Persist**: Save cleaned data
   - Output format: GeoPackage (`.gpkg`)
   - Output path: `data/processed/fdot_work_program_construction.gpkg`
   - Creates parent directories if they don't exist

#### Output Schema

The output GeoPackage contains:
- **Geometry**: Spatial features (points, lines, or polygons) in EPSG:4326
- **Attributes**: All fields from the ArcGIS FeatureServer (`outFields: "*"`)
- **Key Fields**:
  - `LOC_ERROR`: Location error status (filtered to "NO ERROR" only)
  - `CONTYNAM`: County name (filtered to "MIAMI-DADE")

## Data Pipeline

### Ingestion Flow

```
ArcGIS REST API
    ↓
fetch_all() [Pagination]
    ↓
GeoDataFrame (Raw)
    ↓
Validation Checks
    ↓
Data Cleaning [Filtering]
    ↓
GeoPackage Output
```

### Data Validation Rules

1. **Geometry Validation**:
   - Reject empty geometries: `geometry.is_empty == False`
   - Reject null geometries: `geometry.isna() == False`

2. **Location Error Validation**:
   - Accept only: `LOC_ERROR == "NO ERROR"`

### Output Format

- **Format**: GeoPackage (GPKG)
- **CRS**: EPSG:4326 (WGS84)
- **Location**: `data/processed/fdot_work_program_construction.gpkg`

## Development Workflow

### Setting Up Development Environment

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd CAP_3764_2026_Spring_Team_1
   ```

2. **Create conda environment**:
   ```bash
   conda env create -f environment.yml
   conda activate advds
   ```

3. **Verify installation**:
   ```bash
   python -c "import geopandas; import requests; print('Environment OK')"
   ```

### Running the Ingestion Script

```bash
# From project root
python src/ingest_work_program.py
```

**Expected Output**:
- Shape tuple: `(rows, columns)`
- Validation statistics:
  - Total rows
  - Empty geometries count
  - Null geometries count
  - Location error breakdown

### Adding New Data Sources

To add a new data ingestion script:

1. Create new module in `src/` (e.g., `ingest_<source>.py`)
2. Follow the same pattern:
   - Fetch function with pagination support
   - Validation checks
   - Data cleaning
   - Persistence to `data/processed/`
3. Add documentation to this file
4. Update README.md with usage instructions

### Code Review Checklist

- [ ] Code follows PEP 8 style guidelines
- [ ] Functions have docstrings
- [ ] Error handling is implemented
- [ ] Data validation is performed
- [ ] Output paths use `data/processed/` directory
- [ ] No hardcoded paths (use `Path` from `pathlib`)
- [ ] Environment variables used for sensitive data (if applicable)

## Code Style & Standards

### Python Style Guide

- Follow PEP 8
- Use type hints where appropriate
- Write docstrings for all functions (Google style)
- Maximum line length: 100 characters

### Naming Conventions

- **Functions**: `snake_case` (e.g., `fetch_all`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `BASE`)
- **Files**: `snake_case.py` (e.g., `ingest_work_program.py`)

### Documentation Standards

Functions should include:
- Purpose description
- Parameter documentation
- Return value documentation
- Example usage (for complex functions)

Example:
```python
def fetch_all(page_size=2000, where="1=1"):
    """
    Fetches all features from FDOT ArcGIS FeatureServer using pagination.
    
    Parameters:
    -----------
    page_size : int, optional
        Number of records per API request. Default: 2000
    where : str, optional
        SQL WHERE clause for filtering. Default: "1=1" (all records)
    
    Returns:
    --------
    geopandas.GeoDataFrame
        GeoDataFrame containing all matching features with CRS EPSG:4326
    
    Raises:
    -------
    requests.HTTPError
        If API request fails
    """
```

## Common Tasks

### Fetching Data for Different Counties

```python
from src.ingest_work_program import fetch_all

# Broward County
gdf_broward = fetch_all(where="CONTYNAM = 'BROWARD'")

# Palm Beach County
gdf_palm_beach = fetch_all(where="CONTYNAM = 'PALM BEACH'")
```

### Modifying Validation Rules

Edit the filtering logic in `ingest_work_program.py`:

```python
# Current: Only "NO ERROR"
gdf_clean = gdf[gdf["LOC_ERROR"] == "NO ERROR"]

# Alternative: Include warnings
gdf_clean = gdf[gdf["LOC_ERROR"].isin(["NO ERROR", "WARNING"])]
```

### Reading Processed Data

```python
import geopandas as gpd

# Read the processed GeoPackage
gdf = gpd.read_file("data/processed/fdot_work_program_construction.gpkg")

# Basic info
print(f"Shape: {gdf.shape}")
print(f"CRS: {gdf.crs}")
print(f"Columns: {gdf.columns.tolist()}")
```

### Debugging API Issues

1. **Check API endpoint**:
   ```python
   import requests
   BASE = "https://gis.fdot.gov/arcgis/rest/services/Work_Program_Current/FeatureServer/2/query"
   r = requests.get(BASE, params={"where": "1=1", "f": "json", "resultRecordCount": 1})
   print(r.status_code)
   print(r.json())
   ```

2. **Test pagination**:
   ```python
   # Fetch first page only
   params = {"where": "1=1", "outFields": "*", "f": "geojson", 
             "resultRecordCount": 10, "resultOffset": 0}
   r = requests.get(BASE, params=params)
   data = r.json()
   print(f"Features returned: {len(data.get('features', []))}")
   ```

## Troubleshooting

### Common Issues

#### Issue: `ModuleNotFoundError: No module named 'geopandas'`

**Solution**: Ensure conda environment is activated:
```bash
conda activate advds
conda install geopandas
```

#### Issue: API timeout errors

**Solution**: Increase timeout or reduce page size:
```python
# In fetch_all function, increase timeout
r = requests.get(BASE, params=params, timeout=120)  # 120 seconds

# Or reduce page size
gdf = fetch_all(page_size=1000)  # Smaller batches
```

#### Issue: Empty output file

**Possible Causes**:
1. All records filtered out by validation
2. API returned no data for the filter
3. Network/API issues

**Debugging**:
```python
# Check raw data before filtering
gdf_raw = fetch_all(where="CONTYNAM = 'MIAMI-DADE'")
print(f"Raw records: {len(gdf_raw)}")
print(f"Empty geometries: {gdf_raw.geometry.is_empty.sum()}")
print(f"LOC_ERROR values: {gdf_raw['LOC_ERROR'].value_counts()}")
```

#### Issue: Permission errors writing to `data/processed/`

**Solution**: Ensure directory exists and is writable:
```bash
mkdir -p data/processed
chmod 755 data/processed
```

### Performance Optimization

For large datasets:

1. **Adjust page size**: Larger page sizes reduce API calls but increase memory usage
2. **Add progress logging**: Track pagination progress
3. **Stream processing**: For very large datasets, consider processing in chunks

Example with progress:
```python
def fetch_all(page_size=2000, where="1=1", verbose=False):
    features = []
    offset = 0
    
    while True:
        # ... fetch logic ...
        if verbose:
            print(f"Fetched {offset + len(batch)} records...")
        # ... rest of logic ...
```

## Additional Resources

- [GeoPandas Documentation](https://geopandas.org/)
- [ArcGIS REST API Documentation](https://developers.arcgis.com/rest/)
- [PEP 8 Style Guide](https://pep8.org/)
- [Python Pathlib Documentation](https://docs.python.org/3/library/pathlib.html)
