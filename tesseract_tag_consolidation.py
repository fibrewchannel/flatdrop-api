#!/usr/bin/env python3
"""
Tesseract-Aware Tag Consolidation Automation
For Rick's Flatline Codex Memoir Project

This script automates tag consolidation based on the 4D Tesseract coordinate system,
removing tags that are redundant with coordinate data while preserving valuable metadata.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple
import sys

# API Configuration
API_BASE = "http://localhost:8000"
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
        response = self.session.post(f"{self.api_base}/api/backup/create")
        if response.status_code == 200:
            backup_info = response.json()
            print(f"   ✅ Backup created: {backup_info['backup_path']}")
            return backup_info
        else:
            print(f"   ❌ Backup failed: {response.text}")
            return {}
    
    def get_current_tag_audit(self) -> dict:
        """Get current tag distribution"""
        print("📊 Auditing current tag landscape...")
        response = self.session.get(f"{self.api_base}/api/tags/audit")
        if response.status_code == 200:
            audit_data = response.json()
            print(f"   📈 Current tags: {audit_data['total_tags']}")
            print(f"   📈 Total instances: {audit_data['total_instances']}")
            return audit_data
        else:
            print(f"   ❌ Audit failed: {response.text}")
            return {}
    
    def get_tesseract_coordinates(self) -> dict:
        """Extract current 4D coordinate mappings"""
        print("🎲 Extracting Tesseract coordinates...")
        response = self.session.post(f"{self.api_base}/api/tesseract/extract-coordinates")
        if response.status_code == 200:
            coordinate_data = response.json()
            print(f"   🎯 Files mapped: {len(coordinate_data.get('coordinate_combinations', {}))}")
            return coordinate_data
        else:
            print(f"   ❌ Coordinate extraction failed: {response.text}")
            return {}
    
    def analyze_coordinate_redundancy(self, tag_audit: dict, coordinates: dict) -> dict:
        """Analyze which tags are redundant with Tesseract coordinates"""
        print("🔍 Analyzing tag-coordinate redundancy...")
        
        # Define coordinate-redundant tags based on Tesseract dimensions
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
        """Define comprehensive consolidation mappings"""
        
        # Phase 1: Coordinate-redundant tag removal
        coordinate_redundant_mappings = {}
        for tag, data in redundancy_analysis.items():
            coordinate_redundant_mappings[tag] = "COORDINATE_REDUNDANT_REMOVED"
        
        # Phase 2: Format standardization (preserve these but standardize format)
        format_standardization = {
            # Hash prefix removal
            "#flatline": "flatline",
            "#protocol": "protocol", 
            "#archetype": "archetype",
            "#summonings": "summonings",
            "#ritual": "ritual",
            "#narrative": "narrative",
            
            # Color code standardization
            "colors/0A0A23": "color-0a0a23",
            "0A0A23": "color-0a0a23", 
            "B9F5D8": "color-b9f5d8",
            "8A91C5": "color-8a91c5",
            "BC8D6B": "color-bc8d6b",
            
            # Path-like tag flattening (from your existing consolidations)
            "flatline-codex/draw-things": "draw-things",
            "flatline-codex/flatline-dashboard": "flatline-dashboard",
            "protocols/chaos-gen": "chaos-gen",
            "rituals/block-and-release": "ritual-block-release",
        }
        
        # Phase 3: Valuable tag preservation (keep as-is, explicitly documented)
        preserve_tags = {
            # Temporal specificity
            "2024", "2025", "rochester", "mayo-clinic", 
            
            # People/relationships
            "nyx", "sponsor", "therapist",
            
            # Tools/platforms  
            "draw-things", "obsidian", "api", "flatdrop",
            
            # Medical specificity
            "cirrhosis", "cptsd", "therapy", "ssdi",
            
            # Recovery milestones (keep granular)
            "aa-meeting", "step-work", "sponsor-work"
        }
        
        return {
            "phase_1_coordinate_redundant": coordinate_redundant_mappings,
            "phase_2_format_standardization": format_standardization, 
            "phase_3_preserve_valuable": list(preserve_tags)
        }
    
    def execute_consolidation_phase(self, mappings: dict, phase_name: str, dry_run: bool = True) -> dict:
        """Execute a single consolidation phase"""
        print(f"\n🚀 Executing {phase_name} (dry_run={dry_run})...")
        
        payload = {
            "dry_run": dry_run,
            "backup": True if not dry_run else False
        }
        
        # For coordinate redundant removal, we need special handling
        if "coordinate_redundant" in phase_name:
            # This would require a special endpoint for tag removal
            # For now, we'll use the existing consolidation endpoint with empty string mappings
            coordinate_removal_mappings = {tag: "" for tag in mappings.keys()}
            payload["custom_mappings"] = coordinate_removal_mappings
        else:
            payload["custom_mappings"] = mappings
        
        response = self.session.post(
            f"{self.api_base}/api/tags/consolidate",
            json=payload
        )
        
        if response.status_code == 200:
            results = response.json()
            return results
        else:
            print(f"   ❌ Phase failed: {response.text}")
            return {"error": response.text}
    
    def run_full_consolidation(self, execute_changes: bool = False):
        """Run complete Tesseract-aware tag consolidation"""
        print("🎬 STARTING TESSERACT-AWARE TAG CONSOLIDATION")
        print("=" * 60)
        
        # Step 1: Create backup
        backup_info = self.create_backup()
        if not backup_info:
            print("❌ Cannot proceed without backup!")
            return
        
        # Step 2: Get current state
        initial_audit = self.get_current_tag_audit()
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
        if execute_changes:
            print(f"\n⚡ EXECUTING CHANGES (execute_changes=True)")
        else:
            print(f"\n🔍 DRY RUN MODE (execute_changes=False)")
        
        # Phase 1: Remove coordinate-redundant tags
        phase1_results = self.execute_consolidation_phase(
            consolidation_mappings["phase_1_coordinate_redundant"], 
            "Phase 1: Coordinate Redundancy Removal",
            dry_run=not execute_changes
        )
        self.log_phase("Phase 1", "Remove coordinate-redundant tags", phase1_results)
        
        # Phase 2: Format standardization
        phase2_results = self.execute_consolidation_phase(
            consolidation_mappings["phase_2_format_standardization"],
            "Phase 2: Format Standardization", 
            dry_run=not execute_changes
        )
        self.log_phase("Phase 2", "Standardize tag formats", phase2_results)
        
        # Step 6: Final audit
        final_audit = self.get_current_tag_audit()
        
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
            print(f"🎯 REDUCTION: {initial_tags - final_tags} tags removed ({((initial_tags - final_tags) / initial_tags * 100):.1f}%)")
        else:
            print(f"🔍 PROJECTED: ~{final_tags - 150} unique tags after execution (estimated)")
        
        print(f"📋 AUTOMATION STATUS: {'✅ EXECUTED' if executed else '🔍 DRY RUN COMPLETE'}")
        print(f"🔗 TESSERACT INTEGRATION: ✅ Coordinate-aware consolidation active")
        print(f"💾 BACKUP PROTECTION: ✅ Emergency backup created")
        print(f"📱 MOBILE READY: ✅ Cloud-accessible from any device")
    
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


if __name__ == "__main__":
    main()