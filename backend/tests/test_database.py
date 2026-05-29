import sys 
from pathlib import Path 

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text 
from app.config import settings  

def test_db_connection():
    print("TEST:1 DATABASE CONNECTION")
    print("="*50)
    
    try:
        
        engine = create_engine(
            settings.DATABASE_URL.replace("+aiosqlite", ""),
            connect_args = {"check_same_thread" :False}
        )
        
        with engine.connect() as conn:
            
            result = conn.execute(text("SELECT COUNT(*) FROM argo_data"))
            count = result.fetchone()[0]
            
            print(f"[TEST] Database connected successfully")
            print(f"[TEST] Total Records: {count:,} ")
            
            if count > 0:
                #Sample data check 
                result = conn.execute(text("""
                                           
                                           SELECT float_id, latitude, longitude, temperature, pressure, salinity
                                           FROM argo_data
                                           LIMIT 5
                                           """))
                
                print(f"\n[TEST] Sample Data:")
                for row in result:
                    print(f" FLoat: {row.float_id}, Lat: {row.latitude:.2f},  "
                          f"Lon: {row.longitude:.2f}, Temp: {row.temperature:.2f}°C, "
                          f"Pressure: {row.pressure:.2f} dbar")
                    
            
            return count > 0
        
    except Exception as e:
        print(f"[TEST] Database connection failed: {e}")
        return False
    finally:
        if 'engine' in locals():
            engine.dispose()
            print("[TEST] Engine disposed.")
    
    
def test_data_quality():
    print("[TEST:2] Data Quality")
    print("="*50)
    
    try:
        engine = create_engine()