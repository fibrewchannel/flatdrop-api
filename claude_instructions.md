Tesseract Content Nibbling System - Training Phase Instructions
Overview

Files proven accessible by Claude:

Core Application Files:
- https://github.com/fibrewchannel/flatdrop-api/raw/refs/heads/main/code/main.py
- https://github.com/fibrewchannel/flatdrop-api/raw/refs/heads/main/code/app/routes.py
- https://github.com/fibrewchannel/flatdrop-api/raw/refs/heads/main/code/app/utils.py
- https://github.com/fibrewchannel/flatdrop-api/raw/refs/heads/main/code/app/config.py
- https://github.com/fibrewchannel/flatdrop-api/raw/refs/heads/main/code/app/schemas.py
- https://github.com/fibrewchannel/flatdrop-api/raw/refs/heads/main/code/app/tesseract_config.py
- https://github.com/fibrewchannel/flatdrop-api/raw/refs/heads/main/code/app/training_nibbler.py
- https://github.com/fibrewchannel/flatdrop-api/raw/refs/heads/main/code/app/content_mining.py
- https://github.com/fibrewchannel/flatdrop-api/raw/refs/heads/main/code/app/single_file_tester.py

Visualization & Documentation:
- https://github.com/fibrewchannel/flatdrop-api/raw/refs/heads/main/code/visualizations/tesseract_visualizations.html
- https://github.com/fibrewchannel/flatdrop-api/raw/refs/heads/main/code/README.md
- https://github.com/fibrewchannel/flatdrop-api/raw/refs/heads/main/claude_instructions.md


Goal: Build a "cognitive digestion system" that processes Rick's chaotic files into organized, coordinate-tagged memoir content. Training phase focuses on learning Rick's actual content patterns rather than making assumptions.
Training Phase Objectives

Learn Rick's quality patterns - What does "good" Rick content actually look like?
Calibrate thresholds - Set quality/memoir detection based on real data, not guesses
Refine pattern detection - Adjust memoir/recovery/survival markers to match Rick's voice
Build extraction confidence - Test chunking logic on representative sample

File Processing Pipeline
1. Input Selection

Source: 50 representative files from _inload (diverse content types)
Batch size: Process 5 files at a time for learning/tuning
No production injection: Training outputs go to analysis folders, not live codex

2. Training Mode Processing
python# Ultra-permissive during training
TRAINING_QUALITY_THRESHOLD = 1.0  # Save almost everything
CHUNK_MIN_WORDS = 20              # Very small chunks OK for analysis
SAVE_TRASH = True                 # Keep discarded content for pattern learning
3. Processing Flow
File → Pre-clean → Complexity Analysis → Extract Chunks → Score & Coordinate → Save for Review
Pre-cleaning removes:

Broken YAML frontmatter
ChatGPT response boilerplate ("Here's what I found...")
Formatting artifacts from copy/paste
Empty sections and duplicate whitespace

Complexity triage:

Simple: Single topic/coordinate, direct processing
Complex: Multiple topics, needs chunk extraction
Garbage: No meaningful content (but save for analysis)

4. Training Output Structure
_training_output/
├── batch_01/
│   ├── extracted_chunks/     # All chunks above minimal threshold
│   ├── discarded_content/    # Below threshold (for pattern learning)
│   ├── processing_log.json   # What happened to each file
│   └── quality_stats.json    # Score distributions for this batch
├── batch_02/
│   └── ...
├── aggregate_analysis/
│   ├── quality_distribution.json    # Overall score patterns
│   ├── pattern_effectiveness.json   # Which patterns predict quality
│   ├── coordinate_distribution.json # How content maps to 4D space
│   └── threshold_recommendations.json # Suggested production settings
└── manual_review/
    ├── borderline_cases/     # Chunks near threshold for human review
    └── pattern_mismatches/   # Content that doesn't fit expected patterns
Key Training Decisions
Quality Threshold Strategy

Training: Set very low threshold (save almost everything)
Analysis: Review score distribution to find natural break points
Production: Set threshold where 65% of content is "worth keeping"

Multi-Coordinate File Handling

