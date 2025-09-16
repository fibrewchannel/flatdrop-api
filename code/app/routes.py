from fastapi import APIRouter
from collections import Counter, defaultdict
from pathlib import Path
import re


router = APIRouter()

# Fixed imports - note the comma after VAULT_PATH and proper line continuation
from app.utils import (
    # Existing imports...
    validate_markdown, write_markdown_file, parse_yaml_frontmatter,
    fix_yaml_frontmatter, generate_obsidian_yaml, apply_tag_consolidation,
    extract_all_tags, analyze_consolidation_opportunities, create_backup_snapshot,
    CRITICAL_CONSOLIDATIONS,
    VAULT_PATH,  # Add comma here
    
    # NEW: Tesseract 4D functions
    extract_tesseract_position, calculate_memoir_priority, calculate_4d_coherence,
    find_tesseract_clusters, generate_tesseract_folder_path,
    
    # NEW: Content intelligence functions
    identify_document_archetype, extract_content_signature, count_internal_references,
    analyze_folder_content_types, measure_tag_coherence, extract_naming_patterns,
    calculate_urgency_score, group_by_archetype, generate_folder_path,
    calculate_priority, find_orphaned_files, chunked
)
# ============================================================================
# TESSERACT 4D COORDINATE SYSTEM ENDPOINTS
# ============================================================================

@router.get("/api/files/content")
async def get_file_content(file_path: str):
    """Retrieve the full content of a specific file"""
    try:
        full_path = VAULT_PATH / file_path
        
        if not full_path.exists():
            return {"error": f"File not found: {file_path}"}
        
        if not full_path.is_file():
            return {"error": f"Path is not a file: {file_path}"}
            
        content = full_path.read_text(encoding="utf-8")
        
        return {
            "file_path": file_path,
            "content": content,
            "size": len(content),
            "exists": True
        }
        
    except Exception as e:
        return {"error": f"Error reading file: {str(e)}"}

# Add these updates to your existing app/routes.py file

# Update the TESSERACT_REDUNDANT_MAPPINGS to include missing coordinate-redundant tags
TESSERACT_REDUNDANT_MAPPINGS = {
    # Existing mappings...
    "flatline-codex/flatline": "REMOVE_SYSTEM_REDUNDANT",
    "flatline": "REMOVE_SYSTEM_REDUNDANT",
    
    # X-axis structure redundancies
    "protocol": "REMOVE_X_AXIS_REDUNDANT",
    "summonings": "REMOVE_X_AXIS_REDUNDANT",
    "shadowcast": "REMOVE_X_AXIS_REDUNDANT",
    "archetype": "REMOVE_X_AXIS_REDUNDANT",
    
    # MISSING TAGS DISCOVERED DURING CONSOLIDATION:
    "ritual": "REMOVE_X_AXIS_REDUNDANT",     # 13 instances - X-axis structure
    "chaos": "REMOVE_W_AXIS_REDUNDANT",      # 8 instances - W-axis terrain
    "tarot": "REMOVE_Y_AXIS_REDUNDANT",      # 7 instances - Y-axis transmission
    
    # Z-axis purpose redundancies
    "recovery": "REMOVE_Z_AXIS_REDUNDANT",
    "memoir": "REMOVE_Z_AXIS_REDUNDANT",
    "survival": "REMOVE_Z_AXIS_REDUNDANT",
    
    # Y-axis transmission redundancies
    "narrative": "REMOVE_Y_AXIS_REDUNDANT"
}

# Enhanced TECHNICAL_REMOVALS for more complete cleanup
TECHNICAL_REMOVALS = {
    # Number tags (discovered in consolidation)
    1: "REMOVE_NUMBER_TAG",
    2: "REMOVE_NUMBER_TAG",
    3: "REMOVE_NUMBER_TAG",
    4: "REMOVE_NUMBER_TAG",
    5: "REMOVE_NUMBER_TAG",
    6: "REMOVE_NUMBER_TAG",
    7: "REMOVE_NUMBER_TAG",
    8: "REMOVE_NUMBER_TAG",
    9: "REMOVE_NUMBER_TAG",
    10: "REMOVE_NUMBER_TAG",
    111: "REMOVE_NUMBER_TAG",
    222: "REMOVE_NUMBER_TAG",
    222129: "REMOVE_NUMBER_TAG",
    320: "REMOVE_NUMBER_TAG",  # Discovered in final audit
    102: "REMOVE_NUMBER_TAG",  # Discovered in final audit
    220: "REMOVE_NUMBER_TAG",  # Discovered in final audit
    
    # Placeholder remnants
    "REMOVE_SYSTEM_REDUNDANT": "REMOVE_PLACEHOLDER",
    "REMOVE_X_AXIS_REDUNDANT": "REMOVE_PLACEHOLDER",
    "REMOVE_Y_AXIS_REDUNDANT": "REMOVE_PLACEHOLDER",
    "REMOVE_Z_AXIS_REDUNDANT": "REMOVE_PLACEHOLDER",
    "REMOVE_W_AXIS_REDUNDANT": "REMOVE_PLACEHOLDER",
    
    # Null values
    "None": "REMOVE_NULL",
    "null": "REMOVE_NULL"
}

# Enhanced FORMAT_CONSOLIDATIONS with discovered variations
FORMAT_CONSOLIDATIONS = {
    # Format variations discovered during consolidation
    "thread-dump": "threaddump",        # 15 instances → merge with threaddump (18)
    "_import": "import",                # 14 instances → merge with import (18)
    "ritual/ritual-nourishment": "ritual-nourishment",  # 10 instances
    
    # Color codes - standardize to color-HEXCODE format
    "colors/8A91C5": "color-8a91c5",
    "colors/FFA86A": "color-ffa86a",
    "colors/": "color-generic",
    "b9f5d8": "color-b9f5d8",
    "bc8d6b": "color-bc8d6b",
    "colors-0a0a23": "color-0a0a23",
    "colors-1a1a1a": "color-1a1a1a",
    "colors-47c6a6": "color-47c6a6",
    "colors-6e5ba0": "color-6e5ba0",
    "colors-80ffd3": "color-80ffd3",
    "colors-8c9b3e": "color-8c9b3e",
    "colors-a34726": "color-a34726",
    "colors-c1a837": "color-c1a837",
    
    # Case standardizations
    "UX": "ux",
    "Codex": "codex",
    "Tags": "tags",
    "AI": "ai",
    "LTR": "ltr"
}

# Add new endpoint for comprehensive final cleanup
@router.post("/api/tags/final-consolidation-cleanup")
async def final_consolidation_cleanup(dry_run: bool = True):
    """
    Comprehensive final cleanup targeting remaining issues discovered in consolidation
    Combines missing coordinate mappings + format consolidations
    """
    
    files_processed = 0
    total_changes = 0
    coordinate_removals = 0
    format_consolidations = 0
    changes_log = []
    
    # Combine all remaining cleanup mappings
    final_cleanup_mappings = {
        # Missing coordinate-redundant tags
        "ritual": "",           # Remove completely
        "chaos": "",            # Remove completely
        "tarot": "",            # Remove completely
        
        # Format consolidations
        "thread-dump": "threaddump",
        "_import": "import",
        "ritual/ritual-nourishment": "ritual-nourishment",
    }
    
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            if content.startswith("---"):
                yaml_data = parse_yaml_frontmatter(content)
                if yaml_data and 'tags' in yaml_data:
                    original_tags = yaml_data['tags']
                    if isinstance(original_tags, list):
                        updated_tags = []
                        file_changes = []
                        
                        for tag in original_tags:
                            if tag in final_cleanup_mappings:
                                new_value = final_cleanup_mappings[tag]
                                if new_value == "":
                                    # Remove tag completely
                                    file_changes.append(f"REMOVED: {tag}")
                                    coordinate_removals += 1
                                else:
                                    # Consolidate format
                                    updated_tags.append(new_value)
                                    file_changes.append(f"CONSOLIDATED: {tag} → {new_value}")
                                    format_consolidations += 1
                            else:
                                updated_tags.append(tag)
                        
                        if file_changes:
                            yaml_data['tags'] = sorted(set(updated_tags))
                            changes_log.extend(file_changes)
                            total_changes += len(file_changes)
                            
                            if not dry_run:
                                lines = content.split('\n')
                                yaml_end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), -1)
                                if yaml_end > 0:
                                    new_yaml = generate_obsidian_yaml(yaml_data)
                                    updated_content = new_yaml + '\n' + '\n'.join(lines[yaml_end + 1:])
                                    md_file.write_text(updated_content, encoding="utf-8")
            
            files_processed += 1
            
        except Exception as e:
            print(f"Error processing {md_file}: {e}")
    
    return {
        "dry_run": dry_run,
        "files_processed": files_processed,
        "coordinate_removals": coordinate_removals,
        "format_consolidations": format_consolidations,
        "total_changes": total_changes,
        "sample_changes": changes_log[:20],
        "estimated_tag_reduction": coordinate_removals + (format_consolidations // 2),
        "message": "Preview mode - no files changed" if dry_run else "Final consolidation cleanup completed"
    }

# Add endpoint to verify consolidation completion
@router.get("/api/tags/consolidation-status")
async def check_consolidation_status():
    """Check the current status of tag consolidation and identify remaining issues"""
    
    # Get current tag state
    tag_counter = Counter()
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            tags = extract_all_tags(md_file)
            tag_counter.update(tags)
        except Exception:
            continue
    
    # Check for remaining consolidation targets
    remaining_coordinate_redundant = []
    remaining_format_issues = []
    remaining_technical_artifacts = []
    
    coordinate_redundant_patterns = ["ritual", "chaos", "tarot", "protocol", "archetype", "narrative", "shadowcast"]
    format_issue_patterns = ["thread-dump", "_import", "ritual/", "colors/"]
    technical_artifact_patterns = [111, 222, 320, 102, 220, "REMOVE_"]
    
    for tag, count in tag_counter.items():
        tag_str = str(tag)
        
        # Check coordinate redundancy
        if any(pattern in tag_str for pattern in coordinate_redundant_patterns):
            remaining_coordinate_redundant.append({"tag": tag, "count": count})
        
        # Check format issues
        elif any(pattern in tag_str for pattern in format_issue_patterns):
            remaining_format_issues.append({"tag": tag, "count": count})
        
        # Check technical artifacts
        elif any(str(pattern) in tag_str for pattern in technical_artifact_patterns):
            remaining_technical_artifacts.append({"tag": tag, "count": count})
    
    # Calculate consolidation completeness
    total_remaining_issues = len(remaining_coordinate_redundant) + len(remaining_format_issues) + len(remaining_technical_artifacts)
    consolidation_completeness = max(0, 100 - (total_remaining_issues * 2))  # Rough estimate
    
    return {
        "current_tag_count": len(tag_counter),
        "total_instances": sum(tag_counter.values()),
        "consolidation_completeness_percent": round(consolidation_completeness, 1),
        "remaining_issues": {
            "coordinate_redundant": remaining_coordinate_redundant,
            "format_inconsistencies": remaining_format_issues,
            "technical_artifacts": remaining_technical_artifacts
        },
        "total_remaining_issues": total_remaining_issues,
        "recommendations": [
            "Run final-consolidation-cleanup to address remaining coordinate redundancy" if remaining_coordinate_redundant else None,
            "Apply format standardization for remaining inconsistencies" if remaining_format_issues else None,
            "Clean technical artifacts with execute-technical-cleanup" if remaining_technical_artifacts else None,
            "Consolidation appears complete!" if total_remaining_issues == 0 else None
        ],
        "next_step": (
            "POST /api/tags/final-consolidation-cleanup?dry_run=false" if total_remaining_issues > 0
            else "Consolidation complete - system optimized"
        )
    }
    
@router.post("/api/tags/consolidate")
async def consolidate_tesseract_redundant_tags(dry_run: bool = True):
    """Consolidate tags that are redundant with Tesseract coordinates"""
    
    # Define Tesseract redundant tags based on your analysis
    TESSERACT_REDUNDANT_MAPPINGS = {
        # Flatline system redundancies
        "flatline-codex/flatline": "REMOVE_SYSTEM_REDUNDANT",
        "flatline": "REMOVE_SYSTEM_REDUNDANT",
        
        # X-axis structure redundancies
        "protocol": "REMOVE_X_AXIS_REDUNDANT",
        "summonings": "REMOVE_X_AXIS_REDUNDANT",
        "shadowcast": "REMOVE_X_AXIS_REDUNDANT",
        "archetype": "REMOVE_X_AXIS_REDUNDANT",
        
        # Z-axis purpose redundancies
        "recovery": "REMOVE_Z_AXIS_REDUNDANT",
        "memoir": "REMOVE_Z_AXIS_REDUNDANT",
        "survival": "REMOVE_Z_AXIS_REDUNDANT",
        
        # Y-axis transmission redundancies
        "narrative": "REMOVE_Y_AXIS_REDUNDANT"
    }
    
    files_processed = 0
    tags_removed = 0
    changes_made = []
    
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            updated_content, file_changes = apply_tag_consolidation(content, TESSERACT_REDUNDANT_MAPPINGS)
            
            if file_changes and not dry_run:
                md_file.write_text(updated_content, encoding="utf-8")
                
            files_processed += 1
            tags_removed += len(file_changes)
            changes_made.extend(file_changes)
            
        except Exception as e:
            print(f"Error processing {md_file}: {e}")
    
    return {
        "dry_run": dry_run,
        "files_processed": files_processed,
        "estimated_tags_removed": tags_removed,
        "sample_changes": changes_made[:20],
        "total_changes": len(changes_made),
        "message": "Preview mode - no files changed" if dry_run else "Tags consolidated successfully"
    }
    
@router.post("/api/tags/consolidate-singletons")
async def consolidate_singletons(dry_run: bool = True):
    """Consolidate singleton tags into established tags for semantic compression"""
    
    # Get current tag counts
    tag_counter = Counter()
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            tags = extract_all_tags(md_file)
            tag_counter.update(tags)
        except Exception:
            continue
    
    # Identify singletons and established tags
    singletons = [tag for tag, count in tag_counter.items() if count == 1]
    established = {tag: count for tag, count in tag_counter.items() if count > 3}
    
    # Define consolidation mappings
    consolidation_map = {}
    
    # Recovery-related consolidations
    recovery_singletons = [tag for tag in singletons if any(keyword in str(tag).lower()
                          for keyword in ['step', 'resentment', 'amends', 'inventory', 'spiritual'])]
    for tag in recovery_singletons:
        if 'aa' in established:
            consolidation_map[tag] = 'aa'
        elif 'recovery' in established:
            consolidation_map[tag] = 'recovery'
    
    # Emotional/psychological consolidations
    emotional_singletons = [tag for tag in singletons if any(keyword in str(tag).lower()
                           for keyword in ['rage', 'grief', 'authenticity', 'validation', 'burnout'])]
    for tag in emotional_singletons:
        if 'emotion' in established:
            consolidation_map[tag] = 'emotion'
        elif 'psych' in established:
            consolidation_map[tag] = 'psych'
    
    # Technical/tool consolidations
    tech_singletons = [tag for tag in singletons if any(keyword in str(tag).lower()
                      for keyword in ['api', 'python', 'code', 'system', 'tech'])]
    for tag in tech_singletons:
        if 'obsidian' in established:
            consolidation_map[tag] = 'obsidian'
        elif 'ai' in established:
            consolidation_map[tag] = 'ai'
    
    # Creative/artistic consolidations
    creative_singletons = [tag for tag in singletons if any(keyword in str(tag).lower()
                          for keyword in ['art', 'music', 'creative', 'design', 'aesthetic'])]
    for tag in creative_singletons:
        if 'aiart' in established:
            consolidation_map[tag] = 'aiart'
        elif 'creative' in established:
            consolidation_map[tag] = 'creative'
    
    # Work/career consolidations
    work_singletons = [tag for tag in singletons if any(keyword in str(tag).lower()
                      for keyword in ['job', 'interview', 'resume', 'career', 'work'])]
    for tag in work_singletons:
        if 'resume' in established:
            consolidation_map[tag] = 'resume'
    
    # Apply consolidations
    files_processed = 0
    consolidations_made = 0
    changes_log = []
    
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            if content.startswith("---"):
                yaml_data = parse_yaml_frontmatter(content)
                if yaml_data and 'tags' in yaml_data:
                    original_tags = yaml_data['tags']
                    if isinstance(original_tags, list):
                        updated_tags = []
                        file_changes = []
                        
                        for tag in original_tags:
                            if tag in consolidation_map:
                                new_tag = consolidation_map[tag]
                                updated_tags.append(new_tag)
                                file_changes.append(f"CONSOLIDATED: {tag} -> {new_tag}")
                                consolidations_made += 1
                            else:
                                updated_tags.append(tag)
                        
                        if file_changes:
                            yaml_data['tags'] = sorted(set(updated_tags))
                            changes_log.extend(file_changes)
                            
                            if not dry_run:
                                lines = content.split('\n')
                                yaml_end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), -1)
                                if yaml_end > 0:
                                    new_yaml = generate_obsidian_yaml(yaml_data)
                                    updated_content = new_yaml + '\n' + '\n'.join(lines[yaml_end + 1:])
                                    md_file.write_text(updated_content, encoding="utf-8")
            
            files_processed += 1
            
        except Exception as e:
            print(f"Error processing {md_file}: {e}")
    
    return {
        "dry_run": dry_run,
        "files_processed": files_processed,
        "total_singletons": len(singletons),
        "consolidation_opportunities": len(consolidation_map),
        "consolidations_made": consolidations_made,
        "sample_consolidations": changes_log[:20],
        "consolidation_groups": {
            "recovery": len(recovery_singletons),
            "emotional": len(emotional_singletons),
            "technical": len(tech_singletons),
            "creative": len(creative_singletons),
            "work": len(work_singletons)
        },
        "estimated_tag_reduction": len(consolidation_map),
        "message": "Preview mode - no consolidations applied" if dry_run else "Singleton consolidation completed"
    }
    
