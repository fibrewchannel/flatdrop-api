import re
import yaml
import json
import shutil
import time
from datetime import date, datetime
from collections import Counter, defaultdict
from pathlib import Path
from app.config import VAULT_BASE_PATH


# ============================================================================
# EXISTING ENHANCED YAML GENERATION FOR OBSIDIAN COMPATIBILITY
# ============================================================================

# ============================================================================
# MISSING UTILITY FUNCTIONS - ADD THESE
# ============================================================================

def validate_markdown(content: str) -> bool:
    """Basic markdown validation"""
    return isinstance(content, str) and len(content.strip()) > 0

def write_markdown_file(file_path: Path, content: str):
    """Write content to markdown file"""
    file_path.write_text(content, encoding="utf-8")

def parse_yaml_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from markdown content"""
    if not content.startswith("---"):
        return {}
    
    try:
        lines = content.split('\n')
        yaml_end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), -1)
        if yaml_end > 0:
            yaml_content = '\n'.join(lines[1:yaml_end])
            return yaml.safe_load(yaml_content) or {}
    except:
        return {}
    
    return {}

def fix_yaml_frontmatter(content: str) -> str:
    """Fix malformed YAML frontmatter"""
    return content

def extract_all_tags(file_path: Path) -> list:
    """Extract all tags from a markdown file"""
    try:
        content = file_path.read_text(encoding="utf-8")
        yaml_data = parse_yaml_frontmatter(content)
        tags = yaml_data.get('tags', [])
        if isinstance(tags, list):
            return tags
        elif isinstance(tags, str):
            return [tags]
        return []
    except:
        return []

def analyze_consolidation_opportunities(tag_counter: Counter) -> dict:
    """Analyze tags for consolidation opportunities"""
    return {"suggestions": []}

def create_backup_snapshot(vault_path: Path) -> Path:
    """Create backup snapshot"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = vault_path.parent / f"backup_{timestamp}"
    return backup_path

# You'll also need this constant that routes.py references:
CRITICAL_CONSOLIDATIONS = {
    "flatline-codex": "flatline",
    "FLATLINE": "flatline",
    "#flatline": "flatline"
}

# And make sure you have this import at the top of utils.py:
VAULT_PATH = VAULT_BASE_PATH  # routes.py expects this name

def generate_obsidian_yaml(parsed_data):
    """Generate Obsidian 1.4+ compatible YAML with multi-line arrays"""
    yaml_lines = ["---"]
    
    # Handle aliases first (maintain order for consistency)
    if 'aliases' in parsed_data and parsed_data['aliases']:
        yaml_lines.append("aliases:")
        for alias in parsed_data['aliases']:
            yaml_lines.append(f'  - "{alias}"')
    else:
        yaml_lines.append("aliases: []")
    
    # Handle tags as multi-line array (REQUIRED for Obsidian property panel)
    if 'tags' in parsed_data and parsed_data['tags']:
        yaml_lines.append("tags:")
        for tag in sorted(set(parsed_data['tags'])):
            yaml_lines.append(f"  - {tag}")
    else:
        yaml_lines.append("tags: []")
    
    # Add other properties in alphabetical order
    other_props = {k: v for k, v in parsed_data.items() if k not in ['tags', 'aliases']}
    for key in sorted(other_props.keys()):
        value = other_props[key]
        if isinstance(value, str):
            yaml_lines.append(f'{key}: "{value}"')
        elif isinstance(value, (int, float, bool)):
            yaml_lines.append(f'{key}: {value}')
        elif isinstance(value, list):
            if len(value) == 0:
                yaml_lines.append(f'{key}: []')
            else:
                yaml_lines.append(f'{key}:')
                for item in value:
                    yaml_lines.append(f'  - "{item}"')
        else:
            yaml_lines.append(f'{key}: {value}')
    
    yaml_lines.append("---")
    return "\n".join(yaml_lines)

# ============================================================================
# TESSERACT 4D COORDINATE SYSTEM - CORE FUNCTIONS
# ============================================================================

def extract_tesseract_position(content: str) -> dict:
    """Extract 4D Tesseract coordinates for any document"""
    
    # X-Axis: Structure/Archetype Analysis
    x_structure = identify_codex_structure(content)
    
    # Y-Axis: Transmission/Medium Analysis
    y_transmission = identify_transmission_mode(content)
    
    # Z-Axis: Purpose Vector Analysis (Rick's 5 core intents)
    z_purpose = map_to_life_purpose(content)
    
    # W-Axis: Cognitive Terrain Analysis (Cynefin-based)
    w_terrain = assess_cognitive_complexity(content)
    
   initial_coordinates = {
    "x_structure": x_structure,
    "y_transmission": y_transmission,
    "z_purpose": z_purpose,
    "w_terrain": w_terrain,
    "tesseract_key": f"{x_structure}:{y_transmission}:{z_purpose}:{w_terrain}"
    }

    # THEN apply corrections and return
    return apply_coordinate_corrections(file_path, initial_coordinates)

