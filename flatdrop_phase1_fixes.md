# Phase 1: Critical Obsidian Compatibility & Tag Consolidation

## URGENT: Fix YAML Format for Obsidian 1.4+

### Current Problem in `utils.py`
```python
# BROKEN - Creates single-line arrays that Obsidian ignores
parsed['tags'] = sorted(set(fixed_tags))
# Output: tags: [tag1, tag2, tag3]
```

### Required Fix
```python
def generate_obsidian_yaml(parsed_data):
    """Generate Obsidian 1.4+ compatible YAML"""
    yaml_lines = ["---"]
    
    # Handle tags as multi-line array (REQUIRED for Obsidian)
    if 'tags' in parsed_data and parsed_data['tags']:
        yaml_lines.append("tags:")
        for tag in sorted(set(parsed_data['tags'])):
            yaml_lines.append(f"  - {tag}")
    else:
        yaml_lines.append("tags: []")
    
    # Handle aliases as multi-line array
    if 'aliases' in parsed_data and parsed_data['aliases']:
        yaml_lines.append("aliases:")
        for alias in parsed_data['aliases']:
            yaml_lines.append(f"  - \"{alias}\"")
    else:
        yaml_lines.append("aliases: []")
    
    # Add other properties
    for key, value in parsed_data.items():
        if key not in ['tags', 'aliases']:
            if isinstance(value, str):
                yaml_lines.append(f"{key}: \"{value}\"")
            else:
                yaml_lines.append(f"{key}: {value}")
    
    yaml_lines.append("---")
    return "\n".join(yaml_lines)
```

## Critical Tag Consolidation Mappings

Based on your audit data, these are the highest-impact consolidations:

### 1. Core Tag Standardization
```python
CRITICAL_CONSOLIDATIONS = {
    # Flatline variations (3,383+ instances)
    "flatline-codex": "flatline",
    "flatline-dashboard": "flatline-dashboard", # Keep this one
    "FLATLINE": "flatline",
    "#flatline": "flatline",
    
    # Archetype standardization (1,900+ instances)
    "archetypes": "archetype",
    "#archetypes": "archetype",
    
    # Protocol standardization (1,900+ instances) 
    "protocols": "protocol",
    "#protocols": "protocol",
    
    # Remove hash prefixes universally
    "#summonings": "summonings",
    "#tnos": "tnos",
    "#narrative": "narrative",
    "#ritual": "ritual",
    
    # Case normalization for color codes
    "colors/0A0A23": "colors-0a0a23",
    "0A0A23": "0a0a23",
    "B9F5D8": "b9f5d8",
    "8A91C5": "8a91c5",
    
    # Consolidate memoir variations
    "memoir-buffer": "memoir",
    "memoir-as-resistance": "memoir",
    "memoir-splinter": "memoir",
    
    # Recovery theme consolidation
    "recovery-arcs": "recovery",
    "recovery-philosophy": "recovery",
    "recovery-narrative": "recovery",
    
    # Survivor theme consolidation  
    "survivor-myth": "survivor",
    "survivor-redaction": "survivor",
    "survivor-document": "survivor",
    "survivor-record": "survivor",
}
```

### 2. Path-like Tag Cleanup
```python
PATH_TAG_CONSOLIDATIONS = {
    # Flatten nested paths
    "flatline-codex/draw-things": "draw-things",
    "flatline-codex/draw-things/notes/liuliu-js-api": "liuliu-api",
    "protocols/chaos-gen": "chaos-gen",
    "dispatches/dispatches-002": "dispatches-002",
    "archetypes/poisonous-friend": "archetype-poisonous-friend",
    "summonings/burnt-bridge": "summoning-burnt-bridge",
    "rituals/block-and-release": "ritual-block-release",
}
```

## New API Endpoints for Tag Management

### Immediate Priority Endpoints