@router.post("/api/inload/mine-memoir-content")
async def mine_inload_memoir_content():
    """Extract memoir-worthy content from _inload directories using Tesseract analysis"""
    
    inload_analysis = {
        "high_priority_finds": [],
        "memoir_candidates": [],
        "recovery_narratives": [],
        "temporal_content": [],
        "character_development": [],
        "low_priority": []
    }
    
    files_processed = 0
    
    # Scan all _inload directories
    for inload_path in VAULT_PATH.rglob("*inload*"):
        if inload_path.is_dir():
            for md_file in inload_path.rglob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    file_path_str = str(md_file.relative_to(VAULT_PATH))
                    
                    # Extract Tesseract coordinates
                    coordinates = extract_tesseract_position(content)
                    memoir_priority = calculate_memoir_priority(coordinates, content)
                    
                    file_info = {
                        "file": file_path_str,
                        "coordinates": coordinates,
                        "memoir_priority": memoir_priority,
                        "word_count": len(content.split()),
                        "has_narrative_markers": check_narrative_markers(content),
                        "temporal_indicators": extract_temporal_indicators(content),
                        "emotional_intensity": assess_emotional_content(content)
                    }
                    
                    # Categorize based on memoir value
                    if memoir_priority > 0.7:
                        inload_analysis["high_priority_finds"].append(file_info)
                    elif coordinates["z_purpose"] == "tell-story" and coordinates["y_transmission"] == "narrative":
                        inload_analysis["memoir_candidates"].append(file_info)
                    elif coordinates["z_purpose"] == "help-addict" and memoir_priority > 0.4:
                        inload_analysis["recovery_narratives"].append(file_info)
                    elif file_info["temporal_indicators"]["has_dates"] or file_info["temporal_indicators"]["has_timeline"]:
                        inload_analysis["temporal_content"].append(file_info)
                    elif file_info["has_narrative_markers"]["character_references"] > 2:
                        inload_analysis["character_development"].append(file_info)
                    else:
                        inload_analysis["low_priority"].append(file_info)
                    
                    files_processed += 1
                    
                except Exception as e:
                    print(f"Error processing {md_file}: {e}")
    
    # Generate rescue recommendations
    rescue_candidates = []
    
    # High priority files (immediate rescue)
    for file_info in inload_analysis["high_priority_finds"]:
        rescue_candidates.append({
            "file": file_info["file"],
            "priority": "immediate",
            "reason": f"High memoir priority ({file_info['memoir_priority']:.2f})",
            "suggested_destination": generate_tesseract_folder_path(
                file_info["coordinates"]["z_purpose"],
                file_info["coordinates"]["x_structure"]
            )
        })
    
    # Strong memoir candidates
    for file_info in inload_analysis["memoir_candidates"]:
        rescue_candidates.append({
            "file": file_info["file"],
            "priority": "high",
            "reason": "Story-focused narrative content",
            "suggested_destination": "memoir/narratives"
        })
    
    # Recovery narratives worth preserving
    for file_info in inload_analysis["recovery_narratives"]:
        rescue_candidates.append({
            "file": file_info["file"],
            "priority": "medium",
            "reason": "Recovery narrative with memoir potential",
            "suggested_destination": "memoir/recovery-narratives"
        })
    
    return {
        "files_scanned": files_processed,
        "inload_analysis": inload_analysis,
        "rescue_recommendations": rescue_candidates,
        "summary": {
            "high_priority_finds": len(inload_analysis["high_priority_finds"]),
            "memoir_candidates": len(inload_analysis["memoir_candidates"]),
            "recovery_narratives": len(inload_analysis["recovery_narratives"]),
            "total_rescue_worthy": len(rescue_candidates)
        },
        "next_steps": [
            "Review high priority finds for immediate rescue",
            "Evaluate memoir candidates for narrative value",
            "Consider recovery narratives for memoir integration",
            "Execute rescue operations in priority order"
        ]
    }

def check_narrative_markers(content: str) -> dict:
    """Check for narrative storytelling markers"""
    markers = {
        "first_person_narrative": content.lower().count("i ") + content.lower().count("me "),
        "character_references": len(re.findall(r'\b[A-Z][a-z]+\b', content)),
        "dialogue_markers": content.count('"') + content.count("'"),
        "scene_setting": any(word in content.lower() for word in ["when ", "where ", "scene", "setting"]),
        "emotional_language": sum(content.lower().count(word) for word in ["felt", "emotion", "remember", "experience"])
    }
    return markers

def extract_temporal_indicators(content: str) -> dict:
    """Extract temporal/chronological markers"""
    indicators = {
        "has_dates": bool(re.search(r'\b(19|20)\d{2}\b', content)),
        "has_timeline": any(word in content.lower() for word in ["then", "next", "after", "before", "during"]),
        "childhood_markers": any(word in content.lower() for word in ["childhood", "growing up", "as a kid"]),
        "age_references": len(re.findall(r'\b\d{1,2}\s*years?\s*old\b', content.lower())),
        "recovery_timeline": any(word in content.lower() for word in ["sobriety", "clean time", "relapse"])
    }
    return indicators

def assess_emotional_content(content: str) -> float:
    """Assess emotional intensity for memoir potential"""
    emotional_words = ["pain", "joy", "fear", "love", "anger", "hope", "despair", "peace", "rage", "grief"]
    intensity_words = ["overwhelming", "devastating", "incredible", "amazing", "terrible", "beautiful"]
    
    emotion_score = sum(content.lower().count(word) for word in emotional_words)
    intensity_score = sum(content.lower().count(word) for word in intensity_words)
    
    return min(10.0, (emotion_score + intensity_score * 2) / max(len(content.split()) / 100, 1))

