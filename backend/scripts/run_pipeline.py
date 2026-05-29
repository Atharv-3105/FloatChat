import subprocess
import sys
from pathlib import Path

# Ensure the script's directory is in the python path
script_dir = Path(__file__).parent
sys.path.append(str(script_dir.parent))

from app.logging_config import logger

def run_script(script_name: str):
    """Runs a python script using the same interpreter and returns its exit code."""
    script_path = script_dir / script_name
    logger.info(f"--- Running script: {script_name} ---")
    
    try:
        # Using sys.executable ensures we use the same python environment
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        logger.info(f"Output from {script_name}:\n{result.stdout}")
        if result.stderr:
            logger.warning(f"Stderr from {script_name}:\n{result.stderr}")
        logger.info(f"--- Finished script: {script_name} successfully ---")
        return 0
    except subprocess.CalledProcessError as e:
        logger.error(f"!!! Script failed: {script_name} !!!")
        logger.error(f"Exit Code: {e.returncode}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        return e.returncode
    except Exception as e:
        logger.error(f"An unexpected error occurred while running {script_name}: {e}", exc_info=True)
        return 1

def main():
    """
    Main pipeline execution function.
    1. Downloads new data.
    2. Converts and loads data into the database.
    """
    logger.info("=" * 60)
    logger.info("🚀 Starting Data Pipeline")
    logger.info("=" * 60)

    # Step 1: Download new data
    logger.info("STEP 1: Downloading new data files...")
    exit_code = run_script("download_data.py")
    if exit_code != 0:
        logger.error("Download step failed. Aborting pipeline.")
        return

    # Step 2: Convert and load data
    logger.info("STEP 2: Converting and loading data into database...")
    exit_code = run_script("convert_NC.py")
    if exit_code != 0:
        logger.error("Conversion step failed.")
        return

    logger.info("=" * 60)
    logger.info("✅ Pipeline finished successfully!")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
