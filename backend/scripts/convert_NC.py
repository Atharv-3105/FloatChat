#!/usr/bin/env python3
"""
ARGO NetCDF to SQLite Converter - FINAL VERSION
Tested with INCOIS ARGO profile data structure
"""

import xarray as xr
import sqlite3
from pathlib import Path
from datetime import datetime
import numpy as np
import traceback

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
DB_PATH = Path(__file__).parent.parent / "data" / "processed" / "argodata.db"


def safe_float(value, default=None):
    """Safely convert to float"""
    if value is None:
        return default
    try:
        if isinstance(value, (np.integer, np.int64, np.int32, np.float32, np.float64)):
            if np.isnan(value) or np.isinf(value):
                return default
            return float(value)
        val = float(value)
        if np.isnan(val) or np.isinf(val):
            return default
        return val
    except (TypeError, ValueError, OverflowError):
        return default


def decode_qc(qc_value):
    """Decode QC flag from bytes to string"""
    if qc_value is None:
        return None
    try:
        if isinstance(qc_value, bytes):
            return qc_value.decode('utf-8', errors='ignore').strip()
        return str(qc_value).strip()
    except:
        return None


def extract_argo_data(netcdf_path):
    """Extract oceanographic data from ARGO NetCDF profile file"""
    print(f"Processing: {netcdf_path.name}....")
    
    try:
        ds = xr.open_dataset(netcdf_path)
        
        # === VALIDATION ===
        n_prof = ds.sizes.get('N_PROF', 0)
        n_levels = ds.sizes.get('N_LEVELS', 0)
        
        if n_prof < 1 or n_levels < 10:
            print(f"  ⚠️ Skipping: Invalid dimensions (N_PROF={n_prof}, N_LEVELS={n_levels})")
            ds.close()
            return []
        
        print(f"  Dimensions: N_PROF={n_prof}, N_LEVELS={n_levels}")
        
        # === EXTRACT VARIABLES ===
        lat = ds.get("LATITUDE")
        lon = ds.get("LONGITUDE")
        juld = ds.get("JULD")  # Already datetime64, no conversion needed!
        pres = ds.get("PRES")
        temp = ds.get("TEMP")
        psal = ds.get("PSAL")
        platform = ds.get("PLATFORM_NUMBER")
        cycle = ds.get("CYCLE_NUMBER")
        
        # QC flags
        temp_qc = ds.get("TEMP_QC", None)
        pres_qc = ds.get("PRES_QC", None)
        
        # Validate required variables
        if lat is None or pres is None or temp is None:
            print(f"  ⚠️ Missing required variables")
            ds.close()
            return []
        
        print(f"  TEMP shape: {temp.shape}, Range: [{float(temp.min().values):.2f}, {float(temp.max().values):.2f}]°C")
        print(f"  PRES shape: {pres.shape}, Range: [{float(pres.min().values):.2f}, {float(pres.max().values):.2f}] dbar")
        
        # === EXTRACT DATA ===
        data_rows = []
        
        for i in range(min(n_prof, 100)):  # Process up to 100 profiles per file
            try:
                # Extract per-profile metadata
                if platform is not None and i < len(platform.values):
                    platform_val = platform.values[i]
                    if isinstance(platform_val, bytes):
                        float_id = platform_val.decode('utf-8', errors='ignore').strip()
                    else:
                        float_id = str(platform_val).strip()
                else:
                    float_id = netcdf_path.stem.split("_")[0]
                
                if cycle is not None and i < len(cycle.values):
                    cycle_number = int(cycle.values[i])
                else:
                    cycle_number = i + 1
                
                # Extract position (one per profile)
                if i < len(lat.values):
                    current_lat = safe_float(lat.values[i])
                    current_lon = safe_float(lon.values[i]) if lon is not None else current_lat
                else:
                    continue
                
                if current_lat is None or current_lon is None:
                    continue
                
                # Extract datetime (already datetime64, no conversion needed!)
                if juld is not None and i < len(juld.values):
                    juld_val = juld.values[i]
                    # Convert numpy datetime64 to Python datetime
                    if hasattr(juld_val, 'astype'):
                        current_date = juld_val.astype('datetime64[s]').astype(datetime)
                    else:
                        current_date = juld_val
                else:
                    current_date = None
                
                # Extract depth profile data
                for j in range(min(n_levels, 200)):  # Limit to 200 depth levels per profile
                    try:
                        # Extract measurements at this depth level
                        if temp.ndim == 2 and i < temp.shape[0] and j < temp.shape[1]:
                            temperature = safe_float(temp.values[i, j])
                            pressure = safe_float(pres.values[i, j])
                            salinity = safe_float(psal.values[i, j]) if psal is not None else None
                        else:
                            continue
                        
                        # Validate data
                        if temperature is None or pressure is None:
                            continue
                        
                        # Temperature range check (-5 to 40°C)
                        if not (-5 < temperature < 40):
                            continue
                        
                        # Pressure range check (0 to 7000 dbar)
                        if not (0 < pressure < 7000):
                            continue
                        
                        # QC flag check (1=good, 2=probably good, 3=questionable)
                        if temp_qc is not None and temp_qc.ndim == 2:
                            if i < temp_qc.shape[0] and j < temp_qc.shape[1]:
                                qc_val = decode_qc(temp_qc.values[i, j])
                                if qc_val not in ["1", "2", "3"]:
                                    continue
                        
                        # Create row
                        row = {
                            "float_id": float_id,
                            "latitude": current_lat,
                            "longitude": current_lon,
                            "date": current_date.isoformat() if current_date else None,
                            "cycle_number": cycle_number,
                            "pressure": pressure,
                            "temperature": temperature,
                            "salinity": salinity,
                        }
                        
                        data_rows.append(row)
                        
                    except Exception:
                        continue
                
            except Exception as e:
                print(f"  Error at profile {i}: {str(e)}")
                continue
        
        print(f"  ✅ Extracted {len(data_rows)} valid observations")
        ds.close()
        return data_rows

    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        traceback.print_exc()
        return []