@router.post("/api/tags/execute-singleton-consolidation")
async def execute_singleton_consolidation(dry_run: bool = True):
    """Execute singleton consolidation with corrected therapeutic content mapping"""
    
    # Get current tag counts
    tag_counter = Counter()
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            tags = extract_all_tags(md_file)
            tag_counter.update(tags)
        except Exception:
            continue
    
    # Identify singletons
    singletons = [tag for tag, count in tag_counter.items() if count == 1]
    
    # Define corrected consolidation mappings
    consolidation_map = {}
    
    for tag in singletons:
        tag_str = str(tag).lower()
        
        # Therapeutic/DBT content - corrected mapping
        if 'dbt' in tag_str or 'distress-tolerance' in tag_str or 'worksheet' in tag_str:
            consolidation_map[tag] = 'dbt'
        
        # Recovery/AA content
        elif any(keyword in tag_str for keyword in ['step', 'resentment', 'amends', 'inventory', 'spiritual-practice']):
            consolidation_map[tag] = 'aa'
        
        # Emotional/psychological (non-DBT)
        elif any(keyword in tag_str for keyword in ['rage', 'grief', 'authenticity', 'validation', 'burnout']):
            consolidation_map[tag] = 'psych'
        
        # Technical/system content
        elif any(keyword in tag_str for keyword in ['api', 'python', 'code', 'system', 'flatline-codex']):
            consolidation_map[tag] = 'obsidian'
        
        # Creative/artistic content
        elif any(keyword in tag_str for keyword in ['art', 'music', 'creative', 'design', 'aesthetic']):
            consolidation_map[tag] = 'aiart'
        
        # Work/career content (but not therapy)
        elif any(keyword in tag_str for keyword in ['job', 'interview', 'resume', 'career', 'work']) and 'dbt' not in tag_str:
            consolidation_map[tag] = 'resume'
    
    # Execute consolidations
    files_processed = 0
    consolidations_made = 0
    changes_log = []
    
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            if content.startswith("---"):
                yaml_data = parse_yaml_frontmatter(content)
                if yaml_data and 'tags' in yaml_data:
                    original_tags = yaml_data['tags']
                    if isinstance(original_tags, list):
                        updated_tags = []
                        file_changes = []
                        
                        for tag in original_tags:
                            if tag in consolidation_map:
                                new_tag = consolidation_map[tag]
                                updated_tags.append(new_tag)
                                file_changes.append(f"CONSOLIDATED: {tag} -> {new_tag}")
                                consolidations_made += 1
                            else:
                                updated_tags.append(tag)
                        
                        if file_changes:
                            yaml_data['tags'] = sorted(set(updated_tags))
                            changes_log.extend(file_changes)
                            
                            if not dry_run:
                                lines = content.split('\n')
                                yaml_end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), -1)
                                if yaml_end > 0:
                                    new_yaml = generate_obsidian_yaml(yaml_data)
                                    updated_content = new_yaml + '\n' + '\n'.join(lines[yaml_end + 1:])
                                    md_file.write_text(updated_content, encoding="utf-8")
            
            files_processed += 1
            
        except Exception as e:
            print(f"Error processing {md_file}: {e}")
    
    return {
        "dry_run": dry_run,
        "files_processed": files_processed,
        "consolidations_made": consolidations_made,
        "sample_consolidations": changes_log[:20],
        "estimated_tag_reduction": len(consolidation_map),
        "message": "Preview mode" if dry_run else "Corrected singleton consolidation completed"
    }

@router.post("/api/tags/execute-technical-cleanup")
async def execute_technical_cleanup(dry_run: bool = True):
    """Execute technical cleanup: remove artifacts, standardize formats, fix case variants"""
    
    # Define technical cleanup mappings
    TECHNICAL_REMOVALS = {
        # Number tags
        1: "REMOVE_NUMBER_TAG",
        2: "REMOVE_NUMBER_TAG",
        3: "REMOVE_NUMBER_TAG",
        4: "REMOVE_NUMBER_TAG",
        5: "REMOVE_NUMBER_TAG",
        6: "REMOVE_NUMBER_TAG",
        7: "REMOVE_NUMBER_TAG",
        8: "REMOVE_NUMBER_TAG",
        9: "REMOVE_NUMBER_TAG",
        10: "REMOVE_NUMBER_TAG",
        111: "REMOVE_NUMBER_TAG",
        222: "REMOVE_NUMBER_TAG",
        222129: "REMOVE_NUMBER_TAG",
        888: "REMOVE_NUMBER_TAG",
        
        # Placeholder remnants
        "REMOVE_SYSTEM_REDUNDANT": "REMOVE_PLACEHOLDER",
        "REMOVE_X_AXIS_REDUNDANT": "REMOVE_PLACEHOLDER",
        "REMOVE_Z_AXIS_REDUNDANT": "REMOVE_PLACEHOLDER",
        
        # Null values
        "None": "REMOVE_NULL",
        "null": "REMOVE_NULL"
    }
    
    # Format standardizations
    FORMAT_CONSOLIDATIONS = {
        # Color codes - standardize to color-HEXCODE format
        "colors/8A91C5": "color-8a91c5",
        "colors/FFA86A": "color-ffa86a",
        "colors/": "color-generic",
        "b9f5d8": "color-b9f5d8",
        "bc8d6b": "color-bc8d6b",
        "colors-0a0a23": "color-0a0a23",
        "colors-1a1a1a": "color-1a1a1a",
        "colors-47c6a6": "color-47c6a6",
        "colors-6e5ba0": "color-6e5ba0",
        "colors-80ffd3": "color-80ffd3",
        "colors-8c9b3e": "color-8c9b3e",
        "colors-a34726": "color-a34726",
        "colors-c1a837": "color-c1a837",
        
        # Case standardizations - choose lowercase
        "UX": "ux",
        "Codex": "codex",
        "Tags": "tags",
        "AI": "ai",
        "LTR": "ltr"
    }
    
    files_processed = 0
    total_removals = 0
    total_consolidations = 0
    changes_made = []
    
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            if content.startswith("---"):
                yaml_data = parse_yaml_frontmatter(content)
                if yaml_data and 'tags' in yaml_data:
                    original_tags = yaml_data['tags']
                    if isinstance(original_tags, list):
                        updated_tags = []
                        file_changes = []
                        
                        for tag in original_tags:
                            # Check for technical removals
                            if tag in TECHNICAL_REMOVALS:
                                file_changes.append(f"REMOVED: {tag} ({TECHNICAL_REMOVALS[tag]})")
                                total_removals += 1
                                continue  # Skip adding to updated_tags
                                
                            # Check for format consolidations
                            elif tag in FORMAT_CONSOLIDATIONS:
                                new_tag = FORMAT_CONSOLIDATIONS[tag]
                                updated_tags.append(new_tag)
                                file_changes.append(f"STANDARDIZED: {tag} -> {new_tag}")
                                total_consolidations += 1
                            else:
                                updated_tags.append(tag)
                        
                        # Apply changes if any were made
                        if file_changes:
                            yaml_data['tags'] = sorted(set(updated_tags))
                            changes_made.extend(file_changes)
                            
                            if not dry_run:
                                lines = content.split('\n')
                                yaml_end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), -1)
                                if yaml_end > 0:
                                    new_yaml = generate_obsidian_yaml(yaml_data)
                                    updated_content = new_yaml + '\n' + '\n'.join(lines[yaml_end + 1:])
                                    md_file.write_text(updated_content, encoding="utf-8")
            
            files_processed += 1
            
        except Exception as e:
            print(f"Error processing {md_file}: {e}")
    
    return {
        "dry_run": dry_run,
        "files_processed": files_processed,
        "technical_removals": total_removals,
        "format_consolidations": total_consolidations,
        "total_changes": len(changes_made),
        "sample_changes": changes_made[:20],
        "estimated_tag_reduction": total_removals + (total_consolidations // 2),
        "message": "Preview mode - no files changed" if dry_run else "Technical cleanup completed successfully"
    }

@router.get("/api/tags/identify-reduction-candidates")
async def identify_tag_reduction_candidates():
    """Identify specific tags for reduction using strategic criteria"""
    
    # Get current tag counts
    tag_counter = Counter()
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            tags = extract_all_tags(md_file)
            tag_counter.update(tags)
        except Exception:
            continue
    
    reduction_candidates = {
        "technical_artifacts": [],
        "format_consolidations": {},
        "over_granular": [],
        "case_variants": {},
        "low_value_singletons": [],
        "concept_duplicates": {}
    }
    
    all_tags = list(tag_counter.keys())
    
    # 1. Technical artifacts (easy removals)
    for tag in all_tags:
        tag_str = str(tag)
        if (isinstance(tag, int) or
            tag in ['null', 'None', ''] or
            tag_str.startswith('REMOVE_') or
            tag_str.isdigit()):
            reduction_candidates["technical_artifacts"].append({
                "tag": tag,
                "count": tag_counter[tag],
                "reason": "technical_artifact"
            })
    
    # 2. Format consolidations
    # Color codes
    color_tags = [tag for tag in all_tags if 'color' in str(tag).lower()]
    if len(color_tags) > 1:
        reduction_candidates["format_consolidations"]["color_codes"] = {
            "tags": color_tags,
            "suggestion": "Standardize to 'color-HEXCODE' format",
            "potential_removals": len(color_tags) - 1
        }
    
    # Ritual format variations
    ritual_tags = [tag for tag in all_tags if 'ritual' in str(tag).lower()]
    slash_rituals = [tag for tag in ritual_tags if '/' in str(tag)]
    hyphen_rituals = [tag for tag in ritual_tags if '-' in str(tag) and '/' not in str(tag)]
    if slash_rituals and hyphen_rituals:
        reduction_candidates["format_consolidations"]["ritual_separators"] = {
            "slash_format": slash_rituals,
            "hyphen_format": hyphen_rituals,
            "suggestion": "Standardize separator format",
            "potential_removals": min(len(slash_rituals), len(hyphen_rituals))
        }
    
    # 3. Case variants
    case_groups = {}
    for tag in all_tags:
        if isinstance(tag, str):
            lower_key = tag.lower()
            if lower_key not in case_groups:
                case_groups[lower_key] = []
            case_groups[lower_key].append(tag)
    
    for key, variants in case_groups.items():
        if len(variants) > 1:
            total_instances = sum(tag_counter[tag] for tag in variants)
            reduction_candidates["case_variants"][key] = {
                "variants": variants,
                "total_instances": total_instances,
                "potential_removals": len(variants) - 1
            }
    
    # 4. Over-granular tags (length and complexity)
    for tag in all_tags:
        tag_str = str(tag)
        if (len(tag_str) > 50 or
            (tag_counter[tag] == 1 and len(tag_str.split('-')) > 4) or
            ' ' in tag_str and len(tag_str.split()) > 5):
            reduction_candidates["over_granular"].append({
                "tag": tag,
                "count": tag_counter[tag],
                "length": len(tag_str),
                "reason": "overly_specific"
            })
    
    # 5. Low-value singletons (appear once, not memoir-critical)
    memoir_critical_patterns = ['nyx', 'mayo', 'rochester', 'draw-things', 'sponsor', 'therapy', 'aa', 'recovery']
    for tag in all_tags:
        if tag_counter[tag] == 1:
            tag_str = str(tag).lower()
            is_memoir_critical = any(pattern in tag_str for pattern in memoir_critical_patterns)
            is_date = any(char.isdigit() for char in tag_str) and ('202' in tag_str or 'day' in tag_str)
            
            if not is_memoir_critical and not is_date and len(tag_str) > 3:
                reduction_candidates["low_value_singletons"].append({
                    "tag": tag,
                    "reason": "singleton_not_memoir_critical"
                })
    
    # Calculate total reduction potential
    total_removals = (
        len(reduction_candidates["technical_artifacts"]) +
        sum(item.get("potential_removals", 0) for item in reduction_candidates["format_consolidations"].values()) +
        sum(item.get("potential_removals", 0) for item in reduction_candidates["case_variants"].values()) +
        len(reduction_candidates["over_granular"]) +
        len(reduction_candidates["low_value_singletons"])
    )
    
    return {
        "current_total_tags": len(all_tags),
        "target_reduction": len(all_tags) // 3,
        "identified_reduction_potential": total_removals,
        "reduction_categories": reduction_candidates,
        "meets_target": total_removals >= len(all_tags) // 3,
        "next_steps": [
            "Review technical artifacts for immediate removal",
            "Choose format standards (color codes, separators)",
            "Consolidate case variants",
            "Evaluate over-granular tags for memoir relevance",
            "Remove low-value singletons"
        ]
    }

@router.get("/api/tags/analyze-singletons")
async def analyze_singleton_tags():
    """Analyze singleton tags to categorize by value and identify cleanup opportunities"""
    
    # Get current tag counts
    tag_counter = Counter()
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            tags = extract_all_tags(md_file)
            tag_counter.update(tags)
        except Exception:
            continue
    
    # Identify singletons (tags appearing exactly once)
    singletons = [tag for tag, count in tag_counter.items() if count == 1]
    
    # Categorize singletons
    categorized = {
        "high_value_preservation": [],
        "format_consolidation": [],
        "cleanup_candidates": [],
        "case_variants": [],
        "technical_artifacts": []
    }
    
    for tag in singletons:
        tag_str = str(tag).lower()
        
        # High-value preservation candidates
        if any(marker in tag_str for marker in ['nyx', 'mayo', 'rochester', 'draw-things', 'sponsor', 'therapy']):
            categorized["high_value_preservation"].append(tag)
        
        # Case variants (same word, different case)
        elif any(variant in [t.lower() for t in tag_counter.keys() if t != tag] for variant in [tag_str]):
            categorized["case_variants"].append(tag)
        
        # Technical artifacts
        elif tag in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] or tag in ['null', 'None', '']:
            categorized["technical_artifacts"].append(tag)
        
        # Format inconsistencies (color codes, slashes vs hyphens)
        elif 'color' in tag_str or '/' in str(tag) or tag_str.startswith(('#', 'remove_')):
            categorized["format_consolidation"].append(tag)
        
        # Over-granular or experimental tags
        elif len(str(tag)) > 50 or '-' in str(tag) and len(str(tag).split('-')) > 5:
            categorized["cleanup_candidates"].append(tag)
        
        # Default to preservation if unclear
        else:
            categorized["high_value_preservation"].append(tag)
    
    # Generate consolidation suggestions
    consolidation_suggestions = []
    
    # Color code standardization
    color_tags = [tag for tag in tag_counter.keys() if 'color' in str(tag).lower()]
    if len(color_tags) > 1:
        consolidation_suggestions.append({
            "type": "color_standardization",
            "tags": color_tags,
            "suggestion": "Standardize to 'color-HEXCODE' format"
        })
    
    # Case variant consolidation
    case_groups = defaultdict(list)
    for tag in tag_counter.keys():
        case_groups[str(tag).lower()].append(tag)
    
    case_variants = {key: tags for key, tags in case_groups.items() if len(tags) > 1}
    for key, variants in case_variants.items():
        consolidation_suggestions.append({
            "type": "case_consolidation",
            "tags": variants,
            "suggestion": f"Consolidate to single case format"
        })
    
    return {
        "total_singletons": len(singletons),
        "categorized_singletons": {k: len(v) for k, v in categorized.items()},
        "detailed_categories": categorized,
        "consolidation_suggestions": consolidation_suggestions,
        "estimated_cleanup_impact": {
            "technical_artifacts": len(categorized["technical_artifacts"]),
            "format_consolidations": len(categorized["format_consolidation"]),
            "potential_removals": len(categorized["cleanup_candidates"])
        }
    }