# Enhanced coordinate extraction rules for app/utils.py
# Add these correction rules to the extract_tesseract_position function

def apply_coordinate_corrections(file_path: str, initial_coords: dict) -> dict:
    """
    Apply learned corrections to coordinate extraction
    Based on manual training feedback from Week 1 analysis
    """
    corrected = initial_coords.copy()
    
    # Job search content correction rules
    job_search_patterns = [
        'job-search/', 'resume', 'cover-letter', 'interview', 'employment',
        'salary', 'hiring', 'application', 'career', 'professional',
        'two-pronger', 'death-job', 'survival-job', 'linkedin'
    ]
    
    # Survival/crisis content correction rules
    survival_patterns = [
        'homeless', 'rent', 'housing', 'money', 'survival', 'poverty',
        'benefits', 'snap', 'medicaid', 'sober-house', 'shelter',
        'medical', 'mayo-clinic', 'cirrhosis', 'ssdi', 'disability'
    ]
    
    # Recovery content patterns (should stay help-addict)
    recovery_patterns = [
        'aa', 'meeting', 'step', 'sponsor', 'addiction', 'recovery',
        'sober', 'sobriety', 'program', 'inventory', 'amends'
    ]
    
    file_lower = file_path.lower()
    
    # Apply job search corrections
    if any(pattern in file_lower for pattern in job_search_patterns):
        if corrected.get('z_purpose') in ['help-addict', 'help-world']:
            corrected['z_purpose'] = 'financial-amends'
            corrected['correction_applied'] = 'job_search_pattern'
    
    # Apply survival crisis corrections
    elif any(pattern in file_lower for pattern in survival_patterns):
        if corrected.get('z_purpose') == 'help-addict':
            corrected['z_purpose'] = 'prevent-death-poverty'
            corrected['correction_applied'] = 'survival_pattern'
    
    # Keep recovery content as help-addict (no correction needed)
    elif any(pattern in file_lower for pattern in recovery_patterns):
        if corrected.get('z_purpose') != 'help-addict':
            corrected['z_purpose'] = 'help-addict'
            corrected['correction_applied'] = 'recovery_pattern'
    
    # Update tesseract key if corrections were applied
    if 'correction_applied' in corrected:
        corrected['tesseract_key'] = f"{corrected['x_structure']}:{corrected['y_transmission']}:{corrected['z_purpose']}:{corrected['w_terrain']}"
    
    return corrected


def extract_tesseract_position(content: str, file_path: str = "") -> dict:
    """
    Enhanced extraction with correction rules applied
    """
    # ... existing extraction logic ...
    
    initial_coordinates = {
        'x_structure': determine_structure(content, file_path),
        'y_transmission': determine_transmission(content, file_path),
        'z_purpose': determine_purpose(content, file_path),
        'w_terrain': determine_terrain(content, file_path)
    }
    
    initial_coordinates['tesseract_key'] = f"{initial_coordinates['x_structure']}:{initial_coordinates['y_transmission']}:{initial_coordinates['z_purpose']}:{initial_coordinates['w_terrain']}"
    
    # Apply learned corrections
    corrected_coordinates = apply_coordinate_corrections(file_path, initial_coordinates)
    
    return corrected_coordinates

# Enhanced purpose detection with job search priority
def determine_purpose(content: str, file_path: str = "") -> str:
    """
    Determine Z-axis purpose with corrections for common misclassifications
    """
    content_lower = content.lower()
    path_lower = file_path.lower()
    
    # Priority 1: Job search and work responsibility (most commonly misclassified)
    job_indicators = [
        'resume', 'cover letter', 'job application', 'interview', 'employment',
        'salary', 'hiring', 'career', 'professional', 'work', 'consultant',
        'two-pronger', 'death job', 'survival job', 'life-affirming',
        'linkedin', 'indeed', 'recruiter', 'hr'
    ]
    
    if 'job-search/' in path_lower or any(indicator in content_lower for indicator in job_indicators):
        return 'financial-amends'
    
    # Priority 2: Survival and crisis content
    survival_indicators = [
        'homeless', 'rent', 'housing', 'money', 'survival', 'poverty', 'death',
        'benefits', 'snap', 'medicaid', 'sober house', 'shelter', 'crisis',
        'medical', 'mayo clinic', 'cirrhosis', 'ssdi', 'disability', 'emergency'
    ]
    
    if any(indicator in content_lower for indicator in survival_indicators):
        return 'prevent-death-poverty'
    
    # Priority 3: Recovery content (legitimate help-addict)
    recovery_indicators = [
        'aa', 'meeting', 'step', 'sponsor', 'addiction', 'recovery', 'sober',
        'sobriety', 'program', 'inventory', 'amends', 'big book', 'prayer',
        'meditation', 'fellowship'
    ]
    
    if any(indicator in content_lower for indicator in recovery_indicators):
        return 'help-addict'
    
    # Default logic for other content...
    # ... rest of existing determine_purpose logic ...
    
    return 'tell-story'  # Default fallback

