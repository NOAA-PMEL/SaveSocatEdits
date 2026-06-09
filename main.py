from fastapi import FastAPI
from config import settings
from config import engine
from fastapi.responses import HTMLResponse
import netCDF4 as nc
import numpy as np
from dateutil import parser
from datetime import timezone, datetime
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

app = FastAPI()

def _find_observation_indices(dataset, sequence, data_variable_name="fCO2_recommended"):
    """
    Finds the indices in the netCDF file that match the input sequence.
    Returns: (list_of_found_indices, list_of_failed_matches)
    """
    # 1. Load the coordinate arrays into memory for speed
    # We assume these are 1D arrays (the 'row' dimension)
    nc_lats = dataset.variables['latitude'][:]
    nc_lons = dataset.variables['longitude'][:]
    nc_vals = dataset.variables[data_variable_name][:]

    # Handle Time: convert netCDF time to datetime objects or vice-versa
    # netCDF4's num2date is the standard way to handle this
    time_var = dataset.variables['time']
    nc_times = nc.num2date(time_var[:], units=time_var.units, calendar=getattr(time_var, 'calendar', 'standard'))
    found_indices = []
    failed_matches = []

    # 2. Precision tolerances
    COORD_TOLERANCE = 1e-5
    VALUE_TOLERANCE = 1e-4

    for obs in sequence:
        # Parse target time from JSON
        target_time = parser.isoparse(obs['time'])
        if target_time.tzinfo is None:
            target_time = target_time.replace(tzinfo=timezone.utc)

        # 3. Create a boolean mask for matching
        # Vectorized comparison is much faster than a nested loop
        mask = (
                (np.abs(nc_lats - obs['latitude']) < COORD_TOLERANCE) &
                (np.abs(nc_lons - obs['longitude']) < COORD_TOLERANCE) &
                (np.abs(nc_vals - obs['fCO2_recommended']) < VALUE_TOLERANCE)
        )

        # Further refine mask by time (exact match usually works for datetime objects)
        # but we use a small timedelta just in case of sub-second drift
        matching_indices = np.where(mask)[0]

        final_idx = None
        for idx in matching_indices:
            cf_dt = nc_times[idx]
            standard_dt = datetime(cf_dt.year, cf_dt.month, cf_dt.day, cf_dt.hour, cf_dt.minute, cf_dt.second)

            # 2. Add the UTC timezone
            standard_dt = standard_dt.replace(tzinfo=timezone.utc)
            # NetCDF times are often stored as masked arrays or objects
            if abs((standard_dt - target_time).total_seconds()) < 1:
                final_idx = int(idx)
                break

        if final_idx is not None:
            found_indices.append(final_idx)
        else:
            failed_matches.append(obs)

    return found_indices, failed_matches


### Action 1: WOCE Flag Update
@app.post("/SaveEdits")
async def save_edits(data: dict):

    # N.B. The woce_time values are bigint holding SECONDS.
    # These are the columns in the WOCEEvents table:
    # woce_id | woce_name    | woce_flag | woce_time  | expocode     | socat_version | data_name | reviewer_id | woce_comment

    # N.B. date_time is bigint seconds.
    # These are the columns in the WOCELocations table (wode_id is fk to the table above):
    # wloc_id | woce_id | row_num | longitude  | latitude   | data_time | data_value

    # 1. Extract data
    expocode = data['expocode'].strip()
    prefix = expocode[:4]
    path = f"{settings.dsg_file_dir}/{prefix}/{expocode}.nc"
    logger.debug(f"Opening {path}")
    ds = nc.Dataset(path, 'r+')
    woce_flag_name = data['woce_flag_name'].strip()
    woce_flag_value = str(data['woce_flag_value']).strip()
    locations = data['locations']  # List of {date, lat, lon, value}

    # 1. Find the indices of the observations
    matches, failed_matches = _find_observation_indices(ds, locations)

    # 2. Perform the update
    if matches:
        # Update the specific variable at the found indices
        # NumPy slicing/indexing works directly on netCDF variables
        ds.variables[woce_flag_name][matches] = woce_flag_value
        ds.close() # Changes are flushed to disk here

    if failed_matches:
        logger.error(f"Number of failed matches for {expocode}: {len(failed_matches)}")

    logger.debug(f"Changed {len(matches)} matches for {expocode}")


    return {"message": f"Saved edits for {expocode}"}


@app.get("/", response_class=HTMLResponse)
async def root():
    message = f"""
        <!DOCTYPE html>
        <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>Configure Test Results</title>
            </head>
            <body>
                <pre>
                SOCAT_VERSION: {settings.SOCAT_VERSION}
                Database:
                    host: {settings.database.host}
                    port: {settings.database.port}
                <pre>
            </body>
        </html>

    """
    return message
