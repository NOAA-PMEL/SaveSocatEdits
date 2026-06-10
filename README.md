# SaveSocatEdits

A FastAPI application for managing and updating WOCE (World Ocean Circulation Experiment) flag edits in SOCAT (Surface Ocean CO₂ Atlas) netCDF datasets.

## Overview

SaveSocatEdits provides a REST API for:
- WOCE Flag Updates: Modify quality control flags for oceanographic observations in netCDF files
- Observation Matching: Find specific observations in netCDF datasets using latitude, longitude, time, and CO₂ measurements
- Bulk Edits: Process multiple observation records simultaneously with tolerance-based matching

## Project Structure

| File/Directory | Purpose                                                                   |
|---|---------------------------------------------------------------------------|
| main.py | FastAPI application and core logic                                        |
| config.py | Configuration management using Pydantic                                   |
| config.yaml | Configuration file with database and paths                                |
| test_main.http | HTTP request examples                                                     |
| dsg/ | Example NetCDF data files organized by cruise code used in the tests      |
| dec_dsg/ | Decimated files created after the WOCE edit DSG directory (examples only) |

## Setup

Prerequisites:
- Python 3.12.10 or compatible
- Virtual environment (virtualenv)

Installation:
1. cd SaveSocatEdits
2. Activate virtual environment: .venv\Scripts\activate (Windows) or source .venv/bin/activate (macOS/Linux)
3. pip install -r requirements.txt

Configuration:

Edit config.yaml with your settings:
```
# config.yaml
# Will read MYSQL info from the environment variables SOCAT_EDIT_MYSQL_USERNAME and SOCAT_EDIT_MYSQL_PASSWORD
SOCAT_VERSION: SOCAT_v2026
dsg_file_dir: C:/Users/schweitzer/Documents/IntellijProjects/SaveSocatEdits/dsg
dec_dsg_file_dir: C:/Users/schweitzer/Documents/IntellijProjects/SaveSocatEdits/dec_dsg
database:
  user: $SOCAT_EDIT_MYSQL_USERNAME
  password: $SOCAT_EIDT_MYSQL_PASSWORD
  host: sour.pmel.noaa.gov
  port: 3306
  driver: mysql+pymysql
  database: SOCATv2025
```


See the internal documentation for how to run this on hazy:
https://docs.google.com/document/d/1iAsTPnfV8bI0EFlSjGUiWuXiM4tfMbWcdBUeMT42dJs/edit?tab=t.0

## API Endpoints

GET /

Returns HTML dashboard with application status.

Request:
GET http://host:port/
Accept: application/json
Content-Type: text/html

Response: HTML with SOCAT_VERSION and database info

POST /SaveEdits

Updates WOCE flags and saves observation edits to netCDF files.

Request:
POST http://host:port/SaveEdits
Content-Type: application/json
```
{
    "expocode": "MLYD20231002",
    "reviewer_email": "reviewer@example.com",
    "woce_flag_name": "WOCE_CO2_water",
    "woce_flag_value": 9,
    "data_variable_name": "fCO2_recommended",
    "comment": "Quality control update",
    "locations": [
        {"longitude": 135.2843, "latitude": 34.6279, "fCO2_recommended": 223.54503295443286, "time": "2023-10-26T21:28:30Z"}
    ]
}
```
Request Parameters:
- expocode (string, required): Cruise identifier
- reviewer_email (string): Email of reviewer
- woce_flag_name (string, required): WOCE flag variable name
- woce_flag_value (integer, required): New flag value
- data_variable_name (string): Data variable name (default: fCO2_recommended)
- comment (string): Description of changes
- locations (array, required): List of observations

Location Object:
- longitude (float): Observation longitude
- latitude (float): Observation latitude
- fCO2_recommended (float): CO2 measurement value
- time (string, ISO 8601): Observation timestamp

Response:
```
{
"message": "Saved edits for MLYD20231002"
}
```
Matching Tolerances:
- Coordinates: ±1e-5 degrees
- Values: ±1e-4 units
- Time: ±1 second

## Core Functions

_find_observation_indices(dataset, sequence, data_variable_name)

Locates observations in netCDF file with tolerance-based fuzzy matching.

Parameters:
- dataset: netCDF4 Dataset object
- sequence: List of observation dictionaries
- data_variable_name: Data variable name (default: fCO2_recommended)

Returns: (matched_indices, failed_matches)

Algorithm:
1. Load coordinate and data arrays into memory
2. Create vectorized boolean masks for comparisons
3. Refine matches using time validation
4. Return indices for batch updates

## Testing

Use test_main.http in IntelliJ IDEA:
1. Open test_main.http
2. Click green play button next to each request
3. View responses in HTTP client pane

## Database Schema

WOCEEvents Table:
- woce_id (Primary key)
- woce_name (Event name/description)
- woce_flag (Quality flag code)
- woce_time (Timestamp in seconds)
- expocode (Cruise identifier)
- reviewer_id (User who made change)
- woce_comment (Change notes)

WOCELocations Table:
- wloc_id (Primary key)
- woce_id (Foreign key to WOCEEvents)
- row_num (Index in netCDF file)
- longitude (Observation longitude)
- latitude (Observation latitude)
- data_time (Measurement timestamp in seconds)
- data_value (Observation value)

## Logging

Uses Python logging with DEBUG level.
Logs output to stdout.
Includes: file operations, match statistics, error details.

## Dependencies

- click
- numpy
- netCDF4
- sqlalchemy
- pydantic
- pyyaml
- python-dateutil
- fastapi
- uvicorn

## Security Notes

- Database credentials in config.yaml - do not commit
- Uses yaml.safe_load() for security
- Input validation via Pydantic
- NetCDF files opened with read-write access only as needed

## Support

SOCAT documentation: https://www.socat.info/
FastAPI documentation: https://fastapi.tiangolo.com/

Last Updated: 2026-06-09
SOCAT Version: v2026