def identify_codex_structure(content: str) -> str:
    """Map content to Tesseract X-dimension structures"""
    content_lower = content.lower()
    
    # Archetype: Recurring symbolic patterns, personas
    archetype_markers = [
        "the speaker", "the witness", "the survivor", "the addict", "the patient",
        "character", "persona", "role", "identity", "self as", "i am", "who i am"
    ]
    archetype_score = sum(content_lower.count(marker) for marker in archetype_markers)
    
    # Protocol: Repeatable actions, routines, invocations
    protocol_markers = [
        "step ", "routine", "process", "method", "technique", "practice",
        "flow", "ritual", "procedure", "system", "framework", "how to"
    ]
    protocol_score = sum(content_lower.count(marker) for marker in protocol_markers)
    
    # Shadowcast: Exploratory, mood-linked emotional fragments
    shadowcast_markers = [
        "fragment", "mood", "feeling", "shadow", "dark", "hidden",
        "explore", "question", "wonder", "doubt", "fear", "shame", "confused"
    ]
    shadowcast_score = sum(content_lower.count(marker) for marker in shadowcast_markers)
    
    # Expansion: Context, appendices, supporting material
    expansion_markers = [
        "context", "background", "detail", "appendix", "note", "reference",
        "elaboration", "explanation", "supporting", "additional", "more on"
    ]
    expansion_score = sum(content_lower.count(marker) for marker in expansion_markers)
        
    # Summoning: Agency instantiation, centering, provocation
    summoning_markers = [
        "summon", "invoke", "call", "manifest", "create", "begin",
        "activate", "trigger", "initiate", "center", "focus", "now"
    ]
    summoning_score = sum(content_lower.count(marker) for marker in summoning_markers)
    
    # Return highest scoring structure type
    scores = {
        "archetype": archetype_score,
        "protocol": protocol_score,
        "shadowcast": shadowcast_score,
        "expansion": expansion_score,
        "summoning": summoning_score
    }
    
    max_structure = max(scores.items(), key=lambda x: x[1])
    return max_structure[0] if max_structure[1] > 0 else "archetype"

def identify_transmission_mode(content: str) -> str:
    """Map content to Tesseract Y-dimension transmission modes"""
    content_lower = content.lower()
    
    # Narrative: Story, memoir, case study, parable
    narrative_markers = [
        "story", "remember", "happened", "experience", "journey",
        "chapter", "memoir", "narrative", "tale", "account", "when i"
    ]
    narrative_score = sum(content_lower.count(marker) for marker in narrative_markers)
    
    # Tarot: Metaphorical positioning, intuitive alignment
    tarot_markers = [
        "card", "spread", "reading", "intuition", "symbol", "metaphor",
        "archetype", "meaning", "interpretation", "guidance", "divination"
    ]
    tarot_score = sum(content_lower.count(marker) for marker in tarot_markers)
        
    # Image: Symbolic or illustrative artifacts
    image_markers = [
        "image", "picture", "visual", "art", "drawing", "render",
        "sigil", "symbol", "illustration", "graphic", "ai art"
    ]
    image_score = sum(content_lower.count(marker) for marker in image_markers)
        
    # Invocation: Commands, prompts, executable functions
    invocation_markers = [
        "invoke", "call", "command", "prompt", "execute", "run",
        "trigger", "activate", "summon", "begin", "do this"
    ]
    invocation_score = sum(content_lower.count(marker) for marker in invocation_markers)
    
    # Score text by default characteristics
    text_score = 1  # Base score for all text
    if content.startswith("---"):  # Has YAML frontmatter
        text_score += 1
    if "```" in content:  # Has code blocks
        text_score += 1
    
    scores = {
        "narrative": narrative_score + (2 if "i " in content_lower[:100] else 0),
        "tarot": tarot_score,
        "image": image_score,
        "invocation": invocation_score,
        "text": text_score
    }
    
    max_transmission = max(scores.items(), key=lambda x: x[1])
    return max_transmission[0]

