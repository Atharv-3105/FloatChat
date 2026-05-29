import requests
import re
from pathlib import Path
import sys

# Ensure the script can find the 'app' module
sys.path.append(str(Path(__file__).parent.parent))

from app.logging_config import logger

BASE_URL = "https://data-argo.ifremer.fr/geo/indian_ocean/"
RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

def download_file(url: str, dest_path: Path):
    """
    Downloads a file from a URL to a destination path, skipping if it already exists.
    """
    if dest_path.exists():
        logger.info(f"Skipping existing file: {dest_path.name}")
        return

    logger.info(f"Downloading {url}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        logger.info(f"  -> Saved to {dest_path.name}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}. Error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while downloading {url}. Error: {e}")


def main():
    """
    Main function to download ARGO data for a specified year and months.
    """
    logger.info("=" * 60)
    logger.info("🌊 Starting ARGO Data Downloader")
    logger.info("=" * 60)

    RAW_DIR.mkdir(exist_ok=True)

    YEAR = 2026
    # As per the user request, download data for the first 5 months
    MONTHS_TO_DOWNLOAD = range(1, 6) 

    for month in MONTHS_TO_DOWNLOAD:
        month_str = f"{month:02d}"
        month_url = f"{BASE_URL}{YEAR}/{month_str}/"

        logger.info(f"--- Checking month: {YEAR}-{month_str} ---")

        try:
            # Get the directory listing page
            response = requests.get(month_url)
            response.raise_for_status()

            # Find all links to _prof.nc files
            # Example: <a href="20260101_prof.nc">20260101_prof.nc</a>
            file_names = re.findall(r'href="(\d{8}_prof\.nc)"', response.text)

            if not file_names:
                logger.info("  No profile files found for this month.")
                continue

            logger.info(f"  Found {len(file_names)} profile files.")

            for file_name in file_names:
                file_url = f"{month_url}{file_name}"
                dest_path = RAW_DIR / file_name
                download_file(file_url, dest_path)

        except requests.exceptions.RequestException as e:
            logger.warning(f"Could not access {month_url}. Maybe it doesn't exist yet. Error: {e}")
        
        except Exception as e:
            logger.error(f"An unexpected error occurred while processing month {month_str}. Error: {e}", exc_info=True)
    
    logger.info("=" * 60)
    logger.info("✅ Download process finished.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
