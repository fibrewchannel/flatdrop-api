#!/usr/bin/env python3
"""
Incremental Processing System
Only processes new/unprocessed files from _inload (.md, .txt, .rtf), archives processed sources
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Set, Dict, Any
import shutil

# Import the existing production nibbler
from production_relocation_nibbler import ProductionRelocationNibbler, RTF_AVAILABLE

# CONFIGURATION
SOURCE_DIR = "/Users/rickshangle/Vaults/flatline-codex/_inload"
OUTPUT_BASE = "/Users/rickshangle/Vaults/flatline-codex"
BACKUP_DIR = "/Users/rickshangle/Vaults/flatline-codex/_backups"
PROCESSED_LOG = "/Users/rickshangle/Vaults/flatline-codex/_relocation_logs/processed_sources.json"

class IncrementalProcessor:
    """Processes only new files from _inload, tracks what's been processed"""
    
    def __init__(self, source_dir: str, output_base: str, backup_dir: str, log_file: str):
        self.source_dir = Path(source_dir)
        self.output_base = Path(output_base)
        self.backup_dir = Path(backup_dir)
        self.log_file = Path(log_file)
        self.archive_dir = self.output_base / "_archive" / "processed-sources"
        
        # Initialize the nibbler
        self.nibbler = ProductionRelocationNibbler(source_dir, output_base, backup_dir)
        
        # Load processed files log
        self.processed_files = self.load_processed_log()
        
        # Setup archive directory
        self.archive_dir.mkdir(parents=True, exist_ok=True)
    
    def load_processed_log(self) -> Dict[str, Dict[str, Any]]:
        """Load log of previously processed files"""
        if not self.log_file.exists():
            return {}
        
        try:
            with open(self.log_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load processed log: {e}")
            return {}
    
    def save_processed_log(self):
        """Save updated processed files log"""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_file, 'w') as f:
            json.dump(self.processed_files, f, indent=2)
    
    def get_file_fingerprint(self, file_path: Path) -> str:
        """Generate fingerprint for file to detect changes"""
        stat = file_path.stat()
        return f"{file_path.name}_{stat.st_size}_{stat.st_mtime}"
    
    def is_processed(self, file_path: Path) -> bool:
        """Check if file has been processed before"""
        file_key = str(file_path.relative_to(self.source_dir.parent))
        
        if file_key not in self.processed_files:
            return False
        
        # Check if file was modified since processing
        current_fingerprint = self.get_file_fingerprint(file_path)
        stored_fingerprint = self.processed_files[file_key].get("fingerprint")
        
        return current_fingerprint == stored_fingerprint
    
    def mark_as_processed(self, file_path: Path, processing_info: Dict[str, Any]):
        """Mark file as processed in log"""
        file_key = str(file_path.relative_to(self.source_dir.parent))
        
        self.processed_files[file_key] = {
            "fingerprint": self.get_file_fingerprint(file_path),
            "processed_date": datetime.now().isoformat(),
            "chunks_extracted": processing_info.get("chunks_extracted", 0),
            "disposition_summary": processing_info.get("disposition_summary", {})
        }
    
    def archive_source_file(self, file_path: Path):
        """Move processed source file to archive"""
        # Preserve directory structure in archive
        relative_path = file_path.relative_to(self.source_dir)
        archive_path = self.archive_dir / relative_path
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Move file to archive
        shutil.move(str(file_path), str(archive_path))
        print(f"  Archived: {file_path.name} -> {archive_path.relative_to(self.output_base)}")
    
    def scan_for_new_files(self) -> tuple:
        """Find files in _inload that haven't been processed"""
        # Get all processable files
        md_files = list(self.source_dir.rglob("*.md"))
        txt_files = list(self.source_dir.rglob("*.txt"))
        rtf_files = list(self.source_dir.rglob("*.rtf")) if RTF_AVAILABLE else []
        
        all_files = md_files + txt_files + rtf_files
        new_files = []
        already_processed = []
        
        for file_path in all_files:
            if self.is_processed(file_path):
                already_processed.append(file_path)
            else:
                new_files.append(file_path)
        
        return new_files, already_processed
    
    def process_new_files(self, dry_run: bool = False) -> Dict[str, Any]:
        """Process only new/unprocessed files from _inload"""
        
        print("\n🔍 Scanning _inload for new files...")
        new_files, already_processed = self.scan_for_new_files()
        
        # Count by type
        new_by_type = {
            '.md': len([f for f in new_files if f.suffix == '.md']),
            '.txt': len([f for f in new_files if f.suffix == '.txt']),
            '.rtf': len([f for f in new_files if f.suffix == '.rtf'])
        }
        
        if already_processed:
            print(f"\n✓ Found {len(already_processed)} already-processed files")
            if dry_run:
                print("  (These would be archived in real run)")
        
        if not new_files:
            print("\n✅ No new files to process!")
            return {
                "new_files": 0,
                "already_processed": len(already_processed),
                "message": "Nothing to do"
            }
        
        print(f"\n📂 Found {len(new_files)} new files to process")
        print(f"   - .md: {new_by_type['.md']}")
        print(f"   - .txt: {new_by_type['.txt']}")
        print(f"   - .rtf: {new_by_type['.rtf']}")
        
        if dry_run:
            print("\n🔍 DRY RUN - Showing what would be processed:")
            for i, file_path in enumerate(new_files[:10], 1):
                print(f"  {i}. {file_path.name} ({file_path.suffix})")
            if len(new_files) > 10:
                print(f"  ... and {len(new_files) - 10} more")
            
            return {
                "dry_run": True,
                "new_files": len(new_files),
                "new_by_type": new_by_type,
                "already_processed": len(already_processed)
            }
        
        # Create backup before processing
        print("\n💾 Creating backup...")
        backup_path = self.nibbler.create_backup()
        
        # Process new files in batches
        print(f"\n⚙️ Processing {len(new_files)} new files...")
        batch_size = 10
        batch_id = 1
        all_results = []
        
        for i in range(0, len(new_files), batch_size):
            batch_files = new_files[i:i + batch_size]
            print(f"\nProcessing Batch {batch_id}: {len(batch_files)} files")
            
            batch_results = []
            for file_path in batch_files:
                # Process the file
                result = self.nibbler.process_single_file(file_path, dry_run=False)
                batch_results.append(result)
                
                # Calculate disposition summary
                disposition_summary = {}
                for chunk in result.get("chunks", []):
                    dispo = chunk["disposition"]
                    disposition_summary[dispo] = disposition_summary.get(dispo, 0) + 1
                
                # Mark as processed
                processing_info = {
                    "chunks_extracted": result["chunks_extracted"],
                    "disposition_summary": disposition_summary
                }
                self.mark_as_processed(file_path, processing_info)
                
                # Archive the source file
                self.archive_source_file(file_path)
            
            all_results.extend(batch_results)
            batch_id += 1
        
        # Archive already-processed files (if they weren't already moved)
        if already_processed:
            print(f"\n📦 Archiving {len(already_processed)} already-processed files...")
            for file_path in already_processed:
                if file_path.exists():  # Check it hasn't been moved already
                    self.archive_source_file(file_path)
        
        # Save updated log
        self.save_processed_log()
        
        # Calculate final statistics
        total_chunks = sum(r["chunks_extracted"] for r in all_results)
        total_dispositions = {
            "memoir-grade": 0,
            "promising": 0,
            "borderline": 0,
            "trash": 0
        }
        
        for result in all_results:
            for chunk in result.get("chunks", []):
                dispo = chunk["disposition"]
                total_dispositions[dispo] += 1
        
        summary = {
            "new_files_processed": len(new_files),
            "new_files_by_type": new_by_type,
            "already_processed_archived": len(already_processed),
            "total_chunks_extracted": total_chunks,
            "disposition_breakdown": total_dispositions,
            "backup_location": str(backup_path),
            "processing_date": datetime.now().isoformat()
        }
        
        # Save processing summary
        summary_file = self.output_base / "_relocation_logs" / f"incremental_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print("\n" + "=" * 60)
        print("✅ INCREMENTAL PROCESSING COMPLETE")
        print("=" * 60)
        print(f"New files processed: {len(new_files)}")
        print(f"  - .md: {new_by_type['.md']}")
        print(f"  - .txt: {new_by_type['.txt']}")
        print(f"  - .rtf: {new_by_type['.rtf']}")
        print(f"Already-processed archived: {len(already_processed)}")
        print(f"Total chunks extracted: {total_chunks}")
        print(f"\nDisposition breakdown:")
        print(f"  Memoir-grade: {total_dispositions['memoir-grade']}")
        print(f"  Promising: {total_dispositions['promising']}")
        print(f"  Borderline: {total_dispositions['borderline']}")
        print(f"  Trash: {total_dispositions['trash']}")
        print(f"\n📁 _inload/ is now empty (all sources archived)")
        print(f"💾 Backup: {backup_path}")
        
        return summary

def main():
    """Run incremental processor"""
    
    processor = IncrementalProcessor(SOURCE_DIR, OUTPUT_BASE, BACKUP_DIR, PROCESSED_LOG)
    
    print("=" * 60)
    print("INCREMENTAL PROCESSING SYSTEM")
    print("=" * 60)
    print("\nSupports: .md, .txt, .rtf files")
    print("\nThis will:")
    print("  1. Check which files in _inload/ are new/modified")
    print("  2. Process only those files")
    print("  3. Archive ALL source files from _inload/")
    print("  4. Leave _inload/ empty for new content")
    
    mode = input("\nChoose mode:\n  1. Dry run (show what would happen)\n  2. PROCESS new files\nChoice: ")
    
    if mode == "1":
        processor.process_new_files(dry_run=True)
    elif mode == "2":
        confirm = input("\nThis will process new files and archive sources. Continue? (yes/no): ")
        if confirm.lower() == "yes":
            processor.process_new_files(dry_run=False)
        else:
            print("Cancelled")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