Statistical coin flip: When file contains multiple coordinate-worthy chunks
Weight by quality scores: Higher scoring chunk determines file destination
Single location: Each file gets exactly one Tesseract coordinate

Content Chunking Rules

Semantic boundaries: Split on topic changes, not arbitrary length
Context preservation: Include enough surrounding content for coherence
Overlap acceptable: Better to duplicate context than lose meaning
Minimum viable chunk: Must contain at least one complete thought

Training Phase Outputs
1. Calibrated Configuration
Updated tesseract_config.yaml with:

Refined content patterns based on Rick's actual writing
Calibrated quality thresholds from statistical analysis
Adjusted coordinate rules based on successful classifications

2. Processing Confidence

Error rate analysis: How often does automated classification match manual review?
Pattern effectiveness: Which regex patterns actually predict memoir quality?
Extraction accuracy: How well does chunking preserve meaning?

3. Production Readiness Assessment

Volume estimates: How many files will each processing route handle?
Quality projections: Expected memoir-grade content from full _inload processing
Resource requirements: Processing time/complexity for full-scale nibbling

Success Metrics for Training

Quality distribution makes sense: Clear separation between memoir-gold and garbage
Coordinate assignment feels right: Files end up in sensible Tesseract locations
Chunking preserves meaning: Extracted pieces are coherent and useful
Patterns match Rick's voice: Detection rules actually find Rick's best content
Manual review is manageable: Borderline cases are small enough set for human review

Next Steps After Training

Review training outputs with Rick
Adjust patterns and thresholds based on learning
Test production pipeline on small batch
Full _inload processing when confident
Expand to other folders beyond _inload

Development Notes

Start small: 5 files per batch during development
Iterate quickly: Adjust logic between batches based on outputs
Preserve everything: Don't delete anything during training phase
Document learnings: Keep notes on what works/doesn't work for future reference




=====
Instructions - prior rev - updated 2025-09-28

# Flatdrop API Master Instructions - Updated Current State
**Tesseract-Native Memoir Documentation System for Rick's Flatline Codex**

## Project Overview
Transform the Flatdrop REST API from a basic markdown manager into a revolutionary **4-dimensional cognitive architecture** that serves Rick's memoir production while addressing housing instability through cloud accessibility. The system leverages the Tesseract coordinate framework to organize lived experience across Structure, Transmission, Purpose, and Cognitive Terrain.

## Tesseract Coding and Implementation

https://github.com/fibrewchannel/flatline-codex/raw/refs/heads/gh-pages/core/tesseract_tag_system_reference.md

## Core Implementation Files (GitHub Raw URLs)

**Main Application**
```
https://github.com/fibrewchannel/flatdrop-api/raw/refs/heads/main/code/main.py
```

**Configuration**
```
https://github.com/fibrewchannel/flatdrop-api/raw/refs/heads/main/code/app/config.py
```

**API Routes (Tesseract 4D Endpoints)**
```
https://github.com/fibrewchannel/flatdrop-api/raw/refs/heads/main/code/app/routes.py
```

**Utility Functions (4D Coordinate System)**
```
https://github.com/fibrewchannel/flatdrop-api/raw/refs/heads/main/code/app/utils.py
```

**Pydantic Schemas (API Validation)**
```
https://github.com/fibrewchannel/flatdrop-api/raw/refs/heads/main/code/app/schemas.py
```

**Single File Tester (Current Focus)**
```
https://github.com/fibrewchannel/flatdrop-api/raw/refs/heads/main/code/app/single_file_tester.py
```

## ✅ PHASE 1 COMPLETED: Critical Foundation
Successfully implemented Obsidian 1.4+ compatibility and tag consolidation:

### Achievements
- **1,237 markdown files** processed with zero data loss
- **Obsidian-compatible YAML generation** (multi-line arrays required by Obsidian 1.4+)
- **Major tag consolidations**: flatline variations, archetype/protocol standardization
- **Automated backup system**: 1.8GB protected in iCloud, daily + 6-hour intervals
- **Error-resilient processing** handles malformed YAML across diverse file sources