@router.post("/api/tags/cleanup-placeholders")
async def cleanup_consolidation_artifacts(dry_run: bool = True):
    """Remove placeholder tags left by consolidation process"""
    
    PLACEHOLDER_REMOVALS = [
        "REMOVE_SYSTEM_REDUNDANT",
        "REMOVE_X_AXIS_REDUNDANT",
        "REMOVE_Y_AXIS_REDUNDANT",
        "REMOVE_Z_AXIS_REDUNDANT"
    ]
    
    files_processed = 0
    tags_removed = 0
    
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            if content.startswith("---"):
                yaml_data = parse_yaml_frontmatter(content)
                if yaml_data and 'tags' in yaml_data:
                    original_tags = yaml_data['tags']
                    if isinstance(original_tags, list):
                        # Remove placeholder tags completely
                        cleaned_tags = [tag for tag in original_tags if tag not in PLACEHOLDER_REMOVALS]
                        
                        if len(cleaned_tags) != len(original_tags):
                            yaml_data['tags'] = sorted(set(cleaned_tags))
                            tags_removed += len(original_tags) - len(cleaned_tags)
                            
                            if not dry_run:
                                lines = content.split('\n')
                                yaml_end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), -1)
                                if yaml_end > 0:
                                    new_yaml = generate_obsidian_yaml(yaml_data)
                                    updated_content = new_yaml + '\n' + '\n'.join(lines[yaml_end + 1:])
                                    md_file.write_text(updated_content, encoding="utf-8")
            
            files_processed += 1
            
        except Exception as e:
            print(f"Error processing {md_file}: {e}")
    
    return {
        "dry_run": dry_run,
        "files_processed": files_processed,
        "placeholder_tags_removed": tags_removed,
        "message": "Preview mode" if dry_run else "Placeholders cleaned successfully"
    }

@router.get("/api/tags/audit")
async def audit_tags():
    """Comprehensive tag analysis"""
    tag_counter = Counter()
    
    # Collect all tags from all files
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            tags = extract_all_tags(md_file)
            tag_counter.update(tags)
        except Exception as e:
            print(f"Error processing {md_file}: {e}")
    
    return {
        "total_tags": len(tag_counter),
        "total_instances": sum(tag_counter.values()),
        "top_50_tags": tag_counter.most_common(50),
        "unique_tags": list(tag_counter.keys())
    }

@router.post("/api/tesseract/extract-coordinates")
async def extract_tesseract_coordinates():
    """Map entire codex into 4D Tesseract coordinate system"""
    tesseract_map = {
        "x_structure_distribution": Counter(),
        "y_transmission_distribution": Counter(),
        "z_purpose_distribution": Counter(),
        "w_terrain_distribution": Counter(),
        "coordinate_combinations": {},
        "high_dimensional_clusters": {},
        "memoir_spine_candidates": []
    }
    
    processed_files = 0
    error_files = 0
    
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            file_path_str = str(md_file.relative_to(VAULT_PATH))
            
            # Extract 4D coordinates
            coordinates = extract_tesseract_position(content)
            tesseract_map["coordinate_combinations"][file_path_str] = coordinates
            
            # Update dimensional distributions
            tesseract_map["x_structure_distribution"][coordinates["x_structure"]] += 1
            tesseract_map["y_transmission_distribution"][coordinates["y_transmission"]] += 1
            tesseract_map["z_purpose_distribution"][coordinates["z_purpose"]] += 1
            tesseract_map["w_terrain_distribution"][coordinates["w_terrain"]] += 1
            
            # Identify memoir spine candidates (high Purpose + Narrative alignment)
            if coordinates["z_purpose"] in ["tell-story", "help-addict"] and coordinates["y_transmission"] == "narrative":
                memoir_priority = calculate_memoir_priority(coordinates, content)
                tesseract_map["memoir_spine_candidates"].append({
                    "file": file_path_str,
                    "coordinates": coordinates,
                    "memoir_priority": memoir_priority
                })
            
            processed_files += 1
            
            # Progress tracking
            if processed_files % 50 == 0:
                print(f"Processed {processed_files} files into 4D space...")
                
        except Exception as e:
            error_files += 1
            print(f"Error processing {md_file}: {e}")
    
    # Find high-dimensional clusters
    tesseract_map["high_dimensional_clusters"] = find_tesseract_clusters(tesseract_map)
    
    # Calculate 4D statistics
    total_coordinates = len(tesseract_map["coordinate_combinations"])
    unique_tesseract_keys = len(set(
        coords["tesseract_key"] for coords in tesseract_map["coordinate_combinations"].values()
    ))
    
    return {
        "tesseract_analysis_summary": {
            "total_files_mapped": processed_files,
            "processing_errors": error_files,
            "unique_4d_coordinates": unique_tesseract_keys,
            "coordinate_density": round(unique_tesseract_keys / total_coordinates, 3) if total_coordinates > 0 else 0
        },
        "dimensional_distributions": {
            "x_structure": dict(tesseract_map["x_structure_distribution"].most_common()),
            "y_transmission": dict(tesseract_map["y_transmission_distribution"].most_common()),
            "z_purpose": dict(tesseract_map["z_purpose_distribution"].most_common()),
            "w_terrain": dict(tesseract_map["w_terrain_distribution"].most_common())
        },
        "memoir_spine_analysis": {
            "total_candidates": len(tesseract_map["memoir_spine_candidates"]),
            "high_priority_spine": [
                candidate for candidate in tesseract_map["memoir_spine_candidates"]
                if candidate["memoir_priority"] > 0.7
            ][:20]
        },
        "4d_clusters": tesseract_map["high_dimensional_clusters"],
        "coordinate_combinations": tesseract_map["coordinate_combinations"],
        "tesseract_insights": [
            f"Most common structure: {tesseract_map['x_structure_distribution'].most_common(1)[0][0] if tesseract_map['x_structure_distribution'] else 'none'}",
            f"Primary transmission mode: {tesseract_map['y_transmission_distribution'].most_common(1)[0][0] if tesseract_map['y_transmission_distribution'] else 'none'}",
            f"Dominant life purpose: {tesseract_map['z_purpose_distribution'].most_common(1)[0][0] if tesseract_map['z_purpose_distribution'] else 'none'}",
            f"Most common cognitive terrain: {tesseract_map['w_terrain_distribution'].most_common(1)[0][0] if tesseract_map['w_terrain_distribution'] else 'none'}"
        ]
    }

@router.get("/api/tesseract/analyze-4d-structure")
async def analyze_tesseract_structure():
    """Analyze current folder structure through Tesseract lens"""
    tesseract_analysis = {
        "dimensional_coherence": {},
        "coordinate_clusters": {},
        "organizational_gaps": {},
        "memoir_readiness_by_purpose": {},
        "4d_reorganization_opportunities": []
    }
    
    # Get current tesseract mapping
    try:
        tesseract_map_result = await extract_tesseract_coordinates()
        tesseract_map = {
            "coordinate_combinations": tesseract_map_result["coordinate_combinations"],
            "z_purpose_distribution": Counter(tesseract_map_result["dimensional_distributions"]["z_purpose"]),
            "memoir_spine_candidates": tesseract_map_result["memoir_spine_analysis"]["high_priority_spine"]
        }
    except Exception as e:
        return {"error": f"Failed to extract Tesseract coordinates: {str(e)}"}
    
    processed_folders = 0
    
    for folder_path in VAULT_PATH.rglob("*"):
        if folder_path.is_dir() and not folder_path.name.startswith('.'):
            md_files = list(folder_path.glob("*.md"))
            if md_files:
                
                # Analyze 4D coherence within folder
                folder_coordinates = []
                for md_file in md_files:
                    file_key = str(md_file.relative_to(VAULT_PATH))
                    if file_key in tesseract_map["coordinate_combinations"]:
                        folder_coordinates.append(tesseract_map["coordinate_combinations"][file_key])
                
                coherence_score = calculate_4d_coherence(folder_coordinates)
                dominant_coordinates = find_dominant_4d_pattern(folder_coordinates)
                
                folder_key = str(folder_path.relative_to(VAULT_PATH))
                tesseract_analysis["dimensional_coherence"][folder_key] = {
                    "file_count": len(md_files),
                    "4d_coherence_score": coherence_score,
                    "dominant_pattern": dominant_coordinates,
                    "scatter_analysis": analyze_coordinate_scatter(folder_coordinates),
                    "reorganization_urgency": calculate_4d_urgency(coherence_score, len(md_files))
                }
                
                processed_folders += 1
    
    # Identify cross-dimensional clusters that should be grouped
    tesseract_analysis["coordinate_clusters"] = tesseract_map_result["4d_clusters"]
    
    # Find gaps in memoir structure
    tesseract_analysis["memoir_readiness_by_purpose"] = assess_memoir_completeness_by_purpose(tesseract_map)
    
    return {
        "analysis_summary": {
            "folders_analyzed": processed_folders,
            "avg_4d_coherence": calculate_avg_coherence(tesseract_analysis["dimensional_coherence"]),
            "high_coherence_folders": len([
                f for f in tesseract_analysis["dimensional_coherence"].values()
                if f["4d_coherence_score"] > 0.7
            ])
        },
        "tesseract_structure_analysis": tesseract_analysis,
        "reorganization_recommendations": generate_4d_reorganization_recommendations(tesseract_analysis)
    }

def find_dominant_4d_pattern(coordinates_list: list) -> dict:
    """Find the dominant coordinate pattern in a folder"""
    if not coordinates_list:
        return {}
    
    # Count occurrences of each dimension value
    structure_counter = Counter(coord["x_structure"] for coord in coordinates_list)
    transmission_counter = Counter(coord["y_transmission"] for coord in coordinates_list)
    purpose_counter = Counter(coord["z_purpose"] for coord in coordinates_list)
    terrain_counter = Counter(coord["w_terrain"] for coord in coordinates_list)
    
    return {
        "dominant_structure": structure_counter.most_common(1)[0][0] if structure_counter else "none",
        "dominant_transmission": transmission_counter.most_common(1)[0][0] if transmission_counter else "none",
        "dominant_purpose": purpose_counter.most_common(1)[0][0] if purpose_counter else "none",
        "dominant_terrain": terrain_counter.most_common(1)[0][0] if terrain_counter else "none",
        "pattern_strength": {
            "structure": structure_counter.most_common(1)[0][1] / len(coordinates_list) if structure_counter else 0,
            "transmission": transmission_counter.most_common(1)[0][1] / len(coordinates_list) if transmission_counter else 0,
            "purpose": purpose_counter.most_common(1)[0][1] / len(coordinates_list) if purpose_counter else 0,
            "terrain": terrain_counter.most_common(1)[0][1] / len(coordinates_list) if terrain_counter else 0
        }
    }

