#!/usr/bin/env python3
"""
Strip 'concept/' prefix from tesseract coordinate tags
Restores coordinate system purity while preserving other concept tags
"""

import re
from pathlib import Path
from typing import List, Tuple

# CONFIGURATION
VAULT_PATH = Path("/Users/rickshangle/Vaults/flatline-codex")
DRY_RUN = False  # Set to False to actually modify files

# Coordinate dimensions to fix
COORDINATE_PREFIXES = [
    "x-structure/",
    "y-transmission/",
    "z-purpose/",
    "w-terrain/"
]

def fix_coordinate_tags(content: str) -> Tuple[str, List[str]]:
    """
    Replace concept/[dimension]/ with [dimension]/ for coordinate tags only
    Works in both YAML frontmatter and inline tags
    Returns: (modified_content, list_of_changes)
    """
    changes = []
    modified = content
    
    for dim in COORDINATE_PREFIXES:
        # Pattern 1: YAML list item (  - concept/x-structure/)
        yaml_pattern = f'- concept/{dim}'
        yaml_replacement = f'- {dim}'
        
        # Pattern 2: Inline tag (#concept/x-structure/)
        inline_pattern = f'#concept/{dim}'
        inline_replacement = f'#{dim}'
        
        # Find and replace YAML tags
        yaml_matches = re.findall(re.escape(yaml_pattern) + r'\S+', modified)
        if yaml_matches:
            changes.extend([m.replace('- ', '') for m in yaml_matches])
            modified = modified.replace(yaml_pattern, yaml_replacement)
        
        # Find and replace inline tags
        inline_matches = re.findall(re.escape(inline_pattern) + r'\S+', modified)
        if inline_matches:
            changes.extend(inline_matches)
            modified = modified.replace(inline_pattern, inline_replacement)
    
    return modified, changes

def process_file(file_path: Path) -> dict:
    """Process a single markdown file"""
    try:
        content = file_path.read_text(encoding='utf-8')
        modified_content, changes = fix_coordinate_tags(content)
        
        if changes:
            if not DRY_RUN:
                file_path.write_text(modified_content, encoding='utf-8')
            
            return {
                'file': str(file_path.relative_to(VAULT_PATH)),
                'changes': len(changes),
                'modified': not DRY_RUN,
                'tags_fixed': changes
            }
        
        return None
        
    except Exception as e:
        return {
            'file': str(file_path.relative_to(VAULT_PATH)),
            'error': str(e)
        }

def main():
    """Process all markdown files in vault"""
    
    print("=" * 80)
    print("TESSERACT COORDINATE TAG CLEANUP")
    print("=" * 80)
    print(f"\nVault: {VAULT_PATH}")
    print(f"Mode: {'DRY RUN (no changes)' if DRY_RUN else 'LIVE (will modify files)'}")
    print(f"\nFixing these coordinate dimensions:")
    for dim in COORDINATE_PREFIXES:
        print(f"  #concept/{dim}* -> #{dim}*")
    print("\n" + "-" * 80)
    
    if not DRY_RUN:
        response = input("\n⚠️  LIVE MODE: Files will be modified. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return
    
    # Find all markdown files
    md_files = list(VAULT_PATH.rglob("*.md"))
    print(f"\nScanning {len(md_files)} markdown files...\n")
    
    # Process files
    results = []
    modified_count = 0
    total_changes = 0
    
    for i, file_path in enumerate(md_files, 1):
        if i % 100 == 0:
            print(f"  Progress: {i}/{len(md_files)}")
        
        result = process_file(file_path)
        if result:
            results.append(result)
            if 'changes' in result:
                modified_count += 1
                total_changes += result['changes']
    
    # Report results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"\nFiles scanned: {len(md_files)}")
    print(f"Files with coordinate tags: {modified_count}")
    print(f"Total tag changes: {total_changes}")
    
    if DRY_RUN:
        print(f"\n⚠️  DRY RUN - No files were modified")
        print(f"Set DRY_RUN = False to apply changes")
    else:
        print(f"\n✅ Files modified: {modified_count}")
    
    # Show sample of changes
    print("\n" + "-" * 80)
    print("SAMPLE CHANGES (first 10 files)")
    print("-" * 80)
    
    for result in results[:10]:
        if 'error' in result:
            print(f"\n❌ {result['file']}")
            print(f"   Error: {result['error']}")
        elif 'changes' in result:
            print(f"\n✓ {result['file']}")
            print(f"   Tags fixed: {result['changes']}")
            print(f"   Examples: {', '.join(result['tags_fixed'][:3])}")
    
    if len(results) > 10:
        print(f"\n... and {len(results) - 10} more files")
    
    # Dimension breakdown
    print("\n" + "-" * 80)
    print("COORDINATE DIMENSION BREAKDOWN")
    print("-" * 80)
    
    dim_counts = {dim: 0 for dim in COORDINATE_PREFIXES}
    for result in results:
        if 'tags_fixed' in result:
            for tag in result['tags_fixed']:
                for dim in COORDINATE_PREFIXES:
                    if f'concept/{dim}' in tag:
                        dim_counts[dim] += 1
    
    for dim, count in sorted(dim_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {dim:20s} {count:6d} tags")
    
    print("\n" + "=" * 80)
    
    if DRY_RUN:
        print("\n💡 Next steps:")
        print("   1. Review the sample changes above")
        print("   2. Set DRY_RUN = False in the script")
        print("   3. Run again to apply changes")
        print("   4. Backup is already in place (right?)")

if __name__ == "__main__":
    main()