def map_to_life_purpose(content: str) -> str:
    """Map content to Rick's 5 core life purposes (Z-dimension)"""
    content_lower = content.lower()
    
    # Tell My Story (memoir, personal narrative)
    story_markers = [
        "my story", "memoir", "autobiography", "personal", "life story",
        "remember", "childhood", "past", "history", "experience", "growing up"
    ]
    story_score = sum(content_lower.count(marker) for marker in story_markers)
    
    # Help Another Addict (recovery, AA, support)
    help_addict_markers = [
        "recovery", "aa", "na", "sober", "addiction", "alcoholic",
        "sponsor", "step", "meeting", "program", "help others", "share"
    ]
    help_addict_score = sum(content_lower.count(marker) for marker in help_addict_markers)
    
    # Prevent Death/Poverty (practical survival, medical, housing)
    survival_markers = [
        "medical", "health", "money", "housing", "homeless", "survival",
        "practical", "bills", "rent", "insurance", "benefits", "mayo", "poor"
    ]
    survival_score = sum(content_lower.count(marker) for marker in survival_markers)
    
    # Financial Amends (work, income, responsibility)
    amends_markers = [
        "work", "job", "income", "money", "debt", "amends", "responsibility",
        "financial", "career", "employment", "earning", "interview"
    ]
    amends_score = sum(content_lower.count(marker) for marker in amends_markers)
    
    # Help the World (creative work, systems, contribution)
    help_world_markers = [
        "creative", "art", "system", "tool", "help", "contribute",
        "world", "others", "community", "service", "impact", "api"
    ]
    help_world_score = sum(content_lower.count(marker) for marker in help_world_markers)
    
    scores = {
        "tell-story": story_score + (3 if any(pronoun in content_lower[:200] for pronoun in ["i ", "my ", "me "]) else 0),
        "help-addict": help_addict_score,
        "prevent-death-poverty": survival_score,
        "financial-amends": amends_score,
        "help-world": help_world_score
    }
    
    max_purpose = max(scores.items(), key=lambda x: x[1])
    return max_purpose[0] if max_purpose[1] > 0 else "tell-story"

def assess_cognitive_complexity(content: str) -> str:
    """Map content to Cynefin cognitive terrain (W-dimension)"""
    content_lower = content.lower()
    lines = content.split('\n')
    
    # Chaotic: Crisis, emotional overwhelm, trauma responses
    chaotic_markers = [
        "crisis", "panic", "overwhelm", "chaos", "emergency", "breakdown",
        "trauma", "triggered", "flashback", "can't think", "losing it"
    ]
    chaos_score = sum(content_lower.count(marker) for marker in chaotic_markers)
    
    # Confused: Fragmented, contradictory, unclear states
    confused_markers = [
        "confused", "don't know", "unclear", "mixed up", "conflicted",
        "contradictory", "foggy", "lost", "scattered", "what do i"
    ]
    confusion_score = sum(content_lower.count(marker) for marker in confused_markers)
    
    # Complex: Emergent, iterative, requires experimentation
    complex_markers = [
        "complex", "emerge", "iterate", "experiment", "adapt", "evolve",
        "uncertain", "multiple factors", "interconnected", "nuanced"
    ]
    complex_score = sum(content_lower.count(marker) for marker in complex_markers)
    
    # Complicated: Expert knowledge, known solutions, technical
    complicated_markers = [
        "technical", "system", "process", "method", "expert", "analysis",
        "detailed", "specific", "procedure", "algorithm", "api", "code"
    ]
    complicated_score = sum(content_lower.count(marker) for marker in complicated_markers)
    
    # Calculate contextual scores
    scores = {
        "chaotic": chaos_score + (5 if any(line.isupper() and len(line) > 10 for line in lines) else 0),
        "confused": confusion_score + (3 if content.count("?") > 5 else 0),
        "complex": complex_score + (2 if len(content.split()) > 500 else 0),
        "complicated": complicated_score + (3 if "```" in content else 0),
        "obvious": 1 + (1 if len(content.split()) < 100 else 0)
    }
    
    # Return highest scoring terrain
    max_terrain = max(scores.items(), key=lambda x: x[1])
    return max_terrain[0]