def analyze_coordinate_scatter(coordinates_list: list) -> dict:
    """Analyze how scattered coordinates are across 4D space"""
    if not coordinates_list:
        return {"scatter_score": 0, "analysis": "No coordinates to analyze"}
    
    total_files = len(coordinates_list)
    
    # Count unique values in each dimension
    unique_structures = len(set(coord["x_structure"] for coord in coordinates_list))
    unique_transmissions = len(set(coord["y_transmission"] for coord in coordinates_list))
    unique_purposes = len(set(coord["z_purpose"] for coord in coordinates_list))
    unique_terrains = len(set(coord["w_terrain"] for coord in coordinates_list))
    
    # Calculate scatter (higher = more scattered)
    scatter_score = (unique_structures + unique_transmissions + unique_purposes + unique_terrains) / (4 * total_files)
    
    return {
        "scatter_score": round(scatter_score, 3),
        "dimension_variety": {
            "structures": unique_structures,
            "transmissions": unique_transmissions,
            "purposes": unique_purposes,
            "terrains": unique_terrains
        },
        "scatter_assessment": (
            "highly_scattered" if scatter_score > 0.75 else
            "moderately_scattered" if scatter_score > 0.5 else
            "somewhat_coherent" if scatter_score > 0.25 else
            "highly_coherent"
        )
    }

def calculate_4d_urgency(coherence_score: float, file_count: int) -> float:
    """Calculate reorganization urgency based on 4D coherence and impact"""
    # Low coherence = high urgency
    coherence_urgency = 1.0 - coherence_score
    
    # More files = higher impact, thus higher urgency
    impact_urgency = min(1.0, file_count / 50)  # Normalize around 50 files
    
    # Combine factors
    overall_urgency = (coherence_urgency * 0.7) + (impact_urgency * 0.3)
    
    return round(overall_urgency, 3)

def assess_memoir_completeness_by_purpose(tesseract_map: dict) -> dict:
    """Assess memoir readiness across Rick's 5 core purposes"""
    purpose_analysis = {}
    
    for purpose in ["tell-story", "help-addict", "prevent-death-poverty", "financial-amends", "help-world"]:
        purpose_files = [
            file_path for file_path, coords in tesseract_map["coordinate_combinations"].items()
            if coords["z_purpose"] == purpose
        ]
        
        # Analyze transmission modes for this purpose
        transmission_counts = Counter()
        terrain_counts = Counter()
        
        for file_path in purpose_files:
            coords = tesseract_map["coordinate_combinations"][file_path]
            transmission_counts[coords["y_transmission"]] += 1
            terrain_counts[coords["w_terrain"]] += 1
        
        purpose_analysis[purpose] = {
            "total_files": len(purpose_files),
            "narrative_files": transmission_counts.get("narrative", 0),
            "transmission_diversity": len(transmission_counts),
            "cognitive_terrains": dict(terrain_counts),
            "memoir_readiness": calculate_purpose_memoir_readiness(purpose, transmission_counts, terrain_counts),
            "sample_files": purpose_files[:10]
        }
    
    return purpose_analysis

def calculate_purpose_memoir_readiness(purpose: str, transmission_counts: Counter, terrain_counts: Counter) -> dict:
    """Calculate memoir readiness for each life purpose"""
    narrative_count = transmission_counts.get("narrative", 0)
    total_files = sum(transmission_counts.values())
    
    # Different purposes have different memoir requirements
    purpose_weights = {
        "tell-story": {"narrative_importance": 0.8, "min_files": 20},
        "help-addict": {"narrative_importance": 0.6, "min_files": 15},
        "prevent-death-poverty": {"narrative_importance": 0.4, "min_files": 10},
        "financial-amends": {"narrative_importance": 0.3, "min_files": 5},
        "help-world": {"narrative_importance": 0.5, "min_files": 10}
    }
    
    weights = purpose_weights.get(purpose, {"narrative_importance": 0.5, "min_files": 10})
    
    # Calculate readiness score
    volume_score = min(1.0, total_files / weights["min_files"])
    narrative_ratio = narrative_count / total_files if total_files > 0 else 0
    narrative_score = narrative_ratio * weights["narrative_importance"]
    
    # Bonus for diverse cognitive terrains (shows depth)
    terrain_diversity = len(terrain_counts) / 5  # Max 5 terrain types
    
    overall_readiness = (volume_score + narrative_score + terrain_diversity * 0.2) / 2
    
    return {
        "readiness_score": round(overall_readiness, 3),
        "volume_score": round(volume_score, 3),
        "narrative_score": round(narrative_score, 3),
        "narrative_percentage": round(narrative_ratio * 100, 1),
        "recommendations": generate_purpose_recommendations(purpose, volume_score, narrative_score, terrain_counts)
    }

def generate_purpose_recommendations(purpose: str, volume_score: float, narrative_score: float, terrain_counts: Counter) -> list:
    """Generate specific recommendations for improving purpose-based memoir readiness"""
    recommendations = []
    
    if volume_score < 0.5:
        recommendations.append(f"Need more content for '{purpose}' - aim for more documents in this area")
    
    if narrative_score < 0.4:
        recommendations.append(f"Convert more '{purpose}' content to narrative format for memoir use")
    
    if len(terrain_counts) < 2:
        recommendations.append(f"Add emotional depth - explore '{purpose}' across different cognitive terrains")
    
    # Purpose-specific recommendations
    purpose_specific = {
        "tell-story": ["Focus on chronological narrative", "Add more personal details and memories"],
        "help-addict": ["Include specific recovery experiences", "Document sponsor relationships and meeting insights"],
        "prevent-death-poverty": ["Chronicle health challenges and housing struggles", "Document practical survival strategies"],
        "financial-amends": ["Detail work history and financial recovery", "Include specific amends and responsibility steps"],
        "help-world": ["Connect creative work to larger purpose", "Document how systems and tools help others"]
    }
    
    recommendations.extend(purpose_specific.get(purpose, []))
    
    return recommendations

def calculate_avg_coherence(dimensional_coherence: dict) -> float:
    """Calculate average 4D coherence across all folders"""
    if not dimensional_coherence:
        return 0.0
    
    coherence_scores = [folder["4d_coherence_score"] for folder in dimensional_coherence.values()]
    return round(sum(coherence_scores) / len(coherence_scores), 3)

def generate_4d_reorganization_recommendations(tesseract_analysis: dict) -> list:
    """Generate specific 4D reorganization recommendations"""
    recommendations = []
    
    # Analyze coherence issues
    low_coherence_folders = [
        (folder_name, folder_data) for folder_name, folder_data in tesseract_analysis["dimensional_coherence"].items()
        if folder_data["4d_coherence_score"] < 0.5 and folder_data["file_count"] > 5
    ]
    
    if low_coherence_folders:
        recommendations.append({
            "type": "coherence_improvement",
            "priority": "high",
            "description": f"Reorganize {len(low_coherence_folders)} folders with low 4D coherence",
            "affected_folders": [folder[0] for folder in low_coherence_folders[:10]],
            "impact": "Significantly improved findability and memoir structure"
        })
    
    # Analyze cluster opportunities
    significant_clusters = [
        cluster for cluster in tesseract_analysis["coordinate_clusters"].values()
        if len(cluster) > 10
    ]
    
    if significant_clusters:
        recommendations.append({
            "type": "cluster_consolidation",
            "priority": "medium",
            "description": f"Consolidate {len(significant_clusters)} major 4D clusters into coherent folders",
            "cluster_count": len(significant_clusters),
            "impact": "Natural groupings based on Tesseract coordinates"
        })
    
    # Memoir-specific recommendations
    memoir_readiness = tesseract_analysis.get("memoir_readiness_by_purpose", {})
    low_readiness_purposes = [
        purpose for purpose, data in memoir_readiness.items()
        if data.get("memoir_readiness", {}).get("readiness_score", 0) < 0.5
    ]
    
    if low_readiness_purposes:
        recommendations.append({
            "type": "memoir_development",
            "priority": "critical",
            "description": f"Develop memoir content for purposes: {', '.join(low_readiness_purposes)}",
            "purposes_needing_work": low_readiness_purposes,
            "impact": "Essential for memoir production readiness"
        })
    
    return recommendations

@router.post("/api/tesseract/suggest-reorganization")
async def suggest_tesseract_reorganization(
    focus_purpose: str = "all",  # tell-story, help-addict, prevent-death-poverty, financial-amends, help-world, all
    consolidation_threshold: int = 5,
    memoir_priority: bool = True
):
    """Generate 4D Tesseract-aware reorganization suggestions"""
    
    # Get current 4D analysis
    try:
        tesseract_structure_result = await analyze_tesseract_structure()
        tesseract_map_result = await extract_tesseract_coordinates()
        
        tesseract_structure = tesseract_structure_result["tesseract_structure_analysis"]
        tesseract_map = {
            "coordinate_combinations": tesseract_map_result["coordinate_combinations"],
            "z_purpose_distribution": Counter(tesseract_map_result["dimensional_distributions"]["z_purpose"]),
            "memoir_spine_candidates": tesseract_map_result["memoir_spine_analysis"]["high_priority_spine"]
        }
    except Exception as e:
        return {"error": f"Failed to analyze Tesseract structure: {str(e)}"}
    
    suggestions = []
    
    # Primary suggestion: Organize by Purpose + Structure (Z + X dimensions)
    purpose_structure_groups = defaultdict(list)
    for file_path, coords in tesseract_map["coordinate_combinations"].items():
        if focus_purpose == "all" or coords["z_purpose"] == focus_purpose:
            group_key = f"{coords['z_purpose']}/{coords['x_structure']}"
            purpose_structure_groups[group_key].append({
                "file": file_path,
                "coordinates": coords
            })
    
    # Generate suggestions for each significant group
    for group_key, files in purpose_structure_groups.items():
        if len(files) >= consolidation_threshold:
            purpose, structure = group_key.split('/')
            
            suggestions.append({
                "action": "create_tesseract_folder",
                "group_key": group_key,
                "purpose": purpose,
                "structure": structure,
                "total_files": len(files),
                "suggested_path": generate_tesseract_folder_path(purpose, structure),
                "memoir_relevance": assess_memoir_relevance(purpose, structure),
                "priority": calculate_tesseract_priority(purpose, structure, len(files), memoir_priority),
                "4d_coherence": calculate_group_coherence(files),
                "sample_files": [f["file"] for f in files[:5]]
            })
    
    # Special memoir spine suggestion
    memoir_spine = identify_memoir_spine_structure(tesseract_map)
    if memoir_spine:
        suggestions.append({
            "action": "create_memoir_spine",
            "structure": memoir_spine,
            "priority": "critical",
            "memoir_relevance": "essential - creates narrative backbone"
        })
    
    # Identify 4D orphans (files scattered across dimensions)
    orphaned_files = find_4d_orphans(tesseract_structure)
    if orphaned_files:
        suggestions.append({
            "action": "consolidate_4d_orphans",
            "total_orphaned": len(orphaned_files),
            "suggested_target_path": "_tesseract-inbox/needs-classification",
            "priority": "medium",
            "rationale": "Files scattered across 4D space need dimensional alignment"
        })
    
    return {
        "focus_purpose": focus_purpose,
        "tesseract_suggestions": suggestions,
        "4d_analysis_summary": {
            "total_coordinates": len(tesseract_map["coordinate_combinations"]),
            "purpose_distribution": dict(tesseract_map["z_purpose_distribution"]),
            "memoir_spine_candidates": len(tesseract_map["memoir_spine_candidates"])
        },
        "recommended_folder_structure": generate_tesseract_folder_structure(),
        "implementation_phases": [
            "Phase 1: Create memoir spine (tell-story + narrative)",
            "Phase 2: Consolidate recovery content (help-addict purpose)",
            "Phase 3: Organize by remaining purposes",
            "Phase 4: Fine-tune by cognitive terrain (W-dimension)"
        ]
    }

