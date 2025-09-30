#!/usr/bin/env python3
"""
Final Tag Consolidation Script (Complete)
Addresses remaining coordinate-redundant tags: ritual, chaos, tarot
Uses URL parameters (discovered working approach)
"""

import requests
import json
import sys

API_BASE = "http://localhost:5050"

def main():
    print("🎯 FINAL TAG CONSOLIDATION CLEANUP")
    print("Targeting remaining coordinate-redundant tags")
    print("=" * 50)
    
    execute_changes = "--execute" in sys.argv
    
    if not execute_changes:
        print("🔍 DRY RUN MODE - No files will be changed")
        print("Use --execute to apply changes")
    else:
        confirm = input("⚡ EXECUTE MODE: Type 'YES' to apply final cleanup: ")
        if confirm != "YES":
            print("Cancelled.")
            return
    
    results = []
    
    # Step 1: Check consolidation status
    print("\n📊 STEP 1: Checking consolidation status...")
    try:
        response = requests.get(f"{API_BASE}/api/tags/consolidation-status")
        if response.status_code == 200:
            status = response.json()
            print(f"   📈 Current tags: {status['current_tag_count']}")
            print(f"   📊 Completeness: {status['consolidation_completeness_percent']}%")
            print(f"   🎯 Remaining issues: {status['total_remaining_issues']}")
            
            if status['total_remaining_issues'] == 0:
                print("   ✅ Consolidation appears complete!")
                return
                
        else:
            print(f"   ⚠️ Status check failed, proceeding anyway...")
    except Exception as e:
        print(f"   ⚠️ Status check error: {e}")
    
    # Step 2: Run final consolidation cleanup
    print(f"\n🎯 STEP 2: Running final consolidation cleanup...")
    try:
        # Use discovered URL parameter approach
        dry_run_param = "true" if not execute_changes else "false"
        response = requests.post(f"{API_BASE}/api/tags/final-consolidation-cleanup?dry_run={dry_run_param}")
        
        if response.status_code == 200:
            result = response.json()
            results.append(("final_cleanup", result))
            print(f"   ✅ Coordinate removals: {result.get('coordinate_removals', 0)}")
            print(f"   ✅ Format consolidations: {result.get('format_consolidations', 0)}")
            print(f"   ✅ Total changes: {result.get('total_changes', 0)}")
        else:
            print(f"   ❌ Final cleanup failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Step 3: Verify final state
    print(f"\n📊 STEP 3: Verifying final results...")
    try:
        response = requests.get(f"{API_BASE}/api/tags/audit")
        if response.status_code == 200:
            final_audit = response.json()
            print(f"   📈 Final tag count: {final_audit['total_tags']}")
            print(f"   📊 Final instances: {final_audit['total_instances']}")
            
            # Check if problematic tags are gone
            top_tags = dict(final_audit.get('top_50_tags', []))
            remaining_problems = []
            for problem_tag in ['ritual', 'chaos', 'tarot']:
                if problem_tag in top_tags:
                    remaining_problems.append(f"{problem_tag} ({top_tags[problem_tag]})")
            
            if remaining_problems:
                print(f"   ⚠️ Still present: {', '.join(remaining_problems)}")
            else:
                print(f"   ✅ Coordinate-redundant tags successfully removed!")
                
        else:
            print(f"   ❌ Final audit failed")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Summary
    total_changes = sum(
        result.get('coordinate_removals', 0) + result.get('format_consolidations', 0)
        for _, result in results
    )
    
    print(f"\n📊 FINAL CONSOLIDATION SUMMARY:")
    print(f"   Cleanup operations: {len(results)}")
    print(f"   Total changes: {total_changes}")
    print(f"   Mode: {'EXECUTED' if execute_changes else 'DRY RUN'}")
    
    # Save results
    with open("final_consolidation_results.json", "w") as f:
        json.dump({
            "timestamp": "2025-09-16",
            "phase": "final_cleanup",
            "mode": "execute" if execute_changes else "dry_run",
            "operations": results,
            "total_changes": total_changes
        }, f, indent=2)
    
    print(f"   📄 Results saved: final_consolidation_results.json")
    
    if execute_changes and total_changes > 0:
        print(f"\n🎊 TESSERACT TAG CONSOLIDATION COMPLETED!")
        print(f"   Your memoir system is now fully optimized for:")
        print(f"   📱 Mobile access during housing instability")
        print(f"   📚 Memoir production with 4D coordinate organization")
        print(f"   🔍 Precision search with meaningful tag metadata")
        print(f"   ☁️ Cloud deployment readiness")

if __name__ == "__main__":
    main()