def create_database():
    """Create SQLite database and tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS argo_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            float_id TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            date TEXT,
            cycle_number INTEGER,
            pressure REAL NOT NULL,
            temperature REAL NOT NULL,
            salinity REAL
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_float_id ON argo_data(float_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_lat_lon ON argo_data(latitude, longitude)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_pressure ON argo_data(pressure)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON argo_data(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_float_cycle ON argo_data(float_id, cycle_number)')
    
    conn.commit()
    conn.close()
    print("✅ DATABASE created successfully")


def load_to_sqlite(data_rows):
    """Insert extracted data into SQLite database"""
    if not data_rows:
        print("⚠️ No data to insert")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.executemany('''
        INSERT INTO argo_data (float_id, latitude, longitude, date, cycle_number, pressure, temperature, salinity)
        VALUES (:float_id, :latitude, :longitude, :date, :cycle_number, :pressure, :temperature, :salinity)
    ''', data_rows)
    
    conn.commit()
    conn.close()
    print(f"✅ Loaded {len(data_rows)} records to database")


def main():
    """Main execution function"""
    print("=" * 60)
    print("🌊 ARGO NetCDF to SQLite Converter (FINAL)")
    print("=" * 60)
    
    # Create database
    create_database()
    
    # Get count before
    conn = sqlite3.connect(DB_PATH)
    before_count = conn.execute("SELECT COUNT(*) FROM argo_data").fetchone()[0]
    conn.close()
    print(f"📊 Records before: {before_count}")
    
    # Find all NetCDF files
    netcdf_files = list(RAW_DIR.rglob("*.nc")) + list(RAW_DIR.rglob("*.nc4"))
    netcdf_files = [f for f in netcdf_files if "prof" in f.stem.lower()]
    netcdf_files = [f for f in netcdf_files if f.stat().st_size > 50 * 1024]
    
    print(f"📁 Found {len(netcdf_files)} valid profile files")
    
    if not netcdf_files:
        print("⚠️ No valid profile files found!")
        return
    
    all_data = []
    
    # TEST MODE - first 3 files
    test_mode = True
    if test_mode:
        print("🧪 TEST MODE: Processing first 3 files only")
        print("   Set test_mode = False to process ALL files\n")
        netcdf_files = netcdf_files[:3]
    else:
        print()
    
    for i, nc_file in enumerate(netcdf_files):
        print(f"[{i+1}/{len(netcdf_files)}]")
        rows = extract_argo_data(nc_file)
        print(f"  → Got {len(rows)} rows\n")
        all_data.extend(rows)
    
    # Load to SQLite
    load_to_sqlite(all_data)
    
    # Get count after
    conn = sqlite3.connect(DB_PATH)
    after_count = conn.execute("SELECT COUNT(*) FROM argo_data").fetchone()[0]
    conn.close()
    
    print(f"📊 Records after: {after_count}")
    print(f"➕ Added: {after_count - before_count} new records")
    print("=" * 60)
    print("✅ Conversion completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()