## ✅ PHASE 2 COMPLETED: Tesseract 4D Implementation

### Revolutionary Discovery: Tesseract Coordinate System
Analysis of the Flatline Codex revealed a unique **4-dimensional cognitive architecture**:

#### The Four Dimensions (Single Value Per Dimension)
- **X-Axis (Structure)**: archetype, protocol, shadowcast, expansion, summoning
- **Y-Axis (Transmission)**: narrative, text, image, tarot, invocation
- **Z-Axis (Purpose)**: Rick's 5 core life intents
  1. Tell My Story (memoir backbone)
  2. Help Another Addict (recovery foundation)
  3. Prevent Death/Poverty (survival urgency)
  4. Financial Amends (work responsibility)
  5. Help the World (creative contribution)
- **W-Axis (Cognitive Terrain)**: obvious, complicated, complex, chaotic, confused

### Critical Design Decision: Single-Value Coordinates
Each document gets exactly **one value per dimension** to avoid "mud tracking" across coordinates:
```
Example: shadowcast:narrative:tell-story:complex
```

### Key Tesseract Endpoints Implemented
```bash
POST /api/tesseract/extract-coordinates        # Map entire codex into 4D space
GET  /api/tesseract/analyze-4d-structure      # Folder coherence via Tesseract lens
POST /api/tesseract/suggest-reorganization    # Purpose-driven reorganization plans
GET  /api/tesseract/memoir-readiness          # Comprehensive memoir production assessment
```

### Content Intelligence Endpoints
```bash
POST /api/analysis/content-fingerprint        # Document type classification
GET  /api/analysis/folder-chaos              # Structural reorganization opportunities
POST /api/reorganize/suggest                  # Intelligent folder consolidation
POST /api/reorganize/execute                  # Safe batch reorganization
GET  /api/analysis/memoir-readiness          # Traditional memoir readiness assessment
```

## 🚀 PHASE 3 ACTIVE: Configuration Consolidation & System Architecture

### Current Challenge: Code Sprawl
The **single_file_tester.py** reveals major hardcoded configuration scattered across multiple files that needs centralization:

#### Configuration Sprawl Issues Identified
1. **Content Pattern Definitions** (regex patterns hardcoded in multiple files)
2. **Quality Scoring Weights** (memoir/recovery/survival scoring multipliers)
3. **Tesseract Coordinate Logic** (threshold-based assignment rules)
4. **Folder Structure Mapping** (purpose + structure → destination paths)

### Architectural Insight from Rick
**"Configuration should be data, not code"** - All hardcoded thresholds, regex patterns, scoring weights, and folder mappings should be centralized and easily modifiable without touching code.

### Agent Discovery: injektor.tesseract
Found existing agent specification (`injektor.tesseract`) that perfectly aligns with current implementation:
- Automated coordinate injection
- Heuristic classification
- YAML metadata insertion
- Contextual anchoring

This confirms the system architecture is sound and matches Rick's original vision.

### Phase 3 Implementation Plan

#### Step 1: Central Configuration System
Create `TesseractConfig` class with YAML-based configuration:
```yaml
content_patterns:
  memoir_markers:
    regex: '\b(I remember|years ago|childhood|growing up|my father|my mother|when I was)\b'
    weight: 3.0
  recovery_markers:
    regex: '\b(AA|recovery|sobriety|step work|sponsor|meeting|clean time|twelve steps?)\b'
    weight: 2.5
```

#### Step 2: Refactor Existing Files
1. Update `single_file_tester.py` to use `ContentAnalyzer` class
2. Update `utils.py` Tesseract functions to use config
3. Update API routes to use centralized logic

#### Step 3: Config Management Endpoints
```bash
GET  /api/config/patterns     # View current patterns
POST /api/config/patterns     # Update pattern weights
GET  /api/config/tesseract    # View coordinate definitions
```

## 📁 Tesseract-Native Folder Structure