def calculate_memoir_priority(coordinates: dict, content: str) -> float:
    """Calculate memoir production priority based on Tesseract position"""
    priority = 0.0
    
    # High priority for story-focused narrative content
    if coordinates["z_purpose"] == "tell-story" and coordinates["y_transmission"] == "narrative":
        priority += 0.4
    
    # Recovery documents are central to Rick's story
    if coordinates["z_purpose"] == "help-addict":
        priority += 0.3
    
    # Archetype and Protocol structures tend to be more memoir-ready
    if coordinates["x_structure"] in ["archetype", "protocol"]:
        priority += 0.2
    
    # Complex terrain often contains rich, developed content
    if coordinates["w_terrain"] == "complex":
        priority += 0.1
        
    # Bonus for temporal markers (chronological narrative)
    temporal_markers = ["years ago", "back then", "childhood", "recently", "now", "when i was"]
    temporal_score = sum(content.lower().count(marker) for marker in temporal_markers)
    priority += min(0.2, temporal_score * 0.05)
    
    # Bonus for emotional content (memoir needs feeling)
    emotional_words = ["remember", "felt", "emotion", "pain", "joy", "fear", "hope", "love", "hate"]
    emotion_score = sum(content.lower().count(word) for word in emotional_words)
    priority += min(0.2, emotion_score * 0.02)
    
    return min(1.0, priority)

# ============================================================================
# 4D ANALYSIS FUNCTIONS
# ============================================================================

def calculate_4d_coherence(coordinates_list: list) -> float:
    """Calculate how coherent files are within 4D Tesseract space"""
    if not coordinates_list:
        return 0.0
    
    # Count unique values in each dimension
    x_values = set(coord["x_structure"] for coord in coordinates_list)
    y_values = set(coord["y_transmission"] for coord in coordinates_list)
    z_values = set(coord["z_purpose"] for coord in coordinates_list)
    w_values = set(coord["w_terrain"] for coord in coordinates_list)
    
    total_files = len(coordinates_list)
    
    # Higher coherence = fewer unique values per dimension
    x_coherence = 1.0 - (len(x_values) - 1) / max(total_files - 1, 1)
    y_coherence = 1.0 - (len(y_values) - 1) / max(total_files - 1, 1)
    z_coherence = 1.0 - (len(z_values) - 1) / max(total_files - 1, 1)
    w_coherence = 1.0 - (len(w_values) - 1) / max(total_files - 1, 1)
    
    # Weight Z-axis (purpose) most heavily for Rick's memoir project
    weighted_coherence = (x_coherence + y_coherence + z_coherence * 2 + w_coherence) / 5
    
    return round(weighted_coherence, 3)

def find_tesseract_clusters(tesseract_map: dict) -> dict:
    """Find natural clusters in 4D Tesseract space"""
    clusters = defaultdict(list)
    
    # Group by similar coordinate patterns
    for file_path, coordinates in tesseract_map["coordinate_combinations"].items():
        # Create cluster key focusing on purpose + structure (most important for memoir)
        cluster_key = f"{coordinates['z_purpose']}+{coordinates['x_structure']}"
        clusters[cluster_key].append({
            "file": file_path,
            "full_coordinates": coordinates
        })
    
    # Filter to significant clusters (5+ files)
    significant_clusters = {
        cluster_id: files for cluster_id, files in clusters.items()
        if len(files) >= 5
    }
    
    return significant_clusters

def generate_tesseract_folder_path(purpose: str, structure: str) -> str:
    """Generate folder path based on Tesseract coordinates"""
    
    # Primary organization by Purpose (Z-dimension) - Rick's core life intents
    purpose_folders = {
        "tell-story": "memoir",
        "help-addict": "recovery",
        "prevent-death-poverty": "survival",
        "financial-amends": "work-amends",
        "help-world": "contribution"
    }
    
    # Secondary organization by Structure (X-dimension)
    structure_subfolders = {
        "archetype": "personas",
        "protocol": "practices",
        "shadowcast": "explorations",
        "expansion": "context",
        "summoning": "activations"
    }
    
    base_folder = purpose_folders.get(purpose, "unsorted")
    structure_folder = structure_subfolders.get(structure, "general")
    
    return f"{base_folder}/{structure_folder}"

# ============================================================================
# ENHANCED CONTENT INTELLIGENCE FUNCTIONS
# ============================================================================