def assess_memoir_relevance(purpose: str, structure: str) -> str:
    """Assess memoir relevance based on Tesseract coordinates"""
    
    # Purpose-based memoir relevance
    purpose_relevance = {
        "tell-story": "critical",
        "help-addict": "high",
        "prevent-death-poverty": "medium",
        "financial-amends": "low",
        "help-world": "medium"
    }
    
    # Structure-based memoir relevance
    structure_relevance = {
        "archetype": "high",  # Character development
        "protocol": "medium", # Life systems
        "shadowcast": "high", # Emotional depth
        "expansion": "low",   # Background material
        "summoning": "medium" # Pivotal moments
    }
    
    base_relevance = purpose_relevance.get(purpose, "low")
    structure_modifier = structure_relevance.get(structure, "medium")
    
    # Combine ratings
    if base_relevance == "critical":
        return "critical"
    elif base_relevance == "high" or structure_modifier == "high":
        return "high"
    elif base_relevance == "medium" or structure_modifier == "medium":
        return "medium"
    else:
        return "low"

def calculate_tesseract_priority(purpose: str, structure: str, file_count: int, memoir_priority: bool) -> str:
    """Calculate reorganization priority using Tesseract coordinates"""
    
    base_score = 0
    
    # Purpose-based priority
    purpose_scores = {
        "tell-story": 5,
        "help-addict": 4,
        "prevent-death-poverty": 3,
        "financial-amends": 2,
        "help-world": 3
    }
    base_score += purpose_scores.get(purpose, 1)
    
    # Structure-based priority
    structure_scores = {
        "archetype": 3,
        "protocol": 2,
        "shadowcast": 3,
        "expansion": 1,
        "summoning": 2
    }
    base_score += structure_scores.get(structure, 1)
    
    # File count impact
    if file_count > 20:
        base_score += 2
    elif file_count > 10:
        base_score += 1
    
    # Memoir priority boost
    if memoir_priority and purpose in ["tell-story", "help-addict"]:
        base_score += 2
    
    # Convert to priority level
    if base_score >= 8:
        return "critical"
    elif base_score >= 6:
        return "high"
    elif base_score >= 4:
        return "medium"
    else:
        return "low"

def calculate_group_coherence(files: list) -> float:
    """Calculate coherence for a group of files with same coordinates"""
    if not files:
        return 0.0
    
    # Files in same coordinate group should have high coherence by definition
    # But we can measure consistency in related metadata
    
    coordinates_list = [f["coordinates"] for f in files]
    return calculate_4d_coherence(coordinates_list)

def identify_memoir_spine_structure(tesseract_map: dict) -> dict:
    """Identify the core memoir structure from Tesseract analysis"""
    
    spine_candidates = tesseract_map.get("memoir_spine_candidates", [])
    
    if len(spine_candidates) < 10:
        return None
    
    # Organize spine by cognitive terrain (W-dimension) for emotional flow
    terrain_organization = defaultdict(list)
    for candidate in spine_candidates:
        terrain = candidate["coordinates"]["w_terrain"]
        terrain_organization[terrain].append(candidate)
    
    # Suggested memoir spine structure
    return {
        "total_spine_files": len(spine_candidates),
        "suggested_structure": {
            "memoir/spine/foundations/": f"Complex terrain files ({len(terrain_organization.get('complex', []))} files)",
            "memoir/spine/crisis/": f"Chaotic terrain files ({len(terrain_organization.get('chaotic', []))} files)",
            "memoir/spine/recovery/": f"Complicated terrain files ({len(terrain_organization.get('complicated', []))} files)",
            "memoir/spine/integration/": f"Obvious terrain files ({len(terrain_organization.get('obvious', []))} files)",
            "memoir/spine/fragments/": f"Confused terrain files ({len(terrain_organization.get('confused', []))} files)"
        },
        "terrain_files": dict(terrain_organization),
        "emotional_flow_rationale": "Organized by cognitive terrain for natural memoir progression"
    }

def find_4d_orphans(tesseract_structure: dict) -> list:
    """Find files that are scattered across 4D space without clear groupings"""
    orphans = []
    
    # Look for folders with very low coherence and high scatter
    for folder_name, folder_data in tesseract_structure.get("dimensional_coherence", {}).items():
        if (folder_data["4d_coherence_score"] < 0.3 and
            folder_data.get("scatter_analysis", {}).get("scatter_score", 0) > 0.7):
            orphans.append({
                "folder": folder_name,
                "file_count": folder_data["file_count"],
                "coherence_issue": "high_scatter",
                "scatter_score": folder_data.get("scatter_analysis", {}).get("scatter_score", 0)
            })
    
    return orphans

def generate_tesseract_folder_structure() -> dict:
    """Generate complete Tesseract-native folder structure for Rick's codex"""
    return {
        "memoir/": {
            "description": "Tell My Story - Primary memoir content",
            "subfolders": {
                "spine/": "Core narrative backbone organized by cognitive terrain",
                "personas/": "Archetype-based character studies and identity work",
                "practices/": "Protocol-based recovery and life management routines",
                "explorations/": "Shadowcast emotional fragments and mood pieces",
                "context/": "Expansion background and supporting material"
            }
        },
        "recovery/": {
            "description": "Help Another Addict - AA and recovery focused content",
            "subfolders": {
                "practices/": "Step work, sponsor work, meeting protocols",
                "personas/": "Recovery archetypes (sponsor, sponsee, group member)",
                "explorations/": "Emotional recovery work, inventory, amends prep",
                "activations/": "Summoning recovery energy, centering practices"
            }
        },
        "survival/": {
            "description": "Prevent Death/Poverty - Medical, housing, practical life",
            "subfolders": {
                "medical/": "Mayo clinic, health management, treatment protocols",
                "housing/": "Sober house, homelessness preparation, practical survival",
                "systems/": "Benefits, insurance, practical life management"
            }
        },
        "work-amends/": {
            "description": "Financial Amends - Employment, income, responsibility",
            "subfolders": {
                "job-search/": "Employment seeking, interviews, opportunities",
                "skills/": "Technical abilities, creative work, professional development",
                "planning/": "Financial recovery, debt management, future planning"
            }
        },
        "contribution/": {
            "description": "Help the World - Creative work, systems, tools",
            "subfolders": {
                "creative/": "AI art, music, comedy, creative expression",
                "systems/": "Technical tools, APIs, helpful systems",
                "philosophy/": "Wisdom, insights, contributions to understanding"
            }
        },
        "_tesseract-meta/": {
            "description": "Tesseract system files and coordinate mappings",
            "subfolders": {
                "coordinates/": "4D mapping files and analysis",
                "inbox/": "New content awaiting coordinate assignment",
                "templates/": "Tesseract-aware document templates"
            }
        }
    }

@router.get("/api/tesseract/memoir-readiness")
async def assess_tesseract_memoir_readiness():
    """Comprehensive memoir readiness assessment using 4D Tesseract analysis"""
    
    try:
        tesseract_map_result = await extract_tesseract_coordinates()
        tesseract_structure_result = await analyze_tesseract_structure()
        
        tesseract_map = {
            "coordinate_combinations": tesseract_map_result["coordinate_combinations"],
            "x_structure_distribution": Counter(tesseract_map_result["dimensional_distributions"]["x_structure"]),
            "y_transmission_distribution": Counter(tesseract_map_result["dimensional_distributions"]["y_transmission"]),
            "w_terrain_distribution": Counter(tesseract_map_result["dimensional_distributions"]["w_terrain"]),
            "memoir_spine_candidates": tesseract_map_result["memoir_spine_analysis"]["high_priority_spine"]
        }
        
        tesseract_structure = tesseract_structure_result["tesseract_structure_analysis"]
        
    except Exception as e:
        return {"error": f"Failed to analyze Tesseract memoir readiness: {str(e)}"}
    
    # Core memoir analysis
    memoir_analysis = {
        "overall_4d_readiness": 0,
        "dimensional_scores": {},
        "narrative_spine_strength": 0,
        "purpose_coverage": {},
        "cognitive_terrain_balance": {},
        "production_recommendations": []
    }
    
    # X-Dimension Analysis: Structure readiness
    structure_dist = tesseract_map["x_structure_distribution"]
    memoir_analysis["dimensional_scores"]["x_structure"] = {
        "archetype_content": structure_dist.get("archetype", 0),
        "protocol_systems": structure_dist.get("protocol", 0),
        "shadowcast_depth": structure_dist.get("shadowcast", 0),
        "narrative_readiness": calculate_structure_memoir_readiness(structure_dist)
    }
    
    # Y-Dimension Analysis: Transmission readiness
    transmission_dist = tesseract_map["y_transmission_distribution"]
    memoir_analysis["dimensional_scores"]["y_transmission"] = {
        "narrative_content": transmission_dist.get("narrative", 0),
        "total_content": sum(transmission_dist.values()),
        "narrative_percentage": transmission_dist.get("narrative", 0) / max(sum(transmission_dist.values()), 1) * 100,
        "transmission_readiness": calculate_transmission_memoir_readiness(transmission_dist)
    }
    
    # Z-Dimension Analysis: Purpose coverage (Rick's 5 core intents)
    purpose_coverage = tesseract_structure.get("memoir_readiness_by_purpose", {})
    memoir_analysis["purpose_coverage"] = purpose_coverage
    
    # Calculate overall purpose readiness
    purpose_scores = [data.get("memoir_readiness", {}).get("readiness_score", 0) for data in purpose_coverage.values()]
    avg_purpose_readiness = sum(purpose_scores) / len(purpose_scores) if purpose_scores else 0
    
    # W-Dimension Analysis: Cognitive terrain balance
    terrain_dist = tesseract_map["w_terrain_distribution"]
    memoir_analysis["cognitive_terrain_balance"] = {
        "terrain_distribution": dict(terrain_dist),
        "emotional_range": len(terrain_dist),  # More terrains = richer emotional content
        "chaos_integration": terrain_dist.get("chaotic", 0),  # Important for trauma memoir
        "complexity_depth": terrain_dist.get("complex", 0),   # Shows thoughtful processing
        "terrain_readiness": calculate_terrain_memoir_readiness(terrain_dist)
    }
    
    # Narrative spine analysis
    spine_candidates = tesseract_map["memoir_spine_candidates"]
    spine_strength = len([c for c in spine_candidates if c.get("memoir_priority", 0) > 0.6])
    memoir_analysis["narrative_spine_strength"] = spine_strength / max(len(spine_candidates), 1) if spine_candidates else 0
    
    # Calculate overall 4D readiness
    structure_score = memoir_analysis["dimensional_scores"]["x_structure"]["narrative_readiness"]
    transmission_score = memoir_analysis["dimensional_scores"]["y_transmission"]["transmission_readiness"]
    purpose_score = avg_purpose_readiness
    terrain_score = memoir_analysis["cognitive_terrain_balance"]["terrain_readiness"]
    spine_score = memoir_analysis["narrative_spine_strength"]
    
    # Weighted overall score (purpose and spine most important)
    memoir_analysis["overall_4d_readiness"] = (
        structure_score * 0.15 +
        transmission_score * 0.20 +
        purpose_score * 0.30 +
        terrain_score * 0.15 +
        spine_score * 0.20
    )
    
    return {
        "tesseract_memoir_analysis": memoir_analysis,
        "readiness_category": categorize_memoir_readiness(memoir_analysis["overall_4d_readiness"]),
        "estimated_completion_timeline": estimate_memoir_timeline(memoir_analysis),
        "4d_advantages": [
            "Tesseract coordinates provide multidimensional narrative structure",
            "Purpose-driven organization ensures meaningful content flow",
            "Cognitive terrain mapping enables emotional authenticity",
            "4D clustering reveals natural chapter boundaries"
        ]
    }

def calculate_structure_memoir_readiness(structure_dist: Counter) -> float:
    """Calculate memoir readiness based on X-dimension structure distribution"""
    total_structures = sum(structure_dist.values())
    if total_structures == 0:
        return 0.0
    
    # Weight different structures for memoir value
    structure_weights = {
        "archetype": 0.3,  # High value for character development
        "protocol": 0.2,  # Medium value for life systems
        "shadowcast": 0.3, # High value for emotional depth
        "expansion": 0.1,  # Lower value for background material
        "summoning": 0.25  # Good value for pivotal moments
    }
    
    weighted_score = 0.0
    for structure, count in structure_dist.items():
        weight = structure_weights.get(structure, 0.15)
        weighted_score += (count / total_structures) * weight
    
    return round(weighted_score, 3)

def calculate_transmission_memoir_readiness(transmission_dist: Counter) -> float:
    """Calculate memoir readiness based on Y-dimension transmission distribution"""
    total_transmissions = sum(transmission_dist.values())
    if total_transmissions == 0:
        return 0.0
    
    # Narrative content is most important for memoir
    narrative_ratio = transmission_dist.get("narrative", 0) / total_transmissions
    
    # Other transmission modes provide supporting value
    text_ratio = transmission_dist.get("text", 0) / total_transmissions
    
    # Calculate readiness (narrative most important)
    readiness = (narrative_ratio * 0.8) + (text_ratio * 0.2)
    
    return round(readiness, 3)