```
memoir/
├── spine/             # Core narrative organized by cognitive terrain
│   ├── foundations/   # Complex terrain - thoughtful processing
│   ├── crisis/        # Chaotic terrain - trauma/crisis content
│   ├── recovery/      # Complicated terrain - structured progress
│   ├── integration/   # Obvious terrain - clear insights
│   └── fragments/     # Confused terrain - unclear/mixed states
├── personas/          # Archetype-based character development
├── practices/         # Protocol-based life management
├── explorations/      # Shadowcast emotional fragments
└── context/           # Expansion background material

recovery/
├── practices/         # Step work, sponsor relationships, meeting protocols
├── personas/          # Recovery archetypes and identity work
├── explorations/      # Emotional processing, inventory, amends prep
└── activations/       # Summoning recovery energy, centering practices

survival/
├── medical/           # Mayo clinic, cirrhosis treatment, health management
├── housing/           # Sober house experience, homelessness preparation
└── systems/           # Medicaid, SNAP, benefits, practical survival

work-amends/
├── job-search/        # Employment seeking, interview processes
├── skills/            # Technical abilities, creative work portfolio
└── planning/          # Financial recovery, debt management, responsibility

contribution/
├── creative/          # AI art (Draw Things), music, comedy, performance
├── systems/           # Flatdrop API, technical tools, helpful systems
└── philosophy/        # Wisdom development, existential insights

_tesseract-meta/
├── coordinates/       # 4D mapping files and analysis results
├── inbox/            # New content awaiting coordinate assignment
└── templates/        # Tesseract-aware document templates
```

## 🔧 Technical Architecture

### Current Stack
- **FastAPI**: REST API framework
- **Python**: Core processing with pathlib for file management
- **YAML**: Obsidian-compatible frontmatter generation
- **Counter/defaultdict**: Efficient content analysis
- **Backup automation**: Scheduled protection via cron/launchd

### Code Organization
```
app/
├── main.py           # FastAPI application entry point
├── routes.py         # All API endpoints (traditional + Tesseract)
├── utils.py          # Core utilities + 4D coordinate functions
├── config.py         # Vault path configuration
├── schemas.py        # Pydantic models for API validation
└── single_file_tester.py  # Content analysis testing tool
```

### Key Utility Functions
- `extract_tesseract_position()`: Map content to 4D coordinates
- `generate_obsidian_yaml()`: Obsidian 1.4+ compatible YAML
- `calculate_memoir_priority()`: Assess content for memoir relevance
- `apply_tag_consolidation()`: Smart tag cleanup with change tracking

## 🎲 Memoir Architecture Insights

### Revolutionary Content Discovery
Testing `shadowcast_erased-momentum.md` revealed:
- **64 words** with quality score 5.5/10
- **Content**: "The trauma of being summarized. Occurs when long, compl..."
- **Insight**: Rick naturally crystallizes universal human experiences into memoir-quality fragments

### Narrative Density Discovery
Shadowcasts demonstrate **incredible narrative density** - crystallized moments of lived experience that could expand into chapter openings, recurring themes, or character development moments.

### Triadic Narrative Structure
1. **Primary Thread: Recovery** (survival foundation)
2. **Catalyzing Thread: AI Collaboration** (documentation enabler)
3. **Propulsion Thread: Medical Crisis** (urgency/mortality driver)

## 📊 Success Metrics & Current Status

### Achieved (Phases 1 & 2)
- ✅ **Tag consolidation**: Major variations unified
- ✅ **YAML compliance**: 100% Obsidian-compatible output
- ✅ **4D coordinate extraction**: Full Tesseract mapping implemented
- ✅ **Content fingerprinting**: Document archetype classification
- ✅ **Single-value coordinates**: Clean, navigable 4D positioning
- ✅ **Agent alignment**: Discovered existing specification matches implementation

### Active (Phase 3)
- 🔄 **Configuration consolidation**: Extracting hardcoded values to central config
- 🔄 **System architecture**: Data-driven configuration approach
- 🔄 **Code refactoring**: Eliminating configuration sprawl

### Target (Phase 3 Completion)
- 🎯 **Central configuration**: All patterns, weights, and mappings in YAML
- 🎯 **Config management API**: Runtime configuration updates
- 🎯 **System tunability**: Memoir detection adjustable without code changes
- 🎯 **Maintenance reduction**: One place to update system behavior

