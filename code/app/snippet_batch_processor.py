# snippet_batch_processor.py
# Process and organize high-value ChatGPT/AI conversation exports

import json
import shutil
from pathlib import Path
from datetime import datetime

class SnippetBatchProcessor:
    def __init__(self, vault_path, quality_threshold=20):
        self.vault_path = Path(vault_path)
        self.quality_threshold = quality_threshold
        self.processing_results = {
            "promoted": [],
            "archived": [],
            "errors": []
        }
    
    def process_snippets_from_inload(self, ai_collaboration_data):
        """Process snippet files based on content mining results"""
        
        high_value_snippets = []
        archive_candidates = []
        
        for file_data in ai_collaboration_data["files"]:
            file_path = file_data["file"]
            quality_score = file_data["quality"]
            
            # Check if it's tagged as snippet (would need to read YAML)
            if self.is_snippet_file(file_path):
                if quality_score >= self.quality_threshold:
                    high_value_snippets.append({
                        "file": file_path,
                        "quality": quality_score,
                        "ai_markers": file_data["ai_markers"],
                        "destination": self.suggest_destination(quality_score, file_path)
                    })
                else:
                    archive_candidates.append({
                        "file": file_path,
                        "quality": quality_score,
                        "reason": f"Quality {quality_score} below threshold {self.quality_threshold}"
                    })
        
        return {
            "promote_count": len(high_value_snippets),
            "archive_count": len(archive_candidates),
            "high_value_snippets": high_value_snippets,
            "archive_candidates": archive_candidates
        }
    
    def is_snippet_file(self, file_path):
        """Check if file is tagged as snippet by reading YAML frontmatter"""
        try:
            full_path = self.vault_path / file_path
            content = full_path.read_text(encoding='utf-8')
            
            if content.startswith('---'):
                yaml_end = content.find('---', 3)
                if yaml_end > 0:
                    yaml_content = content[3:yaml_end]
                    return 'snippet' in yaml_content.lower() or 'snippets' in yaml_content.lower()
            return False
        except Exception:
            return False
    
    def suggest_destination(self, quality_score, file_path):
        """Suggest where high-quality snippets should go"""
        if quality_score > 100:
            return "memoir/spine/integration/"  # Memoir-quality AI collaboration
        elif quality_score > 50:
            return "contribution/systems/"       # Substantial AI work documentation
        else:
            return "contribution/systems/snippets/"  # Lower-tier but still valuable
    
    def execute_batch_moves(self, snippet_analysis, dry_run=True):
        """Execute the batch moves for high-value snippets"""
        
        # Create backup first
        if not dry_run:
            backup_dir = self.vault_path.parent / f"snippet_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_dir.mkdir(exist_ok=True)
        
        moves_executed = []
        
        # Process high-value snippets
        for snippet in snippet_analysis["high_value_snippets"]:
            source = self.vault_path / snippet["file"]
            destination_dir = self.vault_path / snippet["destination"]
            destination = destination_dir / source.name
            
            if not dry_run:
                # Create backup
                backup_file = backup_dir / source.name
                shutil.copy2(source, backup_file)
                
                # Create destination directory
                destination_dir.mkdir(parents=True, exist_ok=True)
                
                # Move file
                source.rename(destination)
            
            moves_executed.append({
                "source": snippet["file"],
                "destination": str(destination.relative_to(self.vault_path)),
                "quality": snippet["quality"],
                "status": "moved" if not dry_run else "planned"
            })
        
        # Archive low-value snippets
        archive_dir = self.vault_path / "_archive" / "low_quality_snippets"
        archived_files = []
        
        for candidate in snippet_analysis["archive_candidates"]:
            source = self.vault_path / candidate["file"]
            archive_path = archive_dir / source.name
            
            if not dry_run:
                archive_dir.mkdir(parents=True, exist_ok=True)
                source.rename(archive_path)
            
            archived_files.append({
                "source": candidate["file"],
                "archived_to": str(archive_path.relative_to(self.vault_path)),
                "quality": candidate["quality"],
                "reason": candidate["reason"],
                "status": "archived" if not dry_run else "planned"
            })
        
        return {
            "dry_run": dry_run,
            "moves_executed": moves_executed,
            "files_archived": archived_files,
            "backup_location": str(backup_dir) if not dry_run else None,
            "summary": {
                "promoted": len(moves_executed),
                "archived": len(archived_files),
                "total_processed": len(moves_executed) + len(archived_files)
            }
        }

# Usage functions for API integration
def process_current_snippets(vault_path, ai_collaboration_data, quality_threshold=20):
    """Process snippets currently in _inload"""
    processor = SnippetBatchProcessor(vault_path, quality_threshold)
    return processor.process_snippets_from_inload(ai_collaboration_data)

def execute_snippet_reorganization(vault_path, snippet_analysis, dry_run=True):
    """Execute the snippet reorganization plan"""
    processor = SnippetBatchProcessor(vault_path)
    return processor.execute_batch_moves(snippet_analysis, dry_run)