def calculate_terrain_memoir_readiness(terrain_dist: Counter) -> float:
    """Calculate memoir readiness based on W-dimension cognitive terrain balance"""
    total_terrain = sum(terrain_dist.values())
    if total_terrain == 0:
        return 0.0
    
    # Memoir benefits from emotional range across terrains
    terrain_diversity = len(terrain_dist) / 5  # Max 5 terrain types
    
    # Some terrains are more valuable for memoir
    terrain_weights = {
        "chaotic": 0.25,    # Essential for trauma memoir authenticity
        "complex": 0.3,     # Shows depth and processing
        "complicated": 0.2, # Good for technical/system content
        "confused": 0.15,   # Authentic but needs balance
        "obvious": 0.1      # Simple content, less memoir value
    }
    
    weighted_score = 0.0
    for terrain, count in terrain_dist.items():
        weight = terrain_weights.get(terrain, 0.15)
        weighted_score += (count / total_terrain) * weight
    
    # Combine weighted content with diversity bonus
    readiness = (weighted_score * 0.7) + (terrain_diversity * 0.3)
    
    return round(readiness, 3)

def categorize_memoir_readiness(overall_score: float) -> dict:
    """Categorize memoir readiness with specific guidance"""
    if overall_score >= 0.85:
        return {
            "category": "publication_ready",
            "description": "Memoir structure solid, content rich, ready for final editing",
            "confidence": "high"
        }
    elif overall_score >= 0.70:
        return {
            "category": "draft_complete",
            "description": "Strong foundation, needs content development and organization",
            "confidence": "medium-high"
        }
    elif overall_score >= 0.50:
        return {
            "category": "foundation_strong",
            "description": "Good 4D structure, needs more narrative content",
            "confidence": "medium"
        }
    else:
        return {
            "category": "development_phase",
            "description": "Early stage, focus on building content and structure",
            "confidence": "developing"
        }

def estimate_memoir_timeline(memoir_analysis: dict) -> dict:
    """Estimate timeline to memoir completion based on 4D analysis"""
    readiness_score = memoir_analysis["overall_4d_readiness"]
    spine_strength = memoir_analysis["narrative_spine_strength"]
    
    # Base timeline estimates (in months)
    if readiness_score >= 0.85:
        base_months = 2  # Just editing and refinement
    elif readiness_score >= 0.70:
        base_months = 6  # Content development and organization
    elif readiness_score >= 0.50:
        base_months = 12 # Building narrative content
    else:
        base_months = 18 # Fundamental development needed
    
    # Adjust based on spine strength
    if spine_strength > 0.8:
        spine_adjustment = -2  # Strong spine accelerates
    elif spine_strength > 0.5:
        spine_adjustment = 0   # Average spine
    else:
        spine_adjustment = 3   # Weak spine adds time
    
    estimated_months = max(1, base_months + spine_adjustment)
    
    return {
        "estimated_months": estimated_months,
        "estimated_range": f"{estimated_months-1}-{estimated_months+2} months",
        "key_factors": [
            f"Current 4D readiness: {round(readiness_score * 100, 1)}%",
            f"Narrative spine strength: {round(spine_strength * 100, 1)}%",
            "Timeline assumes consistent work on memoir development"
        ]
    }# Add these new imports to the existing routes.py
from app.utils import (
    # Existing imports...
    validate_markdown, write_markdown_file, parse_yaml_frontmatter,
    fix_yaml_frontmatter, generate_obsidian_yaml, apply_tag_consolidation,
    extract_all_tags, analyze_consolidation_opportunities, create_backup_snapshot,
    CRITICAL_CONSOLIDATIONS,
    
    # NEW: Content intelligence functions
    identify_document_archetype, extract_content_signature, count_internal_references,
    analyze_folder_content_types, measure_tag_coherence, extract_naming_patterns,
    calculate_urgency_score, group_by_archetype, generate_folder_path,
    calculate_priority, find_orphaned_files, chunked
)

# ============================================================================
# NEW: PHASE 2 CONTENT INTELLIGENCE ENDPOINTS
# ============================================================================