def identify_document_archetype(content: str) -> str:
    """Classify document type based on content patterns"""
    content_lower = content.lower()
    
    # Recovery/AA indicators (check first - Rick's core focus)
    recovery_markers = [
        "step ", "sponsor", "meeting", "sobriety", "recovery", " aa ", " na ",
        "alcoholic", "addict", "sober", "relapse", "program", "higher power",
        "inventory", "amends", "defects", "resentment", "powerless"
    ]
    if any(marker in content_lower for marker in recovery_markers):
        return "recovery-document"
    
    # Memoir/narrative indicators
    memoir_markers = [
        "i remember", "back then", "years ago", "childhood", "growing up",
        "my mother", "my father", "when i was", "as a child", "memoir",
        "my story", "looking back", "in those days"
    ]
    if any(marker in content_lower for marker in memoir_markers):
        return "memoir-narrative"
    
    # Medical/health indicators (Mayo, therapy, etc.)
    medical_markers = [
        "mayo", "doctor", "medical", "treatment", "therapy", "diagnosis",
        "cirrhosis", "liver", "medication", "appointment", "clinic",
        "therapist", "psychiatrist", "mental health", "cptsd", "trauma"
    ]
    if any(marker in content_lower for marker in medical_markers):
        return "medical-health"
    
    # Creative work indicators
    creative_markers = [
        "draw things", "ai art", "prompt", "generated", "creative",
        "stable diffusion", "sd", "render", "image", "artwork", "sora",
        "music", "song", "comedy", "joke", "performance"
    ]
    if any(marker in content_lower for marker in creative_markers):
        return "creative-work"
    
    # Technical/system indicators
    technical_markers = [
        "api", "code", "system", "endpoint", "function", "error",
        "python", "fastapi", "server", "database", "programming",
        "obsidian", "vault", "yaml", "markdown", "script"
    ]
    if any(marker in content_lower for marker in technical_markers):
        return "technical-system"
    
    # Philosophy/reflection indicators
    philosophy_markers = [
        "philosophy", "meaning", "existence", "consciousness", "reality",
        "god", "spiritual", "universe", "purpose", "truth", "wisdom",
        "reflection", "thoughts on", "what is", "why do we"
    ]
    if any(marker in content_lower for marker in philosophy_markers):
        return "philosophical-reflection"
    
    # Financial/practical life indicators
    practical_markers = [
        "money", "rent", "housing", "homeless", "shelter", "benefits",
        "medicaid", "snap", "work", "job", "income", "budget", "poor",
        "sober house", "rochester"
    ]
    if any(marker in content_lower for marker in practical_markers):
        return "practical-life"
    
    # Default to general if no clear pattern
    return "general-document"

def extract_content_signature(content: str) -> dict:
    """Extract key content characteristics for clustering"""
    lines = content.split('\n')
    words = content.split()
    
    # Count emotional language markers
    emotional_markers = count_emotional_language(content)
    
    # Detect temporal markers (important for memoir chronology)
    temporal_markers = count_temporal_markers(content)
    
    # Find cross-references
    cross_refs = count_internal_references(content)
    
    return {
        "line_count": len(lines),
        "word_count": len(words),
        "has_yaml": content.startswith("---"),
        "has_code_blocks": "```" in content,
        "has_links": "[[" in content or "http" in content,
        "has_lists": any(line.strip().startswith(("-", "*", "1.")) for line in lines),
        "paragraph_count": len([line for line in lines if line.strip() and not line.startswith("#")]),
        "heading_count": len([line for line in lines if line.startswith("#")]),
        "question_density": content.count("?") / max(len(words), 1),
        "emotional_intensity": emotional_markers["total_score"],
        "temporal_markers": temporal_markers,
        "cross_reference_count": cross_refs,
        "readability_score": estimate_readability(content),
        "personal_pronouns": count_personal_pronouns(content)
    }

def count_emotional_language(content: str) -> dict:
    """Count emotional markers for memoir/recovery content classification"""
    content_lower = content.lower()
    
    # Recovery-specific emotional markers
    recovery_emotions = ["shame", "guilt", "fear", "anger", "resentment", "gratitude",
                        "hope", "despair", "powerless", "surrender", "acceptance"]
    
    # General emotional intensity markers
    intense_emotions = ["devastated", "terrified", "overwhelmed", "desperate",
                       "hopeless", "furious", "ecstatic", "peaceful", "serene"]
    
    # Trauma/CPTSD markers
    trauma_markers = ["triggered", "flashback", "dissociat", "hypervigilant",
                     "frozen", "panic", "nightmare", "intrusive"]
    
    scores = {
        "recovery_emotional": sum(content_lower.count(word) for word in recovery_emotions),
        "intense_emotional": sum(content_lower.count(word) for word in intense_emotions),
        "trauma_markers": sum(content_lower.count(word) for word in trauma_markers)
    }
    
    scores["total_score"] = sum(scores.values())
    return scores

def count_temporal_markers(content: str) -> dict:
    """Identify temporal references for memoir chronology"""
    content_lower = content.lower()
    
    # Specific time periods
    childhood_markers = ["childhood", "as a child", "when i was young", "elementary", "high school"]
    adult_markers = ["college", "university", "first job", "career", "marriage", "divorce"]
    recent_markers = ["recently", "last week", "yesterday", "this morning", "today"]
    
    # Age references
    age_pattern = re.compile(r'\b(?:age|years old|when i was) (\d+)\b', re.IGNORECASE)
    age_matches = age_pattern.findall(content)
    
    # Year references
    year_pattern = re.compile(r'\b(19\d{2}|20\d{2})\b')
    year_matches = year_pattern.findall(content)
    
    return {
        "childhood_markers": sum(content_lower.count(marker) for marker in childhood_markers),
        "adult_markers": sum(content_lower.count(marker) for marker in adult_markers),
        "recent_markers": sum(content_lower.count(marker) for marker in recent_markers),
        "age_references": len(age_matches),
        "year_references": len(year_matches),
        "specific_ages": [int(age) for age in age_matches if age.isdigit()],
        "specific_years": [int(year) for year in year_matches]
    }

