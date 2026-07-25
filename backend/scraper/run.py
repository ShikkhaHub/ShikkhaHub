#!/usr/bin/env python3
"""
ShikkhaHub Data Scraper Runner.

Usage:
    python run.py --source ugc
    python run.py --source all
    python run.py --source bmeb --import-to-db
    python run.py --csv-file data.csv

"""

import argparse
import logging
import sys
import os
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.scrapers import UGCScraper, BMEBScraper, BTEBScraper, GeneralBoardScraper
from scraper.importers import DataImporter, CSVImporter
from scraper.base import ScrapedInstitution

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_scraper(scraper_class, import_to_db: bool = False) -> List[ScrapedInstitution]:
    """Run a single scraper and optionally import to database."""
    scraper = scraper_class()
    
    try:
        institutions = scraper.scrape()
        stats = scraper.get_stats()
        
        logger.info(f"Scraper completed: {stats}")
        
        if import_to_db and institutions:
            logger.info(f"Importing {len(institutions)} institutions to database...")
            importer = DataImporter()
            import_stats = importer.bulk_import(institutions)
            logger.info(f"Import stats: {import_stats}")
            importer.close()
        
        return institutions
        
    except Exception as e:
        logger.error(f"Scraper failed: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description='ShikkhaHub Data Scraper')
    parser.add_argument('--source', choices=['ugc', 'bmeb', 'bteb', 'board', 'all'], 
                        default='all', help='Data source to scrape')
    parser.add_argument('--board-name', default='dhaka', 
                        help='Specific board name (for --source board)')
    parser.add_argument('--import-to-db', action='store_true',
                        help='Import scraped data to PostgreSQL')
    parser.add_argument('--csv-file', type=str,
                        help='Import from CSV file instead of scraping')
    parser.add_argument('--generate-csv-template', action='store_true',
                        help='Generate CSV template for data entry')
    
    args = parser.parse_args()
    
    # Generate CSV template
    if args.generate_csv_template:
        csv_importer = CSVImporter()
        template = csv_importer.generate_template()
        print(template)
        return
    
    # CSV import mode
    if args.csv_file:
        logger.info(f"Importing from CSV: {args.csv_file}")
        csv_importer = CSVImporter()
        result = csv_importer.import_csv(args.csv_file)
        
        if result.get('success'):
            logger.info(f"CSV import successful: {result['import_stats']}")
        else:
            logger.error(f"CSV import failed: {result.get('error')}")
            sys.exit(1)
        return
    
    # Scraping mode
    all_institutions = []
    
    sources = {
        'ugc': UGCScraper,
        'bmeb': BMEBScraper,
        'bteb': BTEBScraper,
        'board': lambda: GeneralBoardScraper(args.board_name)
    }
    
    if args.source == 'all':
        # Run all scrapers
        for source_name, scraper_class in sources.items():
            if source_name == 'board':
                # Skip board in 'all' mode (requires specific board name)
                continue
            logger.info(f"\n{'='*50}")
            logger.info(f"Running {source_name.upper()} scraper...")
            logger.info(f"{'='*50}")
            institutions = run_scraper(scraper_class, args.import_to_db)
            all_institutions.extend(institutions)
    else:
        # Run specific scraper
        scraper_class = sources.get(args.source)
        if scraper_class:
            institutions = run_scraper(scraper_class, args.import_to_db)
            all_institutions.extend(institutions)
        else:
            logger.error(f"Unknown source: {args.source}")
            sys.exit(1)
    
    logger.info(f"\n{'='*50}")
    logger.info(f"Total institutions scraped: {len(all_institutions)}")
    logger.info(f"{'='*50}")


if __name__ == '__main__':
    main()