@router.post("/api/analysis/content-fingerprint")
async def analyze_content_patterns():
    """Create content fingerprints to understand document types and patterns"""
    patterns = {
        "document_types": Counter(),
        "content_signatures": {},
        "structural_patterns": {},
        "cross_reference_density": {},
        "narrative_markers": Counter()
    }
    
    processed_files = 0
    error_files = 0
    
    # Sample analysis for initial understanding (process all files but track progress)
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            file_path_str = str(md_file.relative_to(VAULT_PATH))
            
            # Identify document archetypes
            archetype = identify_document_archetype(content)
            patterns["document_types"][archetype] += 1
            
            # Extract structural signatures
            signature = extract_content_signature(content)
            patterns["content_signatures"][file_path_str] = signature
            
            # Measure cross-reference density
            ref_density = count_internal_references(content)
            patterns["cross_reference_density"][file_path_str] = ref_density
            
            processed_files += 1
            
            # Progress tracking for large vaults
            if processed_files % 100 == 0:
                print(f"Processed {processed_files} files...")
                
        except Exception as e:
            error_files += 1
            print(f"Error processing {md_file}: {e}")
    
    # Calculate aggregate metrics
    total_words = sum(sig.get("word_count", 0) for sig in patterns["content_signatures"].values())
    avg_cross_refs = sum(patterns["cross_reference_density"].values()) / len(patterns["cross_reference_density"]) if patterns["cross_reference_density"] else 0
    
    # Identify most connected documents (high cross-reference density)
    top_connected = sorted(
        patterns["cross_reference_density"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:20]
    
    return {
        "analysis_summary": {
            "total_files_processed": processed_files,
            "processing_errors": error_files,
            "total_word_count": total_words,
            "avg_cross_references": round(avg_cross_refs, 2)
        },
        "document_archetypes": dict(patterns["document_types"].most_common()),
        "top_connected_documents": top_connected,
        "content_patterns": {
            "high_emotional_intensity": [
                path for path, sig in patterns["content_signatures"].items()
                if sig.get("emotional_intensity", 0) > 5
            ][:20],
            "memoir_candidates": [
                path for path, sig in patterns["content_signatures"].items()
                if sig.get("temporal_markers", {}).get("childhood_markers", 0) > 0 or
                   sig.get("personal_pronouns", {}).get("first_person", 0) > 10
            ][:20],
            "recovery_focus": [
                path for path in patterns["content_signatures"].keys()
                if identify_document_archetype(
                    VAULT_PATH.joinpath(path).read_text(encoding="utf-8")
                ) == "recovery-document"
            ][:20]
        },
        "structural_insights": {
            "files_with_yaml": sum(1 for sig in patterns["content_signatures"].values() if sig.get("has_yaml", False)),
            "files_with_code": sum(1 for sig in patterns["content_signatures"].values() if sig.get("has_code_blocks", False)),
            "highly_linked_content": len([d for d in patterns["cross_reference_density"].values() if d > 5])
        }
    }

@router.get("/api/analysis/folder-chaos")
async def analyze_folder_structure():
    """Analyze current folder structure for reorganization opportunities"""
    folder_analysis = {}
    processed_folders = 0
    
    for folder_path in VAULT_PATH.rglob("*"):
        if folder_path.is_dir() and not folder_path.name.startswith('.'):
            md_files = list(folder_path.glob("*.md"))
            if md_files:
                try:
                    # Analyze folder contents
                    content_types = analyze_folder_content_types(md_files)
                    tag_coherence = measure_tag_coherence(md_files)
                    naming_patterns = extract_naming_patterns(md_files)
                    
                    folder_key = str(folder_path.relative_to(VAULT_PATH))
                    folder_analysis[folder_key] = {
                        "file_count": len(md_files),
                        "content_types": content_types,
                        "tag_coherence_score": round(tag_coherence, 3),
                        "naming_patterns": naming_patterns,
                        "reorganization_urgency": round(
                            calculate_urgency_score(content_types, tag_coherence), 3
                        ),
                        "path_depth": len(folder_path.relative_to(VAULT_PATH).parts)
                    }
                    processed_folders += 1
                    
                except Exception as e:
                    print(f"Error analyzing folder {folder_path}: {e}")
    
    # Sort by urgency and identify chaos hotspots
    chaos_hotspots = sorted(
        folder_analysis.items(),
        key=lambda x: x[1]["reorganization_urgency"],
        reverse=True
    )[:20]
    
    # Generate structure suggestions
    structure_suggestions = generate_structure_suggestions(folder_analysis)
    
    return {
        "analysis_summary": {
            "total_folders_analyzed": processed_folders,
            "folders_with_files": len(folder_analysis),
            "avg_files_per_folder": sum(f["file_count"] for f in folder_analysis.values()) / len(folder_analysis) if folder_analysis else 0
        },
        "chaos_hotspots": chaos_hotspots,
        "structural_issues": {
            "deep_nested_folders": [
                folder for folder, analysis in folder_analysis.items()
                if analysis["path_depth"] > 4
            ],
            "singleton_folders": [
                folder for folder, analysis in folder_analysis.items()
                if analysis["file_count"] == 1
            ][:10],
            "mixed_content_folders": [
                folder for folder, analysis in folder_analysis.items()
                if analysis["content_types"]["type_diversity"] > 0.7
            ][:10]
        },
        "suggested_structure": structure_suggestions,
        "reorganization_impact": calculate_reorganization_impact(folder_analysis)
    }

def generate_structure_suggestions(folder_analysis: dict) -> dict:
    """Generate intelligent folder structure suggestions"""
    suggestions = {
        "consolidation_opportunities": [],
        "new_structure_proposal": {},
        "quick_wins": []
    }
    
    # Identify folders that could be consolidated
    content_type_groups = defaultdict(list)
    for folder, analysis in folder_analysis.items():
        dominant_type = analysis["content_types"]["dominant_type"]
        if dominant_type != "unknown":
            content_type_groups[dominant_type].append({
                "folder": folder,
                "file_count": analysis["file_count"],
                "urgency": analysis["reorganization_urgency"]
            })
    
    # Suggest consolidations for types with multiple folders
    for content_type, folders in content_type_groups.items():
        if len(folders) > 2:  # Multiple folders with same content type
            total_files = sum(f["file_count"] for f in folders)
            suggestions["consolidation_opportunities"].append({
                "content_type": content_type,
                "current_folders": [f["folder"] for f in folders],
                "total_files": total_files,
                "suggested_target": generate_folder_path(content_type),
                "priority": "high" if total_files > 20 else "medium"
            })
    
    # Propose new top-level structure based on Rick's content
    suggestions["new_structure_proposal"] = {
        "memoir/": "Personal narratives, memories, life stories",
        "recovery/": "AA, sobriety, addiction recovery documents",
        "health/": "Medical, therapy, mental health records",
        "creative/": "AI art, music, comedy, creative projects",
        "systems/": "Technical documentation, API, tools",
        "philosophy/": "Reflections, spiritual, existential content",
        "life/": "Daily life, practical matters, housing, etc",
        "_archive/": "Old versions, deprecated content",
        "_inbox/": "New, unsorted content"
    }
    
    # Quick wins - easy reorganizations
    for folder, analysis in folder_analysis.items():
        if (analysis["reorganization_urgency"] > 0.8 and
            analysis["file_count"] < 10 and
            analysis["content_types"]["type_diversity"] < 0.3):
            suggestions["quick_wins"].append({
                "folder": folder,
                "target": generate_folder_path(analysis["content_types"]["dominant_type"]),
                "file_count": analysis["file_count"],
                "rationale": "High urgency, low file count, coherent content type"
            })
    
    return suggestions

def calculate_reorganization_impact(folder_analysis: dict) -> dict:
    """Calculate potential impact of reorganization"""
    total_files = sum(f["file_count"] for f in folder_analysis.values())
    high_urgency_files = sum(
        f["file_count"] for f in folder_analysis.values()
        if f["reorganization_urgency"] > 0.7
    )
    
    return {
        "total_files_affected": total_files,
        "high_priority_files": high_urgency_files,
        "estimated_improvement": f"{round((high_urgency_files / total_files) * 100, 1)}% of files would benefit",
        "reorganization_complexity": "high" if total_files > 500 else "medium" if total_files > 100 else "low"
    }

@router.post("/api/reorganize/suggest")
async def suggest_reorganization(
    focus_area: str = "all",  # memoir, recovery, creative, medical, technical, all
    consolidation_threshold: int = 5,
    max_suggestions: int = 20
):
    """Generate intelligent folder reorganization suggestions"""
    
    # Get current analysis
    content_analysis = await analyze_content_patterns()
    folder_analysis = await analyze_folder_structure()
    
    suggestions = []
    
    # Group documents by content archetype
    document_types = content_analysis["document_archetypes"]
    
    # Filter by focus area if specified
    if focus_area != "all":
        focus_mappings = {
            "memoir": ["memoir-narrative"],
            "recovery": ["recovery-document"],
            "creative": ["creative-work"],
            "medical": ["medical-health"],
            "technical": ["technical-system"]
        }
        target_types = focus_mappings.get(focus_area, [focus_area])
    else:
        target_types = list(document_types.keys())
    
    # Generate consolidation suggestions for each archetype
    for archetype in target_types:
        file_count = document_types.get(archetype, 0)
        if file_count >= consolidation_threshold:
            
            # Find current folders containing this archetype
            current_locations = []
            for folder_path, folder_data in folder_analysis["chaos_hotspots"]:
                dominant_type = folder_data["content_types"]["dominant_type"]
                if dominant_type == archetype:
                    current_locations.append({
                        "folder": folder_path,
                        "file_count": folder_data["file_count"],
                        "urgency": folder_data["reorganization_urgency"]
                    })
            
            suggestions.append({
                "action": "consolidate_by_archetype",
                "archetype": archetype,
                "total_files": file_count,
                "current_scattered_locations": len(current_locations),
                "current_locations_sample": current_locations[:5],
                "suggested_target_path": generate_folder_path(archetype),
                "priority": calculate_priority(archetype, file_count),
                "estimated_time_savings": f"{file_count * 0.5:.1f} minutes per search",
                "memoir_relevance": get_memoir_relevance(archetype)
            })
    
    # Identify orphaned and deeply nested files
    orphaned_files = []
    for folder_path, folder_data in folder_analysis["chaos_hotspots"]:
        if (folder_data["path_depth"] > 4 and
            folder_data["file_count"] < 3):
            orphaned_files.extend([{
                "current_path": folder_path,
                "file_count": folder_data["file_count"],
                "suggested_target": "_inbox/needs-review",
                "reason": "deeply_nested_singleton"
            }])
    
    if orphaned_files:
        suggestions.append({
            "action": "rescue_orphaned_files",
            "total_orphaned": len(orphaned_files),
            "sample_locations": orphaned_files[:10],
            "suggested_target_path": "_inbox/needs-review",
            "priority": "medium",
            "rationale": "Files buried in deep folder structures are hard to find"
        })
    
    # Special memoir-focused suggestions
    if focus_area in ["all", "memoir"]:
        memoir_suggestions = generate_memoir_structure_suggestions(content_analysis)
        suggestions.extend(memoir_suggestions)
    
    # Limit results
    suggestions = suggestions[:max_suggestions]
    
    return {
        "focus_area": focus_area,
        "total_suggestions": len(suggestions),
        "high_priority_count": len([s for s in suggestions if s.get("priority") == "high"]),
        "suggestions": suggestions,
        "estimated_total_impact": calculate_suggestion_impact(suggestions),
        "next_steps": [
            "Review suggestions and select highest priority items",
            "Create backup before executing any moves",
            "Start with quick wins (small file counts, clear benefits)",
            "Execute in batches to allow for review and adjustment"
        ]
    }

def get_memoir_relevance(archetype: str) -> str:
    """Assess how relevant an archetype is to memoir writing"""
    memoir_relevance = {
        "memoir-narrative": "critical - primary memoir content",
        "recovery-document": "critical - central to your story",
        "medical-health": "high - important life context",
        "practical-life": "medium - daily life details",
        "philosophical-reflection": "medium - provides depth and insight",
        "creative-work": "low - supplementary creative expression",
        "technical-system": "low - behind-the-scenes infrastructure"
    }
    return memoir_relevance.get(archetype, "unknown")

def generate_memoir_structure_suggestions(content_analysis: dict) -> list:
    """Generate specific suggestions for memoir organization"""
    memoir_suggestions = []
    
    # Look for chronological organization opportunities
    temporal_files = []
    for file_path, signature in content_analysis.get("content_patterns", {}).get("memoir_candidates", []):
        if signature and "temporal_markers" in signature:
            temporal_files.append(file_path)
    
    if len(temporal_files) > 10:
        memoir_suggestions.append({
            "action": "create_chronological_memoir_structure",
            "archetype": "memoir-organization",
            "total_files": len(temporal_files),
            "suggested_structure": {
                "memoir/childhood/": "Early life, family, formative experiences",
                "memoir/addiction/": "Descent into addiction, dark times",
                "memoir/rock-bottom/": "Crisis points, consequences",
                "memoir/recovery/": "Getting sober, AA journey",
                "memoir/health-crisis/": "Cirrhosis diagnosis, Mayo treatment",
                "memoir/present/": "Current life, reflections, hope"
            },
            "priority": "critical",
            "memoir_relevance": "critical - creates narrative backbone for book",
            "rationale": "Chronological organization essential for memoir readability"
        })
    
    return memoir_suggestions

def calculate_suggestion_impact(suggestions: list) -> dict:
    """Calculate estimated impact of implementing suggestions"""
    total_files = sum(s.get("total_files", 0) for s in suggestions)
    high_priority = len([s for s in suggestions if s.get("priority") == "high"])
    
    # Estimate time savings
    search_time_savings = sum(
        float(s.get("estimated_time_savings", "0 minutes").split()[0])
        for s in suggestions if "estimated_time_savings" in s
    )
    
    return {
        "files_to_be_reorganized": total_files,
        "high_priority_actions": high_priority,
        "estimated_weekly_time_savings": f"{search_time_savings:.1f} minutes",
        "memoir_production_readiness": "significantly improved" if high_priority > 2 else "moderately improved"
    }

@router.post("/api/reorganize/execute")
async def execute_reorganization(
    suggestion_id: int,  # Which suggestion to execute
    batch_size: int = 25,
    dry_run: bool = True,
    create_backup: bool = True
):
    """Execute a specific reorganization suggestion in safe batches"""
    
    if create_backup and not dry_run:
        print("Creating backup before reorganization...")
        backup_path = create_backup_snapshot(VAULT_PATH)
        print(f"Backup created at: {backup_path}")
    else:
        backup_path = None
    
    # For this implementation, we'll work with a simple move plan
    # In production, you'd load the specific suggestion and create detailed move plans
    
    results = []
    total_moves = 0
    successful_moves = 0
    errors = []
    
    # This is a simplified version - would need suggestion storage/retrieval
    example_moves = [
        {"source": "old/path/file1.md", "target": "memoir/childhood/", "archetype": "memoir-narrative"},
        {"source": "scattered/file2.md", "target": "recovery/documents/", "archetype": "recovery-document"}
    ]
    
    try:
        for batch_num, batch in enumerate(chunked(example_moves, batch_size), 1):
            batch_results = []
            
            print(f"Processing batch {batch_num} ({len(batch)} files)...")
            
            for move in batch:
                try:
                    source_path = VAULT_PATH / move["source"]
                    target_dir = VAULT_PATH / move["target"]
                    
                    if not source_path.exists():
                        batch_results.append({
                            "file": move["source"],
                            "status": "error",
                            "error": "Source file not found"
                        })
                        continue
                    
                    if not dry_run:
                        # Create target directory
                        target_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Move file
                        target_path = target_dir / source_path.name
                        source_path.rename(target_path)
                        
                        status = "moved"
                        successful_moves += 1
                    else:
                        status = "planned"
                    
                    batch_results.append({
                        "file": move["source"],
                        "target": move["target"],
                        "archetype": move.get("archetype", "unknown"),
                        "status": status
                    })
                    
                    total_moves += 1
                    
                except Exception as e:
                    error_msg = str(e)
                    errors.append(f"Error moving {move['source']}: {error_msg}")
                    batch_results.append({
                        "file": move["source"],
                        "status": "error",
                        "error": error_msg
                    })
            
            results.extend(batch_results)
            
            # Safety pause between batches (only in real execution)
            if not dry_run and batch_num < len(list(chunked(example_moves, batch_size))):
                time.sleep(2)
                
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "backup_path": str(backup_path) if backup_path else None
        }
    
    return {
        "status": "completed" if not errors else "completed_with_errors",
        "dry_run": dry_run,
        "backup_created": backup_path is not None,
        "backup_path": str(backup_path) if backup_path else None,
        "execution_summary": {
            "total_planned_moves": len(example_moves),
            "batches_processed": len(list(chunked(example_moves, batch_size))),
            "successful_moves": successful_moves,
            "total_errors": len(errors)
        },
        "results": results,
        "errors": errors,
        "recommendations": [
            "Review moved files to ensure they're in correct locations",
            "Update any internal links that may have broken",
            "Run tag audit to identify any cleanup needed after moves",
            "Consider creating index files for new folder structure"
        ]
    }

@router.get("/api/analysis/memoir-readiness")
async def assess_memoir_readiness():
    """Assess how ready the codex is for memoir production"""
    
    # Get content analysis
    content_patterns = await analyze_content_patterns()
    folder_structure = await analyze_folder_structure()
    
    # Analyze memoir-specific readiness factors
    memoir_files = []
    recovery_files = []
    chronological_files = []
    
    for archetype, count in content_patterns["document_archetypes"].items():
        if archetype == "memoir-narrative":
            memoir_files.append(count)
        elif archetype == "recovery-document":
            recovery_files.append(count)
    
    # Check for chronological markers
    temporal_content = len(content_patterns.get("content_patterns", {}).get("memoir_candidates", []))
    
    # Assess organization quality
    avg_urgency = sum(
        folder["reorganization_urgency"]
        for _, folder in folder_structure["chaos_hotspots"]
    ) / len(folder_structure["chaos_hotspots"]) if folder_structure["chaos_hotspots"] else 0
    
    # Calculate readiness scores
    content_score = min(100, (sum(memoir_files) + sum(recovery_files)) * 2)  # More content = better
    organization_score = max(0, 100 - (avg_urgency * 100))  # Less chaos = better
    temporal_score = min(100, temporal_content * 5)  # More chronological markers = better
    
    overall_readiness = (content_score + organization_score + temporal_score) / 3
    
    # Generate specific recommendations
    recommendations = []
    if content_score < 50:
        recommendations.append("Continue documenting key life events and memories")
    if organization_score < 70:
        recommendations.append("Prioritize folder reorganization to group related content")
    if temporal_score < 60:
        recommendations.append("Add more chronological context to existing documents")
    
    # Identify memoir structure gaps
    expected_chapters = [
        "early-life", "family-background", "addiction-onset", "spiral-downward",
        "rock-bottom", "recovery-beginning", "aa-journey", "health-crisis",
        "present-day", "future-hopes"
    ]
    
    missing_chapters = []
    for chapter in expected_chapters:
        # Simple check - would need more sophisticated content analysis
        chapter_content = sum(1 for file_type in content_patterns["document_archetypes"].keys()
                             if chapter.replace("-", " ") in file_type.lower())
        if chapter_content == 0:
            missing_chapters.append(chapter)
    
    return {
        "overall_readiness_score": round(overall_readiness, 1),
        "readiness_category": (
            "publication_ready" if overall_readiness >= 85 else
            "revision_ready" if overall_readiness >= 70 else
            "draft_ready" if overall_readiness >= 50 else
            "foundation_building"
        ),
        "component_scores": {
            "content_volume": round(content_score, 1),
            "organization_quality": round(organization_score, 1),
            "chronological_structure": round(temporal_score, 1)
        },
        "content_inventory": {
            "memoir_documents": sum(memoir_files),
            "recovery_documents": sum(recovery_files),
            "total_relevant_files": sum(memoir_files) + sum(recovery_files),
            "files_with_temporal_markers": temporal_content
        },
        "structural_assessment": {
            "folders_needing_reorganization": len([
                folder for _, folder in folder_structure["chaos_hotspots"]
                if folder["reorganization_urgency"] > 0.7
            ]),
            "average_organization_urgency": round(avg_urgency, 3)
        },
        "missing_content_areas": missing_chapters,
        "recommendations": recommendations,
        "next_steps": [
            "Focus on highest readiness score improvements first",
            "Use reorganization suggestions to improve structure",
            "Identify and fill content gaps in missing chapters",
            "Consider creating timeline documents for chronological flow"
        ]
    }
