#!/usr/bin/env python3
"""
Test script to verify Obsidian YAML compatibility
Run this to ensure the new YAML generation works correctly
"""

import sys
from pathlib import Path

# Add the app directory to path so we can import utils
sys.path.append(str(Path(__file__).parent / "app"))

from utils import generate_obsidian_yaml, parse_yaml_frontmatter, validate_obsidian_properties

def test_yaml_generation():
    """Test the new Obsidian-compatible YAML generation"""
    print("Testing Obsidian YAML Compatibility")
    print("=" * 50)
    
    # Test case 1: Basic tags and aliases
    sample_data = {
        'tags': ['flatline', 'protocol', 'memoir', 'recovery'],
        'aliases': ['Test Document', 'Sample Entry'],
        'date': '2025-09-13',
        'category': 'recovery',
        'inload_date': '2025-09-13'
    }
    
    print("Test 1: Basic YAML generation")
    yaml_output = generate_obsidian_yaml(sample_data)
    print(yaml_output)
    print()
    
    # Test case 2: Empty tags/aliases
    empty_data = {
        'date': '2025-09-13',
        'category': 'test'
    }
    
    print("Test 2: Empty tags/aliases")
    yaml_output2 = generate_obsidian_yaml(empty_data)
    print(yaml_output2)
    print()
    
    # Test case 3: Parse back and validate
    print("Test 3: Round-trip parsing validation")
    fake_content = f"{yaml_output}\n\nThis is the content of the document."
    parsed_back = parse_yaml_frontmatter(fake_content)
    print(f"Parsed back: {parsed_back}")
    
    is_valid = validate_obsidian_properties(parsed_back)
    print(f"Obsidian compatible: {is_valid}")
    print()
    
    # Test case 4: Problem cases that should be fixed
    problem_data = {
        'tag': ['this-should-be-tags'],  # Wrong property name
        'alias': ['this-should-be-aliases'],  # Wrong property name
        'tags': 'single-string-not-list',  # Wrong format
    }
    
    print("Test 4: Problem case detection")
    is_problem_valid = validate_obsidian_properties(problem_data)
    print(f"Problem data valid: {is_problem_valid} (should be False)")
    print()
    
    return yaml_output

def test_critical_consolidations():
    """Test the critical tag consolidations"""
    from utils import CRITICAL_CONSOLIDATIONS
    
    print("Critical Tag Consolidations Available:")
    print("=" * 50)
    
    print(f"Total mappings: {len(CRITICAL_CONSOLIDATIONS)}")
    print("\nSample mappings:")
    
    # Show some key consolidations
    key_consolidations = [
        ("flatline-codex", "flatline"),
        ("archetypes", "archetype"), 
        ("#summonings", "summonings"),
        ("colors/0A0A23", "colors-0a0a23"),
        ("memoir-buffer", "memoir")
    ]
    
    for old_tag, expected in key_consolidations:
        actual = CRITICAL_CONSOLIDATIONS.get(old_tag, "NOT FOUND")
        status = "✅" if actual == expected else "❌"
        print(f"  {status} {old_tag} -> {actual}")
    
    print(f"\nHash prefix removals: {len([k for k in CRITICAL_CONSOLIDATIONS.keys() if k.startswith('#')])}")
    print(f"Case normalizations: {len([k for k in CRITICAL_CONSOLIDATIONS.keys() if any(c.isupper() for c in k)])}")
    print(f"Path flattening: {len([k for k in CRITICAL_CONSOLIDATIONS.keys() if '/' in k])}")

def simulate_tag_consolidation():
    """Simulate tag consolidation on sample content"""
    from utils import apply_tag_consolidation, CRITICAL_CONSOLIDATIONS
    
    print("Simulating Tag Consolidation")
    print("=" * 50)
    
    # Sample markdown content with problematic tags
    sample_content = """---
tags:
  - flatline-codex
  - archetypes
  - #summonings
  - memoir-buffer
aliases: []
date: "2025-09-13"
---

# Test Document

This document contains some inline tags like #protocols and #FLATLINE.
It also references #memoir-as-resistance and other tags that should be consolidated.

The color tag colors/0A0A23 should also be normalized.
"""
    
    print("Original content:")
    print(sample_content)
    print("\n" + "="*30 + "\n")
    
    # Apply consolidation
    updated_content, changes = apply_tag_consolidation(sample_content, CRITICAL_CONSOLIDATIONS)
    
    print("Updated content:")
    print(updated_content)
    print(f"\nChanges made ({len(changes)}):")
    for change in changes:
        print(f"  - {change}")

if __name__ == "__main__":
    print("Flatdrop Obsidian Compatibility Test")
    print("=" * 60)
    print()
    
    try:
        # Run all tests
        test_yaml_generation()
        test_critical_consolidations()
        simulate_tag_consolidation()
        
        print("✅ All tests completed successfully!")
        print("\nNext steps:")
        print("1. Update your utils.py with the new functions")
        print("2. Update routes.py with the new tag management endpoints")
        print("3. Run a tag audit: GET /api/tags/audit")
        print("4. Create a backup: POST /api/backup/create") 
        print("5. Run consolidation in dry-run mode: POST /api/tags/consolidate?dry_run=true")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