#### 1. Tag Consolidation
```python
@router.post("/api/tags/consolidate")
async def consolidate_tags(
    mapping_file: str = None,
    dry_run: bool = True,
    backup: bool = True
):
    """Apply tag consolidation mapping to entire vault"""
    if backup:
        create_backup_snapshot()
    
    if mapping_file:
        mappings = load_mapping_table(mapping_file)
    else:
        mappings = {**CRITICAL_CONSOLIDATIONS, **PATH_TAG_CONSOLIDATIONS}
    
    results = []
    for md_file in VAULT_PATH.rglob("*.md"):
        changes = apply_tag_mappings(md_file, mappings, dry_run)
        if changes:
            results.append({
                "file": str(md_file.relative_to(VAULT_PATH)),
                "changes": changes
            })
    
    return {
        "dry_run": dry_run,
        "files_affected": len(results),
        "total_changes": sum(len(r["changes"]) for r in results),
        "details": results
    }
```

#### 2. Tag Audit with Smart Suggestions
```python
@router.get("/api/tags/audit")
async def audit_tags():
    """Comprehensive tag analysis with consolidation suggestions"""
    tag_counter = Counter()
    
    # Collect all tags from all files
    for md_file in VAULT_PATH.rglob("*.md"):
        tags = extract_all_tags(md_file)
        tag_counter.update(tags)
    
    # Analyze for consolidation opportunities
    suggestions = analyze_consolidation_opportunities(tag_counter)
    
    return {
        "total_tags": len(tag_counter),
        "total_instances": sum(tag_counter.values()),
        "top_50_tags": tag_counter.most_common(50),
        "consolidation_suggestions": suggestions,
        "case_issues": find_case_variations(tag_counter),
        "hash_prefixes": find_hash_prefixed_tags(tag_counter),
        "path_like_tags": find_path_like_tags(tag_counter)
    }
```

#### 3. Emergency Backup System
```python
@router.post("/api/backup/create")
async def create_emergency_backup():
    """Create complete vault backup before major operations"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = VAULT_PATH.parent / f"flatline_backup_{timestamp}"
    
    # Copy entire vault
    shutil.copytree(VAULT_PATH, backup_path)
    
    # Create manifest
    manifest = {
        "backup_date": timestamp,
        "source_path": str(VAULT_PATH),
        "file_count": len(list(VAULT_PATH.rglob("*.md"))),
        "total_size": sum(f.stat().st_size for f in VAULT_PATH.rglob("*") if f.is_file())
    }
    
    with open(backup_path / "backup_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    
    return {
        "backup_path": str(backup_path),
        "manifest": manifest
    }
```

## Implementation Plan - Next 48 Hours

### Day 1: Critical Fixes
1. **Fix YAML generation** in `utils.py` - Replace yaml.dump with custom function
2. **Test Obsidian compatibility** - Verify tags appear in property panel
3. **Create backup system** - Ensure data safety before any changes

### Day 2: Tag Consolidation  
1. **Implement tag consolidation endpoints** 
2. **Run dry-run consolidation** on critical mappings
3. **Execute actual consolidation** after verification

### Quick Test Script
```python
# test_obsidian_yaml.py
def test_yaml_format():
    sample_data = {
        'tags': ['flatline', 'protocol', 'memoir'],
        'aliases': ['Test Document'],
        'date': '2025-09-13',
        'category': 'recovery'
    }
    
    yaml_output = generate_obsidian_yaml(sample_data)
    print("Generated YAML:")
    print(yaml_output)
    
    # This should produce:
    # ---
    # tags:
    #   - flatline  
    #   - memoir
    #   - protocol
    # aliases:
    #   - "Test Document"
    # date: "2025-09-13"
    # category: "recovery"
    # ---
```

## Expected Impact
- **Tag count reduction**: ~60% (from ~800 unique tags to ~300)
- **Obsidian compatibility**: 100% property panel recognition
- **Search improvement**: Consolidated tags improve discoverability
- **Memoir structure**: Cleaner thematic organization

This phase addresses the most critical technical debt while preserving all your content and maintaining compatibility with your existing Obsidian workflow.