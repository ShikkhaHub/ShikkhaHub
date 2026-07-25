#!/usr/bin/env python3
"""
Case-insensitive find and replace CLI tool for files, directories, and code content.
Supports matching patterns like: Oldname, OldName, OLDNAME
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional


class CaseInsensitiveReplacer:
    def __init__(self, old_pattern: str, new_pattern: str, dry_run: bool = False):
        self.old_pattern = old_pattern
        self.new_pattern = new_pattern
        self.dry_run = dry_run
        self.case_insensitive_regex = re.compile(
            re.escape(old_pattern), re.IGNORECASE
        )
    
    def matches_pattern(self, text: str) -> bool:
        """Check if text matches the old pattern (case-insensitive)."""
        return bool(self.case_insensitive_regex.search(text))
    
    def replace_in_text(self, text: str) -> str:
        """Replace all case-insensitive occurrences in text while preserving case pattern."""
        def replace_match(match):
            original = match.group(0)
            
            # Determine the case pattern of the original text
            if original.isupper():
                # ALL UPPERCASE -> ALL UPPERCASE
                return self.new_pattern.upper()
            elif original.islower():
                # all lowercase -> all lowercase
                return self.new_pattern.lower()
            elif original.istitle():
                # Title Case -> Title Case
                return self.new_pattern.title()
            elif original[0].isupper() and original[1:].islower():
                # CamelCase -> CamelCase
                return self.new_pattern[0].upper() + self.new_pattern[1:].lower()
            else:
                # Mixed case or other patterns -> use new pattern as-is
                return self.new_pattern
        
        return self.case_insensitive_regex.sub(replace_match, text)
    
    def find_and_replace_in_files(self, directory: str, 
                                file_extensions: Optional[List[str]] = None) -> Tuple[int, int]:
        """Find and replace in file contents."""
        files_processed = 0
        replacements_made = 0
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = Path(root) / file
                
                # Skip if file extensions filter is specified and file doesn't match
                if file_extensions and file_path.suffix not in file_extensions:
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if self.matches_pattern(content):
                        new_content = self.replace_in_text(content)
                        
                        if not self.dry_run:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                        
                        files_processed += 1
                        replacements_made += len(self.case_insensitive_regex.findall(content))
                        
                        action = "Would replace" if self.dry_run else "Replaced"
                        print(f"{action} in file: {file_path}")
                        
                except (UnicodeDecodeError, PermissionError) as e:
                    print(f"Skipping file {file_path}: {e}")
        
        return files_processed, replacements_made
    
    def rename_files_and_directories(self, directory: str) -> Tuple[int, int]:
        """Rename files and directories that match the pattern."""
        files_renamed = 0
        dirs_renamed = 0
        
        # Collect all rename operations first
        file_renames = []
        dir_renames = []
        
        # First, collect file rename operations (bottom-up)
        for root, dirs, files in os.walk(directory, topdown=False):
            for file in files:
                old_path = Path(root) / file
                if self.matches_pattern(file):
                    new_name = self.replace_in_text(file)
                    new_path = old_path.parent / new_name
                    
                    if old_path != new_path:
                        file_renames.append((old_path, new_path))
        
        # Then, collect directory rename operations (bottom-up)
        for root, dirs, files in os.walk(directory, topdown=False):
            for dir_name in dirs:
                old_path = Path(root) / dir_name
                if self.matches_pattern(dir_name):
                    new_name = self.replace_in_text(dir_name)
                    new_path = old_path.parent / new_name
                    
                    if old_path != new_path:
                        dir_renames.append((old_path, new_path))
        
        # Execute file renames
        for old_path, new_path in file_renames:
            action = "Would rename" if self.dry_run else "Renamed"
            print(f"{action} file: {old_path} -> {new_path}")
            
            if not self.dry_run:
                try:
                    old_path.rename(new_path)
                    files_renamed += 1
                except OSError as e:
                    print(f"Failed to rename {old_path}: {e}")
            else:
                files_renamed += 1
        
        # Execute directory renames
        for old_path, new_path in dir_renames:
            action = "Would rename" if self.dry_run else "Renamed"
            print(f"{action} directory: {old_path} -> {new_path}")
            
            if not self.dry_run:
                try:
                    old_path.rename(new_path)
                    dirs_renamed += 1
                except OSError as e:
                    print(f"Failed to rename {old_path}: {e}")
            else:
                dirs_renamed += 1
        
        return files_renamed, dirs_renamed


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Case-insensitive find and replace tool for files, directories, and code content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Replace in file contents only
  python replacer.py --content OldName NewName /path/to/project

  # Rename files and directories only
  python replacer.py --rename OldName NewName /path/to/project

  # Replace in content and rename files/directories
  python replacer.py --all OldName NewName /path/to/project

  # Only process specific file types
  python replacer.py --content OldName NewName /path/to/project --extensions .py .js .html

  # Dry run to see what would be changed
  python replacer.py --all --dry-run OldName NewName /path/to/project
        """
    )
    
    parser.add_argument('old_pattern', help='Pattern to search for (case-insensitive)')
    parser.add_argument('new_pattern', help='Replacement pattern')
    parser.add_argument('directory', help='Directory to search in')
    
    parser.add_argument('--content', action='store_true', 
                       help='Replace in file contents')
    parser.add_argument('--rename', action='store_true', 
                       help='Rename files and directories')
    parser.add_argument('--all', action='store_true', 
                       help='Replace in content AND rename files/directories')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be changed without making changes')
    parser.add_argument('--extensions', nargs='+', 
                       help='File extensions to process (e.g., .py .js .html)')
    
    return parser.parse_args()


def main():
    args = parse_arguments()
    
    # Validate arguments
    if not any([args.content, args.rename, args.all]):
        print("Error: Must specify one of --content, --rename, or --all")
        sys.exit(1)
    
    if not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist")
        sys.exit(1)
    
    # Create replacer instance
    replacer = CaseInsensitiveReplacer(args.old_pattern, args.new_pattern, args.dry_run)
    
    print(f"Searching for pattern: {args.old_pattern}")
    print(f"Replacement pattern: {args.new_pattern}")
    print(f"Directory: {args.directory}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print("-" * 50)
    
    total_files_processed = 0
    total_replacements = 0
    total_files_renamed = 0
    total_dirs_renamed = 0
    
    # Process content replacement
    if args.content or args.all:
        print("Processing file contents...")
        files_processed, replacements = replacer.find_and_replace_in_files(
            args.directory, args.extensions
        )
        total_files_processed += files_processed
        total_replacements += replacements
        print(f"Files processed: {files_processed}, Replacements: {replacements}")
        print()
    
    # Process file/directory renaming
    if args.rename or args.all:
        print("Processing file and directory names...")
        files_renamed, dirs_renamed = replacer.rename_files_and_directories(args.directory)
        total_files_renamed += files_renamed
        total_dirs_renamed += dirs_renamed
        print(f"Files renamed: {files_renamed}, Directories renamed: {dirs_renamed}")
        print()
    
    # Summary
    print("=" * 50)
    print("SUMMARY:")
    print(f"Files with content changes: {total_files_processed}")
    print(f"Total content replacements: {total_replacements}")
    print(f"Files renamed: {total_files_renamed}")
    print(f"Directories renamed: {total_dirs_renamed}")
    
    if args.dry_run:
        print("\nThis was a DRY RUN. No changes were made.")
        print("Run without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
