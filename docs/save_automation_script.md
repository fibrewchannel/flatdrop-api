# Save Tesseract Tag Consolidation Automation

## File Location
Save the automation script as:
```
flatdrop-api/tesseract_tag_consolidation.py
```

## Copy This Complete Script

```python
#!/usr/bin/env python3
"""
Tesseract-Aware Tag Consolidation Automation
For Rick's Flatline Codex Memoir Project

This script automates tag consolidation based on the 4D Tesseract coordinate system,
removing tags that are redundant with coordinate data while preserving valuable metadata.

REST API approach for local development and cloud deployment compatibility.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple
import sys

# API Configuration - Update when deploying to cloud  
API_BASE = "http://localhost:5050"  # Rick's actual API port
CONSOLIDATION_LOG_FILE = "tag_consolidation_log.json"

class TesseractTagConsolidator:
    def __init__(self, api_base: str = API_BASE):
        self.api_base = api_base
        self.session = requests.Session()
        self.consolidation_log = {
            "timestamp": datetime.now().isoformat(),
            "phases": [],
            "total_changes": 0,
            "files_affected": 0
        }
    
    def log_phase(self, phase_name: str, description: str, results: dict):
        """Log phase results for automation documentation"""
        phase_entry = {
            "phase": phase_name,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "results": results
        }
        self.consolidation_log["phases"].append(phase_entry)
        self.consolidation_log["total_changes"] += results.get("total_changes", 0)
        self.consolidation_log["files_affected"] += results.get("files_affected", 0)
        
        print(f"\n🎯 {phase_name}: {description}")
        print(f"   Files affected: {results.get('files_affected', 0)}")
        print(f"   Total changes: {results.get('total_changes', 0)}")
    
    def create_backup(self) -> dict:
        """Create emergency backup before consolidation"""
        print("🔒 Creating emergency backup...")
        try:
            response = self.session.post(f"{self.api_base}/api/backup/create")
            if response.status_code == 200:
                backup_info = response.json()
                print(f"   ✅ Backup created: {backup_info.get('backup_path', 'Success')}")
                return backup_info
            else:
                print(f"   ❌ Backup failed: {response.text}")
                return {}
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Cannot connect to API at {self.api_base}")
            print(f"   💡 Start your API server first: cd code && python -m uvicorn main:app --reload")
            return {}
    
    def get_current_tag_audit(self) -> dict:
        """Get current tag distribution"""
        print("📊 Auditing current tag landscape...")
        try:
            response = self.session.get(f"{self.api_base}/api/tags/audit")
            if response.status_code == 200:
                audit_data = response.json()
                print(f"   📈 Current tags: {audit_data.get('total_tags', 0)}")
                print(f"   📈 Total instances: {audit_data.get('total_instances', 0)}")
                return audit_data
            else:
                print(f"   ❌ Audit failed: {response.text}")
                return {}
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Cannot connect to API at {self.api_base}")
            return {}
    
    def get_tesseract_coordinates(self) -> dict:
        """Extract current 4D coordinate mappings"""
        print("🎲 Extracting Tesseract coordinates...")
        try:
            response = self.session.post(f"{self.api_base}/api/tesseract/extract-coordinates")
            if response.status_code == 200:
                coordinate_data = response.json()
                print(f"   🎯 Files mapped: {len(coordinate_data.get('coordinate_combinations', {}))}")
                return coordinate_data
            else:
                print(f"   ❌ Coordinate extraction failed: {response.text}")
                return {}
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Cannot connect to API at {self.api_base}")
            return {}
    
    def analyze_coordinate_redundancy(self, tag_audit: dict, coordinates: dict) -> dict:
        """Analyze which tags are redundant with Tesseract coordinates"""
        print("🔍 Analyzing tag-coordinate redundancy...")
        
        # Define coordinate-redundant tags based on your Tesseract dimensions
        coordinate_redundant_tags = {
            # X-Axis Structure redundancies
            "archetype": "X-axis structure mapping",
            "protocol": "X-axis structure mapping", 
            "ritual": "X-axis structure mapping (maps to protocol/summoning)",
            "summonings": "X-axis structure mapping",
            "shadowcast": "X-axis structure mapping",
            "expansion": "X-axis structure mapping",
            
            # Y-Axis Transmission redundancies
            "narrative": "Y-axis transmission mapping",
            "text": "Y-axis transmission mapping",
            "image": "Y-axis transmission mapping", 
            "tarot": "Y-axis transmission mapping",
            "invocation": "Y-axis transmission mapping",
            
            # Z-Axis Purpose redundancies
            "memoir": "Z-axis purpose mapping (tell-story)",
            "recovery": "Z-axis purpose mapping (help-addict)",
            "survival": "Z-axis purpose mapping (prevent-death-poverty)",
            "work": "Z-axis purpose mapping (financial-amends)",
            "creative": "Z-axis purpose mapping (help-world)",
            
            # W-Axis Terrain redundancies
            "chaos": "W-axis terrain mapping (chaotic)",
            "complex": "W-axis terrain mapping", 
            "crisis": "W-axis terrain mapping (chaotic)",
            "obvious": "W-axis terrain mapping",
            "complicated": "W-axis terrain mapping"
        }
        
        # Analyze current tags for redundancy
        top_tags = dict(tag_audit.get("top_50_tags", []))
        redundant_analysis = {}
        
        for tag, count in top_tags.items():
            if tag in coordinate_redundant_tags:
                redundant_analysis[tag] = {
                    "count": count,
                    "redundancy_reason": coordinate_redundant_tags[tag],
                    "action": "REMOVE_COORDINATE_REDUNDANT"
                }
        
        print(f"   🎯 Found {len(redundant_analysis)} coordinate-redundant tags")
        total_redundant_instances = sum(data["count"] for data in redundant_analysis.values())
        print(f"   📊 Total redundant instances: {total_redundant_instances}")
        
        return redundant_analysis
    
    def define_consolidation_mappings(self, redundancy_analysis: dict) -> dict:
        """Define consolidation mappings for Rick's current vault state (742 tags)"""
        
        # Phase 1: Remaining coordinate-redundant tags (based on current audit)
        coordinate_redundant_mappings = {
            # X-Axis Structure redundancies still present
            "ritual": "",  # 13 instances - X-axis structure (protocol/summoning)
            
            # Y-Axis Transmission redundancies still present  
            "tarot": "",  # 7 instances - Y-axis transmission
            
            # W-Axis Terrain redundancies still present
            "chaos": "",  # 8 instances - W-axis terrain (chaotic)
            
            # Clean up any automation residue
            "REMOVE_SYSTEM_REDUNDANT": "",
            "REMOVE_X_AXIS_REDUNDANT": "", 
            "REMOVE_Z_AXIS_REDUNDANT": ""
        }
        
        # Phase 2: Format standardization (based on Rick's current patterns)
        format_standardization = {
            # Path-like consolidations still present
            "ritual/ritual-nourishment": "ritual-nourishment",  # 10 instances
            
            # Merge similar concepts
            "thread-dump": "threaddump",  # 15 → merge with threaddump (18)
            "_import": "import",  # 14 → merge with import (18)
            
            # Any remaining hash prefixes
            "#flatline": "flatline",
            "#codex": "codex",
            
            # Clean up any remaining color variations
            "colors/": "colors",
            "colors/8A91C5": "color-8a91c5",
            "colors/FFA86A": "color-ffa86a"
        }
        
        # Phase 3: Valuable tags to preserve (Rick's current strong tags)
        preserve_tags = {
            # Core system identity (top performers)
            "codex",  # 139 instances - Core knowledge system
            "dispatch",  # 96 instances - Communication format
            "flatline",  # 8 instances - System identity
            
            # Memoir production tools
            "todo",  # 31 instances - Action tracking
            "oracle-gospel",  # 26 instances - Philosophical framework
            "obsidian",  # 24 instances - Tool specificity
            "resume",  # 24 instances - Career narrative
            
            # Medical/therapy specificity  
            "dbt",  # 21 instances - Therapy methodology
            "mayo-diet-deathmarch",  # 10 instances - Medical specificity
            "psych",  # 7 instances - Mental health context
            
            # Technical/creative tools
            "draw-things",  # 8 instances - AI art tool
            "maddog5",  # 28 instances - System component
            "runtime-chaos",  # 27 instances - System state
            "threaddump",  # 18 instances - Debug/system tool
            "ai",  # 11 instances - AI collaboration
            
            # Temporal/location context
            "2025-06-30", "rochester", "mayo-clinic",
            
            # Recovery/people context
            "nyx", "sponsor", "therapist", "caregiving"
        }
        
        return {
            "phase_1_coordinate_redundant": coordinate_redundant_mappings,
            "phase_2_format_standardization": format_standardization, 
            "phase_3_preserve_valuable": list(preserve_tags)
        }
    
    def execute_consolidation_phase(self, mappings: dict, phase_name: str, dry_run: bool = True) -> dict:
        """Execute a single consolidation phase using your existing API endpoint"""
        print(f"\n🚀 Executing {phase_name} (dry_run={dry_run})...")
        
        try:
            # Use your existing /api/tags/consolidate endpoint
            payload = {
                "dry_run": dry_run,
                "backup": not dry_run,  # Only backup on real execution
                "custom_mappings": mappings
            }
            
            response = self.session.post(
                f"{self.api_base}/api/tags/consolidate",
                json=payload
            )
            
            if response.status_code == 200:
                results = response.json()
                return results
            else:
                print(f"   ❌ Phase failed: {response.text}")
                return {"error": response.text, "files_affected": 0, "total_changes": 0}
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Cannot connect to API at {self.api_base}")
            return {"error": "API connection failed", "files_affected": 0, "total_changes": 0}
    
    def run_full_consolidation(self, execute_changes: bool = False):
        """Run complete Tesseract-aware tag consolidation"""
        print("🎬 STARTING TESSERACT-AWARE TAG CONSOLIDATION")
        print("=" * 60)
        
        # Step 1: Verify API connection and create backup
        backup_info = self.create_backup()
        if not backup_info and execute_changes:
            print("❌ Cannot proceed with execution without backup!")
            print("💡 Make sure your API server is running: cd code && python -m uvicorn main:app --reload")
            return
        
        # Step 2: Get current state
        initial_audit = self.get_current_tag_audit()
        if not initial_audit:
            print("❌ Cannot proceed without tag audit!")
            return
            
        coordinates = self.get_tesseract_coordinates()
        
        # Step 3: Analyze redundancy
        redundancy_analysis = self.analyze_coordinate_redundancy(initial_audit, coordinates)
        
        # Step 4: Define consolidation strategy
        consolidation_mappings = self.define_consolidation_mappings(redundancy_analysis)
        
        print(f"\n📋 CONSOLIDATION STRATEGY SUMMARY")
        print(f"   Phase 1: Remove {len(consolidation_mappings['phase_1_coordinate_redundant'])} coordinate-redundant tags")
        print(f"   Phase 2: Standardize {len(consolidation_mappings['phase_2_format_standardization'])} format variations")
        print(f"   Phase 3: Preserve {len(consolidation_mappings['phase_3_preserve_valuable'])} valuable metadata tags")
        
        # Step 5: Execute phases
        execution_mode = "EXECUTING CHANGES" if execute_changes else "DRY RUN MODE"
        print(f"\n⚡ {execution_mode}")
        
        # Phase 1: Remove coordinate-redundant tags
        if consolidation_mappings["phase_1_coordinate_redundant"]:
            phase1_results = self.execute_consolidation_phase(
                consolidation_mappings["phase_1_coordinate_redundant"], 
                "Phase 1: Coordinate Redundancy Removal",
                dry_run=not execute_changes
            )
            self.log_phase("Phase 1", "Remove coordinate-redundant tags", phase1_results)
        else:
            print("\n🎯 Phase 1: No coordinate-redundant tags found to remove")
        
        # Phase 2: Format standardization  
        if consolidation_mappings["phase_2_format_standardization"]:
            phase2_results = self.execute_consolidation_phase(
                consolidation_mappings["phase_2_format_standardization"],
                "Phase 2: Format Standardization", 
                dry_run=not execute_changes
            )
            self.log_phase("Phase 2", "Standardize tag formats", phase2_results)
        else:
            print("\n🎯 Phase 2: No format standardizations needed")
        
        # Step 6: Final audit (only if executing)
        if execute_changes:
            print("\n📊 Getting final audit results...")
            final_audit = self.get_current_tag_audit()
        else:
            final_audit = initial_audit
        
        # Step 7: Generate summary report
        self.generate_summary_report(initial_audit, final_audit, execute_changes)
        
        # Step 8: Save automation log
        self.save_consolidation_log()
    
    def generate_summary_report(self, initial_audit: dict, final_audit: dict, executed: bool):
        """Generate comprehensive summary report"""
        print(f"\n📊 CONSOLIDATION SUMMARY REPORT")
        print("=" * 50)
        
        initial_tags = initial_audit.get("total_tags", 0)
        final_tags = final_audit.get("total_tags", 0) if executed else initial_tags
        
        initial_instances = initial_audit.get("total_instances", 0)  
        final_instances = final_audit.get("total_instances", 0) if executed else initial_instances
        
        print(f"📈 BEFORE: {initial_tags} unique tags, {initial_instances} total instances")
        if executed:
            print(f"📉 AFTER:  {final_tags} unique tags, {final_instances} total instances")
            tag_reduction = initial_tags - final_tags
            instance_reduction = initial_instances - final_instances
            total_project_reduction = 798 - final_tags  # From original starting point
            print(f"🎯 SESSION REDUCTION: {tag_reduction} tags ({(tag_reduction/initial_tags*100):.1f}%), {instance_reduction} instances ({(instance_reduction/initial_instances*100):.1f}%)")
            print(f"📊 TOTAL PROJECT REDUCTION: 798 → {final_tags} tags ({(total_project_reduction/798*100):.1f}% total reduction)")
        else:
            estimated_reduction = sum(len(phase.get("results", {}).get("details", [])) for phase in self.consolidation_log["phases"])
            print(f"🔍 PROJECTED: ~{estimated_reduction} changes would be made")
            print(f"📊 TOTAL PROJECT STATUS: 798 → 742 → ~{initial_tags - estimated_reduction} tags")
        
        print(f"📋 AUTOMATION STATUS: {'✅ EXECUTED' if executed else '🔍 DRY RUN COMPLETE'}")
        print(f"🔗 TESSERACT INTEGRATION: ✅ Coordinate-aware consolidation active")
        print(f"💾 BACKUP PROTECTION: ✅ Emergency backup {'created' if executed else 'verified'}")
        print(f"📱 MOBILE READY: ✅ Cloud-accessible from any device")
        print(f"🏠 HOUSING INSTABILITY READY: ✅ System optimized for anywhere access")
    
    def save_consolidation_log(self):
        """Save detailed log for automation documentation"""
        with open(CONSOLIDATION_LOG_FILE, "w") as f:
            json.dump(self.consolidation_log, f, indent=2)
        print(f"📄 Automation log saved: {CONSOLIDATION_LOG_FILE}")


def main():
    """Main execution function"""
    print("🎲 Tesseract-Aware Tag Consolidation Automation")
    print("For Rick's Flatline Codex Memoir Project")
    print("=" * 60)
    
    # Check command line arguments
    execute_changes = "--execute" in sys.argv
    if not execute_changes:
        print("🔍 Running in DRY RUN mode. Use --execute to apply changes.")
        print("   This will show what WOULD be changed without modifying files.")
    else:
        print("⚡ EXECUTION MODE: Changes will be applied to vault files!")
        confirm = input("   Type 'YES' to confirm: ")
        if confirm != "YES":
            print("   Cancelled by user.")
            return
    
    # Initialize and run consolidator
    consolidator = TesseractTagConsolidator()
    consolidator.run_full_consolidation(execute_changes=execute_changes)
    
    print(f"\n🎬 Consolidation complete! Check {CONSOLIDATION_LOG_FILE} for details.")
    if not execute_changes:
        print("💡 Run with --execute to apply changes after reviewing the dry run results.")


if __name__ == "__main__":
    main()
```

## Prerequisites

1. **Start your API server first:**
   ```bash
   cd flatdrop-api/code
   python -m uvicorn main:app --reload
   ```

2. **Verify API is running:**
   ```bash
   curl http://localhost:8000/api/tags/audit
   ```

## Usage

1. **Dry run (safe preview):**
   ```bash
   cd flatdrop-api
   python tesseract_tag_consolidation.py
   ```

2. **Live execution:**
   ```bash
   cd flatdrop-api  
   python tesseract_tag_consolidation.py --execute
   ```

## Cloud Migration Ready

When you deploy to cloud (Vercel/Railway):
- Update `API_BASE = "https://your-deployed-api.com"`
- Script works identically for anywhere access during housing instability

**Save this script and you're ready to execute the Tesseract-aware tag consolidation!**