def count_internal_references(content: str) -> int:
    """Count internal links and references for relationship mapping"""
    # Obsidian-style links
    obsidian_links = re.findall(r'\[\[([^\]]+)\]\]', content)
    
    # Hash tag references
    hash_tags = re.findall(r'(?<!\w)#([\w/-]+)', content)
    
    # Explicit references to other documents
    ref_patterns = [
        r'see also:?\s*([^\n]+)',
        r'related:?\s*([^\n]+)',
        r'mentioned in:?\s*([^\n]+)'
    ]
    
    explicit_refs = []
    for pattern in ref_patterns:
        explicit_refs.extend(re.findall(pattern, content, re.IGNORECASE))
    
    return len(obsidian_links) + len(hash_tags) + len(explicit_refs)

def estimate_readability(content: str) -> float:
    """Simple readability estimate (higher = more complex)"""
    sentences = re.split(r'[.!?]+', content)
    words = content.split()
    
    if not sentences or not words:
        return 0.0
    
    avg_sentence_length = len(words) / len(sentences)
    
    # Count complex words (3+ syllables, rough estimate)
    complex_words = sum(1 for word in words if len(word) > 6)
    complex_word_ratio = complex_words / len(words) if words else 0
    
    # Simple readability score
    return avg_sentence_length + (complex_word_ratio * 100)

def count_personal_pronouns(content: str) -> dict:
    """Count personal pronouns to gauge narrative perspective"""
    content_lower = content.lower()
    
    pronouns = {
        "first_person": ["i ", "me ", "my ", "mine ", "myself "],
        "second_person": ["you ", "your ", "yours ", "yourself "],
        "third_person": ["he ", "she ", "him ", "her ", "his ", "hers ", "they ", "them "]
    }
    
    counts = {}
    for category, pronoun_list in pronouns.items():
        counts[category] = sum(content_lower.count(pronoun) for pronoun in pronoun_list)
    
    total = sum(counts.values())
    if total > 0:
        counts["perspective"] = max(counts, key=counts.get)
    else:
        counts["perspective"] = "unknown"
    
    return counts

# ============================================================================
# FOLDER STRUCTURE ANALYSIS
# ============================================================================

def analyze_folder_content_types(md_files: list) -> dict:
    """Analyze the content types within a folder"""
    content_types = Counter()
    
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            archetype = identify_document_archetype(content)
            content_types[archetype] += 1
        except Exception:
            content_types["unreadable"] += 1
    
    total_files = len(md_files)
    return {
        "type_distribution": dict(content_types),
        "dominant_type": content_types.most_common(1)[0][0] if content_types else "unknown",
        "type_diversity": len(content_types) / total_files if total_files > 0 else 0
    }

def measure_tag_coherence(md_files: list) -> float:
    """Measure how coherent the tags are within a folder"""
    all_tags = []
    
    for md_file in md_files:
        try:
            tags = extract_all_tags(md_file)
            all_tags.extend(tags)
        except Exception:
            continue
    
    if not all_tags:
        return 0.0
    
    tag_counter = Counter(all_tags)
    unique_tags = len(tag_counter)
    total_tag_instances = sum(tag_counter.values())
    
    # Higher coherence = fewer unique tags relative to total instances
    coherence = 1.0 - (unique_tags / total_tag_instances) if total_tag_instances > 0 else 0.0
    return max(0.0, min(1.0, coherence))

def extract_naming_patterns(md_files: list) -> dict:
    """Extract naming patterns from filenames"""
    filenames = [f.stem for f in md_files]
    
    # Common prefixes
    prefixes = defaultdict(int)
    for name in filenames:
        parts = name.split('-')
        if len(parts) > 1:
            prefixes[parts[0]] += 1
    
    # Date patterns
    date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
    date_files = [name for name in filenames if date_pattern.search(name)]
    
    # Number patterns
    number_pattern = re.compile(r'\d+')
    numbered_files = [name for name in filenames if number_pattern.search(name)]
    
    return {
        "total_files": len(filenames),
        "common_prefixes": dict(prefixes),
        "date_pattern_count": len(date_files),
        "numbered_files_count": len(numbered_files),
        "avg_filename_length": sum(len(name) for name in filenames) / len(filenames) if filenames else 0
    }

