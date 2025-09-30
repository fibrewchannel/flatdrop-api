#!/usr/bin/env python3
"""
Working Tag Consolidation Fix
Uses Rick's existing API endpoints that actually work

Based on analysis of routes.py, the working endpoints are:
- /api/tags/cleanup-placeholders (removes REMOVE_* tags)
- /api/tags/execute-technical-cleanup (removes numbers, standardizes formats)
"""

import requests
import json
import sys

API_BASE = "http://localhost:5050"

def main():
    print("🔧 WORKING TAG CONSOLIDATION FIX")
    print("Using your actual working API endpoints")
    print("=" * 50)
    
    execute_changes = "--execute" in sys.argv
    
    if not execute_changes:
        print("🔍 DRY RUN MODE - No files will be changed")
        print("Use --execute to apply changes")
    else:
        confirm = input("⚡ EXECUTE MODE: Type 'YES' to apply changes: ")
        if confirm != "YES":
            print("Cancelled.")
            return
    
    results = []
    
    # Step 1: Clean up placeholder tags from previous consolidation attempts
    print("\n🧹 STEP 1: Cleaning up consolidation artifacts...")
    try:
        response = requests.post(
            f"{API_BASE}/api/tags/cleanup-placeholders",
            json={"dry_run": not execute_changes}
        )
        if response.status_code == 200:
            result1 = response.json()
            results.append(("cleanup_placeholders", result1))
            print(f"   ✅ Placeholder cleanup: {result1.get('placeholder_tags_removed', 0)} tags removed")
        else:
            print(f"   ❌ Placeholder cleanup failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Step 2: Execute technical cleanup (numbers, format standardization)
    print("\n🔧 STEP 2: Technical cleanup (numbers, format standards)...")
    try:
        response = requests.post(
            f"{API_BASE}/api/tags/execute-technical-cleanup", 
            json={"dry_run": not execute_changes}
        )
        if response.status_code == 200:
            result2 = response.json()
            results.append(("technical_cleanup", result2))
            print(f"   ✅ Technical cleanup: {result2.get('technical_removals', 0)} removed, {result2.get('format_consolidations', 0)} standardized")
        else:
            print(f"   ❌ Technical cleanup failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Step 3: Try the working consolidate endpoint (it has hardcoded mappings)
    print("\n🎯 STEP 3: Running hardcoded Tesseract consolidation...")
    try:
        response = requests.post(
            f"{API_BASE}/api/tags/consolidate",
            json={"dry_run": not execute_changes}
        )
        if response.status_code == 200:
            result3 = response.json()
            results.append(("tesseract_consolidate", result3))
            print(f"   ✅ Tesseract consolidation: {result3.get('total_changes', 0)} changes")
        else:
            print(f"   ❌ Tesseract consolidation failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Summary
    total_changes = sum(
        result.get('placeholder_tags_removed', 0) + 
        result.get('technical_removals', 0) + 
        result.get('format_consolidations', 0) +
        result.get('total_changes', 0)
        for _, result in results
    )
    
    print(f"\n📊 CONSOLIDATION SUMMARY:")
    print(f"   Total cleanup operations: {len(results)}")
    print(f"   Total changes made: {total_changes}")
    print(f"   Mode: {'EXECUTED' if execute_changes else 'DRY RUN'}")
    
    # Save results
    with open("working_consolidation_results.json", "w") as f:
        json.dump({
            "timestamp": "2025-09-16",
            "mode": "execute" if execute_changes else "dry_run",
            "operations": results,
            "total_changes": total_changes
        }, f, indent=2)
    
    print(f"   📄 Results saved: working_consolidation_results.json")
    
    if total_changes > 0:
        print(f"\n🎯 VERIFY RESULTS:")
        print(f"   curl http://localhost:5050/api/tags/audit")
        print(f"   Should show reduced tag count and cleaner structure")

if __name__ == "__main__":
    main()