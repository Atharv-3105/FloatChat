import xarray as xr
from pathlib import Path 

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

nc_files = list(RAW_DIR.rglob("*_prof.nc"))
if not nc_files:
    print("No profile files found!")
    exit()
    
nc_file = nc_files[0]
print(f"DEBUGGING: {nc_file.name}")
print("="*50)

ds = xr.open_dataset(nc_file)

print("DIMENSIONS")
for dim, size in ds.sizes.items():
    print(f"{dim} : {size}")
    
print("VARIABLES")
for var in ds.data_vars:
    v = ds[var]
    print(f"  {var}: ")
    print(f" Shape: {v.shape}")
    print(f" Dims:  {v.dims}")
    print(f" Dtype: {v.dtype}")
    
    if v.shape == ():
        print(f" Value: {v.values}")
    elif len(v.shape) == 1 and v.shape[0] < 20:
        print(f" Sample: {v.values[:5]}")
    elif len(v.shape) == 2:
        print(f"  Sample [0, :5]: {v.values[0, :5] if v.shape[0] > 0 else 'N/A'}")
        
print("CORE OCEAN VARIABLES")
for var_name in ["TEMP", "PRES", "PSAL", "LATITUDE", "LONGITUDE", "JULD"]:
    if var_name in ds:
        v = ds[var_name]
        print(f"\n {var_name}:")
        print(f" Shape: {v.shape}")
        print(f" Dims:  {v.dims}")
        print(f" Min:   {float(v.min().values) if v.size > 0 else 'N/A'}")
        print(f" Max:   {float(v.max().values) if v.size > 0 else 'N/A'}")
        print(f" Sample values:  {v.values.flatten()[:10]}")
        
        
ds.close()
print("="*50)