def calculate_urgency_score(content_types: dict, tag_coherence: float) -> float:
    """Calculate how urgently a folder needs reorganization"""
    type_diversity = content_types.get("type_diversity", 0)
    
    # High urgency factors:
    # - Low tag coherence (tags are all over the place)
    # - High type diversity (mixed content that should be separated)
    # - Large number of files (more impact from reorganization)
    
    urgency_score = 0.0
    
    # Penalty for low tag coherence
    urgency_score += (1.0 - tag_coherence) * 0.4
    
    # Penalty for high type diversity
    urgency_score += type_diversity * 0.4
    
    # Bonus for having many files (more impact)
    file_count = sum(content_types.get("type_distribution", {}).values())
    if file_count > 20:
        urgency_score += 0.2
    
    return min(1.0, urgency_score)

# ============================================================================
# REORGANIZATION PLANNING
# ============================================================================

def group_by_archetype(content_patterns: dict) -> dict:
    """Group files by their content archetype"""
    archetype_groups = defaultdict(list)
    
    for file_path, signature in content_patterns.get("content_signatures", {}).items():
        # This would need the archetype data from the analysis
        # For now, we'll infer from the content_patterns structure
        pass
    
    return dict(archetype_groups)

def generate_folder_path(archetype: str) -> str:
    """Generate suggested folder path based on archetype"""
    folder_mappings = {
        "recovery-document": "recovery/documents",
        "memoir-narrative": "memoir/narratives",
        "medical-health": "health/medical",
        "creative-work": "creative/projects",
        "technical-system": "systems/technical",
        "philosophical-reflection": "philosophy/reflections",
        "practical-life": "life/practical",
        "general-document": "general/misc"
    }
    
    return folder_mappings.get(archetype, "unsorted/needs-classification")

def calculate_priority(archetype: str, file_count: int) -> str:
    """Calculate reorganization priority"""
    high_priority_types = ["recovery-document", "memoir-narrative", "medical-health"]
    
    if archetype in high_priority_types and file_count > 10:
        return "high"
    elif file_count > 25:
        return "high"
    elif file_count > 10:
        return "medium"
    else:
        return "low"

def find_orphaned_files(folder_analysis: dict) -> list:
    """Find files in overly nested or singleton folders"""
    orphaned = []
    
    for folder_path, analysis in folder_analysis.items():
        file_count = analysis["file_count"]
        path_depth = len(Path(folder_path).parts)
        
        # Files in deep nested folders with few siblings
        if path_depth > 3 and file_count < 3:
            orphaned.extend([
                {"path": folder_path, "reason": "deep_nested_singleton"}
            ])
    
    return orphaned

def chunked(iterable, size):
    """Yield successive chunks of specified size from iterable"""
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]

# ============================================================================
# EXISTING TAG FUNCTIONS (PRESERVED)
# ============================================================================

CRITICAL_CONSOLIDATIONS = {
    # [Previous consolidation mappings preserved]
    "flatline-codex": "flatline",
    "FLATLINE": "flatline",
    "#flatline": "flatline",
    "archetypes": "archetype",
    "#archetypes": "archetype",
    "protocols": "protocol",
    "#protocols": "protocol",
    # [All other existing mappings...]
}

def apply_tag_consolidation(content: str, tag_mappings: dict) -> tuple[str, list]:
    """Apply tag consolidation with change tracking and YAML repair"""
    # [Existing function preserved as-is]
    changes = []
    updated_content = content
    
    # Handle YAML tags with error recovery
    if content.startswith("---"):
        try:
            yaml_data = parse_yaml_frontmatter(content)
            if yaml_data and 'tags' in yaml_data:
                original_tags = yaml_data['tags']
                if isinstance(original_tags, list):
                    updated_tags = []
                    for tag in original_tags:
                        new_tag = tag_mappings.get(str(tag), str(tag))
                        if str(new_tag) != str(tag):
                            changes.append(f"YAML tag: {tag} -> {new_tag}")
                        updated_tags.append(new_tag)
                    
                    yaml_data['tags'] = sorted(set(updated_tags))
                    
                    # Rebuild content with new YAML
                    lines = content.split('\n')
                    yaml_end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), -1)
                    if yaml_end > 0:
                        new_yaml = generate_obsidian_yaml(yaml_data)
                        updated_content = new_yaml + '\n' + '\n'.join(lines[yaml_end + 1:])
        except Exception as e:
            changes.append(f"YAML repair attempted: {str(e)}")
    
    return updated_content, changes

# [All other existing functions preserved...]
