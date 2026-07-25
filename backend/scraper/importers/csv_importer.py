"""
CSV Importer for manual data uploads.
Supports standardized CSV format for bulk institution data entry.
"""

import logging
from typing import List, Dict, Any, Optional
import csv
import io
from pathlib import Path

from scraper.importers.postgres_importer import DataImporter, ScrapedInstitution

logger = logging.getLogger(__name__)


class CSVImporter:
    """Import institutions from CSV files."""
    
    # Expected CSV columns
    REQUIRED_COLUMNS = ['name_en']
    OPTIONAL_COLUMNS = [
        'name_bn', 'short_name', 'institution_type', 'division',
        'district', 'upazila', 'address', 'phone', 'email', 'website',
        'established_year', 'education_level', 'education_board'
    ]
    
    def __init__(self):
        self.data_importer = DataImporter()
    
    def _validate_csv(self, reader: csv.DictReader) -> List[str]:
        """Validate CSV has required columns."""
        fieldnames = reader.fieldnames or []
        missing = [col for col in self.REQUIRED_COLUMNS if col not in fieldnames]
        return missing
    
    def _parse_row(self, row: Dict[str, str]) -> Optional[ScrapedInstitution]:
        """Parse CSV row into ScrapedInstitution."""
        try:
            # Extract and clean data
            name_en = row.get('name_en', '').strip()
            if not name_en:
                return None
            
            # Parse year
            year_str = row.get('established_year', '')
            established_year = None
            if year_str:
                try:
                    established_year = int(year_str)
                except ValueError:
                    pass
            
            return ScrapedInstitution(
                name_en=name_en,
                name_bn=row.get('name_bn', '').strip() or None,
                short_name=row.get('short_name', '').strip() or None,
                institution_type=row.get('institution_type', 'unknown').strip().lower(),
                division=row.get('division', '').strip() or None,
                district=row.get('district', '').strip() or None,
                upazila=row.get('upazila', '').strip() or None,
                address=row.get('address', '').strip() or None,
                phone=row.get('phone', '').strip() or None,
                email=row.get('email', '').strip() or None,
                website=row.get('website', '').strip() or None,
                established_year=established_year,
                education_level=row.get('education_level', '').strip() or None,
                education_board=row.get('education_board', '').strip() or None,
                data_source='csv_upload',
                source_url=None
            )
        except Exception as e:
            logger.error(f"Error parsing row: {row}. Error: {e}")
            return None
    
    def import_csv(self, file_path: str, data_source: str = "csv_upload") -> Dict[str, Any]:
        """Import institutions from CSV file."""
        path = Path(file_path)
        
        if not path.exists():
            return {'error': f'File not found: {file_path}'}
        
        institutions = []
        errors = []
        
        try:
            with open(path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                # Validate columns
                missing = self._validate_csv(reader)
                if missing:
                    return {
                        'error': f'Missing required columns: {missing}',
                        'expected_columns': self.REQUIRED_COLUMNS + self.OPTIONAL_COLUMNS
                    }
                
                # Parse rows
                for i, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                    institution = self._parse_row(row)
                    if institution:
                        institution.data_source = data_source
                        institutions.append(institution)
                    else:
                        errors.append(f"Row {i}: Failed to parse")
                
        except UnicodeDecodeError:
            # Try with different encoding
            with open(path, 'r', encoding='latin-1') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader, start=2):
                    institution = self._parse_row(row)
                    if institution:
                        institution.data_source = data_source
                        institutions.append(institution)
                    else:
                        errors.append(f"Row {i}: Failed to parse")
        
        # Import to database
        if institutions:
            stats = self.data_importer.bulk_import(institutions)
            return {
                'success': True,
                'total_rows': len(institutions) + len(errors),
                'parsed_successfully': len(institutions),
                'import_stats': stats,
                'errors': errors[:10]  # Limit error output
            }
        
        return {
            'success': False,
            'error': 'No valid institutions found in CSV',
            'errors': errors
        }
    
    def import_from_string(self, csv_content: str, data_source: str = "csv_upload") -> Dict[str, Any]:
        """Import from CSV string (for API uploads)."""
        institutions = []
        errors = []
        
        try:
            f = io.StringIO(csv_content)
            reader = csv.DictReader(f)
            
            # Validate columns
            missing = self._validate_csv(reader)
            if missing:
                return {
                    'error': f'Missing required columns: {missing}',
                    'expected_columns': self.REQUIRED_COLUMNS + self.OPTIONAL_COLUMNS
                }
            
            # Parse rows
            for i, row in enumerate(reader, start=2):
                institution = self._parse_row(row)
                if institution:
                    institution.data_source = data_source
                    institutions.append(institution)
                else:
                    errors.append(f"Row {i}: Failed to parse")
        
        except Exception as e:
            return {
                'success': False,
                'error': f'CSV parsing error: {str(e)}'
            }
        
        # Import to database
        if institutions:
            stats = self.data_importer.bulk_import(institutions)
            return {
                'success': True,
                'total_rows': len(institutions) + len(errors),
                'parsed_successfully': len(institutions),
                'import_stats': stats,
                'errors': errors[:10]
            }
        
        return {
            'success': False,
            'error': 'No valid institutions found in CSV'
        }
    
    def generate_template(self) -> str:
        """Generate CSV template for data entry."""
        all_columns = self.REQUIRED_COLUMNS + self.OPTIONAL_COLUMNS
        
        # Sample data
        sample_data = {
            'name_en': 'Dhaka College',
            'name_bn': 'ঢাকা কলেজ',
            'short_name': 'DC',
            'institution_type': 'college',
            'division': 'Dhaka',
            'district': 'Dhaka',
            'upazila': 'Dhaka',
            'address': 'New Market, Dhaka 1205',
            'phone': '+88029555197',
            'email': 'info@dhakacollege.edu.bd',
            'website': 'https://dhakacollege.edu.bd',
            'established_year': '1841',
            'education_level': 'higher_secondary',
            'education_board': 'Dhaka Board'
        }
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=all_columns)
        writer.writeheader()
        writer.writerow(sample_data)
        
        return output.getvalue()