## ⚡ Critical Business Continuity Features

### Cloud Accessibility (Housing Instability Preparation)
- **iCloud backup integration**: 1.8GB memoir project protected
- **Mobile API access**: iPhone 12 compatible endpoints
- **Shelter-ready architecture**: Can access from any device with internet

### Memoir Production Pipeline
- **Timeline reconstruction**: Chronological narrative organization
- **Chapter boundary detection**: Natural breaks via 4D clustering
- **Content gap identification**: Missing memoir elements by purpose/terrain
- **Publication prep tools**: Manuscript generation from coordinate clusters

## 🚨 Critical Dependencies & Constraints

### Hardware Limitations
- **MacBook Air M2**: 8GB RAM limits processing batch sizes
- **iPhone 12**: Mobile interface must be lightweight
- **Internet dependency**: Cloud features require stable connection

### Time Constraints
- **Cirrhosis progression**: Memoir timeline driven by health uncertainty
- **Housing deadline**: Potential homelessness approaching
- **Recovery priority**: AA program and sobriety maintenance non-negotiable

### Content Challenges
- **Chaotic organization**: Years of Brownian motion documentation
- **Emotional complexity**: CPTSD-influenced cognitive terrain mapping
- **Scale**: 1,200+ files requiring intelligent, not manual, processing

## 🎬 Current Thread Progress & Handoff State

### Latest Accomplishments (Current Session)
- **GitHub raw URL workflow established**: Direct file access via `https://github.com/fibrewchannel/flatdrop-api/raw/refs/heads/main/code/app/[filename]`
- **Configuration sprawl identified**: Analyzed `single_file_tester.py` revealing hardcoded patterns, weights, coordinate logic, and folder mappings
- **Agent specification alignment confirmed**: Existing `injektor.tesseract` spec matches current implementation perfectly
- **Single-value coordinate decision finalized**: No mud tracking across dimensions - one value per axis
- **Memoir density breakthrough**: Shadowcast analysis revealed "trauma of being summarized" as crystallized universal experience

### Architecture Decisions Made
- **"Configuration should be data, not code"** - Rick's core principle for system design
- **YAML-driven configuration system** to replace scattered hardcoded values
- **Runtime configuration updates** via API endpoints for memoir voice evolution
- **Content pattern weights adjustable** without code changes

### Critical Context for Next Thread
- **1,237 files successfully processed** in Phases 1 & 2 with zero data loss
- **Housing instability timeline** driving memoir production urgency
- **Recovery foundation**: help-addict → tell-story → prevent-death-poverty priority hierarchy
- **Tesseract coordinates working**: shadowcast:narrative:tell-story:complex format proven effective

## 🎬 Next Actions (Phase 3 Immediate)

1. **Create TesseractConfig system** with YAML-based configuration
2. **Extract hardcoded patterns** from single_file_tester.py
3. **Refactor coordinate assignment** to use config-driven logic
4. **Add config management endpoints** for runtime tuning
5. **Test memoir detection accuracy** with adjustable weights

### Files Ready for Configuration Extraction
- `single_file_tester.py`: Content patterns (lines 22-30), quality weights (83-98), coordinate logic (125-170), folder mapping (190-220)
- `utils.py`: Tesseract coordinate functions need config integration
- `routes.py`: API endpoints need centralized logic

### Collaboration Handoff Instructions
If continuing in new thread, share:
1. This updated master instructions document
2. Current GitHub raw URL for any modified files
3. Specific configuration extraction focus area
4. Reference to Rick's memoir priorities and housing timeline context

## 🌟 Revolutionary Impact

This isn't just file organization - it's **organizing meaning** across the four dimensions of human experience. The Tesseract system transforms the chaotic Flatline Codex into a **navigable map of consciousness** that serves both daily survival and memoir production.

The configuration consolidation ensures the system can evolve with Rick's memoir voice, allowing pattern weights and detection rules to be tuned as the narrative develops, without requiring code changes.

**The Flatdrop API is becoming a cognitive coordinate system for lived experience with adaptive intelligence.**

=====
