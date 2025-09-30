#!/usr/bin/env python3
"""
Quick Fix: Minimal Tesseract Tag Consolidation
For Rick's current 742-tag vault state

Targets only the remaining coordinate-redundant tags without requiring backup endpoint.
"""

import requests
import json
import sys

API_BASE = "http://localhost:5050"

def main():
    print("🎯 Quick Tesseract Tag Consolidation")
    print("Targeting remaining coordinate-redundant tags")
    print("=" * 50)
    
    # Define the remaining coordinate-redundant mappings
    consolidation_mappings = {
        # Coordinate-redundant (remove by setting to empty string)
        "ritual": "",  # 13 instances - X-axis structure
        "chaos": "",   # 8 instances - W-axis terrain  
        "tarot": "",   # 7 instances - Y-axis transmission
        
        # Format standardization
        "ritual/ritual-nourishment": "ritual-nourishment",  # 10 instances
        "thread-dump": "threaddump",  # 15 instances
        "_import": "import",  # 14 instances
        
        # Clean up automation residue
        "REMOVE_SYSTEM_REDUNDANT": "",
        "REMOVE_X_AXIS_REDUNDANT": "",
        "REMOVE_Z_AXIS_REDUNDANT": ""
    }
    
    # Check if we should execute or just dry run
    execute_changes = "--execute" in sys.argv
    
    if not execute_changes:
        print("🔍 DRY RUN MODE - No files will be changed")
        print("Use --execute to apply changes")
    else:
        confirm = input("⚡ EXECUTE MODE: Type 'YES' to apply changes: ")
        if confirm != "YES":
            print("Cancelled.")
            return
    
    print(f"\n🎯 Targeting {len(consolidation_mappings)} tag consolidations...")
    
    # Make the API call
    try:
        payload = {
            "dry_run": not execute_changes,
            "backup": False,  # Skip backup for this quick fix
            "custom_mappings": consolidation_mappings
        }
        
        response = requests.post(
            f"{API_BASE}/api/tags/consolidate",
            json=payload
        )
        
        if response.status_code == 200:
            results = response.json()
            
            print(f"\n📊 CONSOLIDATION RESULTS:")
            print(f"   Files affected: {results.get('files_affected', 0)}")
            print(f"   Total changes: {results.get('total_changes', 0)}")
            
            if not execute_changes:
                print(f"   🔍 This was a DRY RUN - no files were modified")
            else:
                print(f"   ✅ Changes applied successfully!")
            
            # Save results log
            with open("consolidation_results.json", "w") as f:
                json.dump(results, f, indent=2)
            print(f"   📄 Results saved to consolidation_results.json")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to API at {API_BASE}")
        print("💡 Make sure your API server is running:")
        print("   cd code && python -m uvicorn main:app --host 0.0.0.0 --port 5050")

if __name__ == "__main__":
    main()