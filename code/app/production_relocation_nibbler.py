#!/usr/bin/env python3
"""
Production Relocation Nibbler
Processes _inload files, extracts chunks, assigns dispositions, relocates to appropriate folders
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import shutil

# Import existing systems
from tesseract_config import get_analyzer, get_config

# CONFIGURATION
SOURCE_DIR = "/Users/rickshangle/Vaults/flatline-codex/_inload"
OUTPUT_BASE = "/Users/rickshangle/Vaults/flatline-codex"
BACKUP_DIR = "/Users/rickshangle/Vaults/flatline-codex/_backups"

@dataclass
class ChunkMetadata:
    """Complete metadata for an extracted chunk"""
    chunk_id: str
    extraction_date: str
    chunk_source: str
    source_chunk_sequence: int
    
    content_date: Optional[str]
    content_date_type: Optional[str]
    content_date_status: str
    
    quality_score: float
    quality_history: List[Dict[str, Any]]
    
    disposition: str
    status: str
    priority: int
    
    tesseract_coordinates: Dict[str, str]
    modality: List[str]
    
    parent_piece: Optional[str]
    parent_piece_status: str
    
    next_action: Optional[str]
    annotations: Optional[str]

class ProductionRelocationNibbler:
    """Production system for extracting chunks and relocating to organized structure"""
    
    def __init__(self, source_dir: str, output_base: str, backup_dir: str):
        self.source_dir = Path(source_dir)
        self.output_base = Path(output_base)
        self.backup_dir = Path(backup_dir)
        self.config = get_config()
        self.analyzer = get_analyzer()
        
        # Quality thresholds - recalibrated from actual score distribution
        # Based on analysis of 50 files: 90th percentile = 80, 80th = 51, 65th = 34, median = 28
        self.MEMOIR_GRADE_THRESHOLD = 51.0   # 80th percentile - high quality worth refining
        self.PROMISING_THRESHOLD = 34.0      # 65th percentile - worth human review
        self.BORDERLINE_THRESHOLD = 20.0     # ~50th percentile - maybe salvageable
        
        # Chunk counter for unique IDs
        self.chunk_counter = 0
        
        self.setup_output_directories()
    
    def setup_output_directories(self):
        """Create production folder structure"""
        folders = [
            "memoir",
            "recovery",
            "creative",
            "survival",
            "work-amends",
            "_review/promising",
            "_review/borderline",
            "_review/uncategorized",
            "_archive/processed-trash",
            "_archive/processed-sources",
            "_relocation_logs"
        ]
        
        for folder in folders:
            (self.output_base / folder).mkdir(parents=True, exist_ok=True)
    
    def create_backup(self) -> Path:
        """Create timestamped backup before processing"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"pre_relocation_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Copy _inload directory
        inload_backup = backup_path / "_inload"
        shutil.copytree(self.source_dir, inload_backup)
        
        print(f"Backup created: {backup_path}")
        return backup_path
    
    def generate_chunk_id(self) -> str:
        """Generate unique chunk ID with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        self.chunk_counter += 1
        return f"{timestamp}-chunk-{self.chunk_counter:03d}"
    
    def determine_disposition(self, quality_score: float) -> Dict[str, Any]:
        """Map quality score to disposition and destination"""
        if quality_score >= self.MEMOIR_GRADE_THRESHOLD:
            return {
                "disposition": "memoir-grade",
                "status": "ready-for-refinement",
                "priority": 1,
                "needs_purpose_routing": True
            }
        elif quality_score >= self.PROMISING_THRESHOLD:
            return {
                "disposition": "promising",
                "status": "needs-human-decision",
                "priority": 2,
                "destination": "_review/promising"
            }
        elif quality_score >= self.BORDERLINE_THRESHOLD:
            return {
                "disposition": "borderline",
                "status": "needs-human-decision",
                "priority": 3,
                "destination": "_review/borderline"
            }
        else:
            return {
                "disposition": "trash",
                "status": "archived",
                "priority": 4,
                "destination": "_archive/processed-trash"
            }
    
    def get_destination_from_purpose(self, z_purpose: str) -> str:
        """Map z_purpose to folder for memoir-grade chunks"""
        purpose_folders = {
            "tell-story": "memoir",
            "help-addict": "recovery",
            "prevent-death": "survival",
            "financial-amends": "work-amends",
            "help-world": "creative"
        }
        return purpose_folders.get(z_purpose, "memoir")
    
    def extract_content_date(self, content: str) -> Dict[str, Optional[str]]:
        """Attempt to extract temporal markers from content"""
        # Look for explicit dates
        date_patterns = [
            r'\b(19|20)\d{2}-\d{2}-\d{2}\b',  # YYYY-MM-DD
            r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+(19|20)\d{2}\b',  # Month DD, YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return {
                    "content_date": match.group(0),
                    "content_date_type": "approximate",
                    "content_date_status": "machine-extracted"
                }
        
        # No date found
        return {
            "content_date": None,
            "content_date_type": None,
            "content_date_status": "needs-human-input"
        }
    
    def detect_modality(self, content: str) -> List[str]:
        """Detect media types present in content"""
        modalities = ["text"]  # Always has text
        
        if re.search(r'!\[\[.*?\.(jpg|jpeg|png|gif|webp)', content, re.IGNORECASE):
            modalities.append("image")
        if re.search(r'!\[\[.*?\.(mp4|mov|avi|webm)', content, re.IGNORECASE):
            modalities.append("video")
        if re.search(r'!\[\[.*?\.(mp3|wav|m4a|ogg)', content, re.IGNORECASE):
            modalities.append("audio")
        if re.search(r'https?://', content):
            modalities.append("weblink")
        
        return modalities
    
    def extract_chunks_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract one or more chunks from source file"""
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        
        # Pre-clean content
        content = self.pre_clean_content(content)
        word_count = len(content.split())
        
        # Analyze content
        patterns = self.analyzer.extract_content_patterns(content)
        quality_score = self.analyzer.calculate_quality_score(content, patterns, word_count)
        coordinates = self.analyzer.suggest_tesseract_coordinates(patterns, content)
        theme = self.analyzer.identify_dominant_theme(patterns)
        
        # Determine if we should split into multiple chunks
        if word_count > 1000 and self.should_split_content(content, patterns):
            # Split into multiple chunks
            return self.split_into_chunks(content, file_path, patterns)
        else:
            # Single chunk
            return [{
                "content": content,
                "source_file": str(file_path.relative_to(self.source_dir.parent)),
                "sequence": 1,
                "total_chunks": 1,
                "quality_score": quality_score,
                "coordinates": coordinates,
                "theme": theme,
                "word_count": word_count
            }]
    
    def should_split_content(self, content: str, patterns: Dict) -> bool:
        """Determine if content should be split into multiple chunks"""
        # Split if multiple distinct topics detected
        topic_markers = [
            r'\b(AA|recovery|sobriety)\b',
            r'\b(Mayo|clinic|medical)\b',
            r'\b(memoir|story|childhood)\b',
            r'\b(housing|homeless|shelter)\b',
            r'\b(work|job|employment)\b'
        ]
        
        topic_hits = sum(1 for marker in topic_markers if re.search(marker, content, re.IGNORECASE))
        return topic_hits >= 3
    
    def split_into_chunks(self, content: str, file_path: Path, patterns: Dict) -> List[Dict[str, Any]]:
        """Split content into multiple logical chunks"""
        # Split on paragraph breaks
        sections = re.split(r'\n\s*\n', content)
        chunks = []
        chunk_seq = 1
        
        for section in sections:
            section = section.strip()
            if len(section.split()) < 20:  # Skip tiny fragments
                continue
            
            # Analyze this chunk
            section_patterns = self.analyzer.extract_content_patterns(section)
            section_quality = self.analyzer.calculate_quality_score(
                section, section_patterns, len(section.split())
            )
            section_coords = self.analyzer.suggest_tesseract_coordinates(section_patterns, section)
            section_theme = self.analyzer.identify_dominant_theme(section_patterns)
            
            chunks.append({
                "content": section,
                "source_file": str(file_path.relative_to(self.source_dir.parent)),
                "sequence": chunk_seq,
                "total_chunks": None,  # Will update after counting
                "quality_score": section_quality,
                "coordinates": section_coords,
                "theme": section_theme,
                "word_count": len(section.split())
            })
            chunk_seq += 1
        
        # Update total_chunks count
        for chunk in chunks:
            chunk["total_chunks"] = len(chunks)
        
        return chunks if chunks else [{
            "content": content,
            "source_file": str(file_path.relative_to(self.source_dir.parent)),
            "sequence": 1,
            "total_chunks": 1,
            "quality_score": 0,
            "coordinates": {},
            "theme": "unknown",
            "word_count": len(content.split())
        }]
    
    def pre_clean_content(self, content: str) -> str:
        """Clean content before processing"""
        # Remove YAML frontmatter if present
        content = re.sub(r'^---[\s\S]*?---\s*', '', content.strip())
        
        # Remove ChatGPT artifacts
        chatgpt_patterns = [
            r"Here's what I found[:.]\s*",
            r"I'll help you[^.]*\.\s*",
            r"Based on (?:the|this)[^.]*\.\s*"
        ]
        for pattern in chatgpt_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        # Normalize whitespace
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        content = re.sub(r'[ \t]+', ' ', content)
        
        return content.strip()
    
    def create_chunk_metadata(self, chunk_data: Dict[str, Any]) -> ChunkMetadata:
        """Create complete metadata structure for chunk"""
        chunk_id = self.generate_chunk_id()
        extraction_date = datetime.now().isoformat()
        
        # Get disposition
        dispo_info = self.determine_disposition(chunk_data["quality_score"])
        
        # Extract temporal markers
        date_info = self.extract_content_date(chunk_data["content"])
        
        # Detect modality
        modality = self.detect_modality(chunk_data["content"])
        
        # Create quality history entry
        quality_history = [{
            "score": chunk_data["quality_score"],
            "date": extraction_date,
            "method": "production_nibbler_v1",
            "human_edited": False
        }]
        
        return ChunkMetadata(
            chunk_id=chunk_id,
            extraction_date=extraction_date,
            chunk_source=chunk_data["source_file"],
            source_chunk_sequence=chunk_data["sequence"],
            
            content_date=date_info["content_date"],
            content_date_type=date_info["content_date_type"],
            content_date_status=date_info["content_date_status"],
            
            quality_score=chunk_data["quality_score"],
            quality_history=quality_history,
            
            disposition=dispo_info["disposition"],
            status=dispo_info["status"],
            priority=dispo_info["priority"],
            
            tesseract_coordinates=chunk_data["coordinates"],
            modality=modality,
            
            parent_piece=None,
            parent_piece_status="unassigned",
            
            next_action=None,
            annotations=None
        )
    
    def generate_yaml_frontmatter(self, metadata: ChunkMetadata) -> str:
        """Generate YAML frontmatter from metadata"""
        coords = metadata.tesseract_coordinates
        
        # Build tag list
        tags = []
        if coords.get("x_structure"):
            tags.append(f"x-structure/{coords['x_structure']}")
        if coords.get("y_transmission"):
            tags.append(f"y-transmission/{coords['y_transmission']}")
        if coords.get("z_purpose"):
            tags.append(f"z-purpose/{coords['z_purpose']}")
        if coords.get("w_terrain"):
            tags.append(f"w-terrain/{coords['w_terrain']}")
        
        yaml_content = f"""---
# Identity
chunk_id: {metadata.chunk_id}
extraction_date: {metadata.extraction_date}
chunk_source: {metadata.chunk_source}
source_chunk_sequence: {metadata.source_chunk_sequence}

# Temporal context
content_date: {metadata.content_date or 'null'}
content_date_type: {metadata.content_date_type or 'null'}
content_date_status: {metadata.content_date_status}

# Quality tracking
quality_score: {metadata.quality_score}
quality_history:
"""
        
        for entry in metadata.quality_history:
            yaml_content += f"""  - score: {entry['score']}
    date: {entry['date']}
    method: {entry['method']}
    human_edited: {str(entry['human_edited']).lower()}
"""
        
        yaml_content += f"""
# Disposition
disposition: {metadata.disposition}
status: {metadata.status}
priority: {metadata.priority}

# Tesseract coordinates
tags:
"""
        for tag in tags:
            yaml_content += f"  - {tag}\n"
        
        yaml_content += f"""
# Media/modality
modality:
"""
        for mod in metadata.modality:
            yaml_content += f"  - {mod}\n"
        
        yaml_content += f"""
# Parent piece assignment
parent_piece: {metadata.parent_piece or 'null'}
parent_piece_status: {metadata.parent_piece_status}

# Human annotations
next_action: {metadata.next_action or 'null'}
annotations: {metadata.annotations or 'null'}
---

"""
        return yaml_content
    
    def determine_destination_folder(self, metadata: ChunkMetadata) -> Path:
        """Determine destination folder based on disposition and coordinates"""
        if metadata.disposition == "memoir-grade":
            # Route by z_purpose
            z_purpose = metadata.tesseract_coordinates.get("z_purpose", "tell-story")
            folder = self.get_destination_from_purpose(z_purpose)
            return self.output_base / folder
        
        elif metadata.disposition == "promising":
            return self.output_base / "_review" / "promising"
        
        elif metadata.disposition == "borderline":
            return self.output_base / "_review" / "borderline"
        
        else:  # trash
            return self.output_base / "_archive" / "processed-trash"
    
    def write_chunk_file(self, metadata: ChunkMetadata, content: str) -> Path:
        """Write chunk to destination with frontmatter"""
        destination_folder = self.determine_destination_folder(metadata)
        destination_folder.mkdir(parents=True, exist_ok=True)
        
        filename = f"{metadata.chunk_id}.md"
        destination_path = destination_folder / filename
        
        # Generate full content
        yaml_frontmatter = self.generate_yaml_frontmatter(metadata)
        full_content = yaml_frontmatter + content
        
        destination_path.write_text(full_content, encoding='utf-8')
        return destination_path
    
    def process_single_file(self, file_path: Path, dry_run: bool = False) -> Dict[str, Any]:
        """Process a single file from _inload"""
        try:
            # Extract chunks (always analyze, even in dry run)
            chunks = self.extract_chunks_from_file(file_path)
            
            results = {
                "source_file": str(file_path.relative_to(self.source_dir.parent)),
                "chunks_extracted": len(chunks),
                "chunks": []
            }
            
            # Process each chunk
            for chunk_data in chunks:
                metadata = self.create_chunk_metadata(chunk_data)
                
                # Determine destination
                destination_folder = self.determine_destination_folder(metadata)
                destination_path = destination_folder / f"{metadata.chunk_id}.md"
                
                chunk_result = {
                    "chunk_id": metadata.chunk_id,
                    "quality_score": metadata.quality_score,
                    "disposition": metadata.disposition,
                    "coordinates": metadata.tesseract_coordinates,
                    "theme": chunk_data["theme"],
                    "word_count": chunk_data["word_count"],
                    "destination": str(destination_path.relative_to(self.output_base))
                }
                
                # Only write file if not dry run
                if not dry_run:
                    actual_destination = self.write_chunk_file(metadata, chunk_data["content"])
                    chunk_result["destination"] = str(actual_destination.relative_to(self.output_base))
                
                results["chunks"].append(chunk_result)
            
            return results
            
        except Exception as e:
            return {
                "source_file": str(file_path.relative_to(self.source_dir.parent)),
                "error": str(e),
                "chunks_extracted": 0
            }
    
    def process_batch(self, files: List[Path], batch_id: int, dry_run: bool = False) -> Dict[str, Any]:
        """Process a batch of files"""
        batch_results = []
        
        print(f"\n{'[DRY RUN] ' if dry_run else ''}Processing Batch {batch_id}: {len(files)} files")
        
        for file_path in files:
            result = self.process_single_file(file_path, dry_run=dry_run)
            batch_results.append(result)
            
            # Show summary for each file in dry run
            if dry_run and result["chunks_extracted"] > 0:
                print(f"  {file_path.name}:")
                for chunk in result.get("chunks", []):
                    print(f"    -> {chunk['disposition']} (Q:{chunk['quality_score']:.1f}) => {chunk['destination']}")
        
        # Calculate statistics
        total_chunks = sum(r["chunks_extracted"] for r in batch_results)
        disposition_counts = {
            "memoir-grade": 0,
            "promising": 0,
            "borderline": 0,
            "trash": 0
        }
        
        for result in batch_results:
            for chunk in result.get("chunks", []):
                disposition_counts[chunk["disposition"]] += 1
        
        batch_summary = {
            "batch_id": batch_id,
            "files_processed": len(files),
            "total_chunks_extracted": total_chunks,
            "disposition_distribution": disposition_counts,
            "results": batch_results
        }
        
        # Save batch log (even in dry run, for review)
        if not dry_run:
            log_dir = self.output_base / "_relocation_logs"
            log_file = log_dir / f"batch_{batch_id:03d}.json"
            with open(log_file, 'w') as f:
                json.dump(batch_summary, f, indent=2)
        
        print(f"Batch {batch_id} complete: {total_chunks} chunks extracted")
        print(f"   Dispositions: {disposition_counts}")
        
        return batch_summary
    
    def process_all_inload(self, batch_size: int = 10, dry_run: bool = False, limit: int = None) -> Dict[str, Any]:
        """Process all files in _inload directory"""
        
        if dry_run:
            print("\nDRY RUN MODE - Analyzing but not moving files\n")
        else:
            # Create backup before processing
            backup_path = self.create_backup()
        
        # Get all .md files in _inload
        md_files = list(self.source_dir.rglob("*.md"))
        
        if not md_files:
            print(f"No .md files found in {self.source_dir}")
            return {}
        
        # Limit for dry run or testing
        if limit:
            md_files = md_files[:limit]
        
        print(f"Found {len(md_files)} files to process")
        
        # Process in batches
        all_batch_summaries = []
        batch_id = 1
        
        for i in range(0, len(md_files), batch_size):
            batch_files = md_files[i:i + batch_size]
            batch_summary = self.process_batch(batch_files, batch_id, dry_run=dry_run)
            all_batch_summaries.append(batch_summary)
            batch_id += 1
        
        # Generate final summary
        total_chunks = sum(b["total_chunks_extracted"] for b in all_batch_summaries)
        total_files = sum(b["files_processed"] for b in all_batch_summaries)
        
        # Aggregate disposition counts
        total_dispositions = {
            "memoir-grade": 0,
            "promising": 0,
            "borderline": 0,
            "trash": 0
        }
        for batch in all_batch_summaries:
            for dispo, count in batch["disposition_distribution"].items():
                total_dispositions[dispo] += count
        
        final_summary = {
            "dry_run": dry_run,
            "total_files_processed": total_files,
            "total_chunks_extracted": total_chunks,
            "total_batches": len(all_batch_summaries),
            "disposition_distribution": total_dispositions,
            "processing_date": datetime.now().isoformat()
        }
        
        if not dry_run:
            final_summary["backup_location"] = str(backup_path)
            # Save final summary
            summary_file = self.output_base / "_relocation_logs" / "final_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(final_summary, f, indent=2)
        
        print(f"\n{'=' * 60}")
        print(f"{'DRY RUN ' if dry_run else ''}PROCESSING COMPLETE")
        print(f"{'=' * 60}")
        print(f"Files processed: {total_files}")
        print(f"Chunks extracted: {total_chunks}")
        print(f"\nDisposition breakdown:")
        print(f"  Memoir-grade: {total_dispositions['memoir-grade']}")
        print(f"  Promising: {total_dispositions['promising']}")
        print(f"  Borderline: {total_dispositions['borderline']}")
        print(f"  Trash: {total_dispositions['trash']}")
        
        if not dry_run:
            print(f"\nBackup: {backup_path}")
        else:
            print("\nNo files were moved (dry run)")
        
        return final_summary

def main():
    """Run production relocation nibbler"""
    
    nibbler = ProductionRelocationNibbler(SOURCE_DIR, OUTPUT_BASE, BACKUP_DIR)
    
    print("=" * 60)
    print("PRODUCTION RELOCATION NIBBLER")
    print("=" * 60)
    
    mode = input("\nChoose mode:\n  1. Dry run (3 files)\n  2. Dry run (full)\n  3. REAL run (full)\nChoice: ")
    
    if mode == "1":
        results = nibbler.process_all_inload(batch_size=10, dry_run=True, limit=3)
    elif mode == "2":
        results = nibbler.process_all_inload(batch_size=10, dry_run=True, limit=None)
    elif mode == "3":
        confirm = input("\nThis will process and relocate files. Continue? (yes/no): ")
        if confirm.lower() == "yes":
            results = nibbler.process_all_inload(batch_size=10, dry_run=False, limit=None)
        else:
            print("Cancelled")
            return
    else:
        print("Invalid choice")
        return

if __name__ == "__main__":
    main()
