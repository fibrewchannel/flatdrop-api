# _inload Processing Runbook
**Tesseract-Native Content Classification and Consolidation System**

## Overview

This runbook systematizes the process of extracting valuable content from chaotic import folders (_inload) using content-based search patterns, sample analysis, and Tesseract coordinate classification.

**Key Insight**: Filename-based searches miss 90%+ of relevant content. Content-based grep searches reveal the actual material inside files.

## Prerequisites

- Functional Tesseract vault structure with organized threads:
  - `recovery/` (activations, practices, explorations, personas)
  - `memoir/spine/` (foundations, crisis, recovery, integration, fragments)
  - `work-amends/` (job-search, skills, planning)
  - `contribution/` (creative, systems, philosophy)

## Phase 1: Content Discovery Scripts

### 1.1 Basic Content Search Script

```bash
#!/bin/bash
# content_search.sh

OUT_DIR="search_results"
mkdir -p $OUT_DIR

# Recovery content search
grep -l -i "recovery\|sobriety\|AA\|twelve step\|sponsor\|meeting\|step work" _inload/*.md > $OUT_DIR/recovery_content_files.txt

# Job/work content search  
grep -l -i "job\|interview\|resume\|employment\|career\|salary\|work" _inload/*.md > $OUT_DIR/job_content_files.txt

# Memoir/narrative content search
grep -l -i "story\|memoir\|childhood\|remember\|years ago\|when I was" _inload/*.md > $OUT_DIR/memoir_content_files.txt

# Tesseract coordinate content search
grep -l "archetype\|protocol\|shadowcast\|summoning\|expansion" _inload/*.md > $OUT_DIR/tesseract_content_files.txt

echo "Content search complete. Results in $OUT_DIR/"
echo "Recovery files: $(wc -l < $OUT_DIR/recovery_content_files.txt)"
echo "Job files: $(wc -l < $OUT_DIR/job_content_files.txt)" 
echo "Memoir files: $(wc -l < $OUT_DIR/memoir_content_files.txt)"
echo "Tesseract files: $(wc -l < $OUT_DIR/tesseract_content_files.txt)"
```

### 1.2 Extended Content Search Script

```bash
#!/bin/bash
# extended_content_search.sh

OUT_DIR="search_results"
mkdir -p $OUT_DIR

# Medical/health content
grep -l -i "mayo\|doctor\|medical\|health\|cirrhosis\|therapy" _inload/*.md > $OUT_DIR/medical_content_files.txt

# AI collaboration content
grep -l -i "nyx\|chatgpt\|AI\|prompt\|LLM\|assistant" _inload/*.md > $OUT_DIR/ai_content_files.txt

# Personal narrative content
grep -l -i "I remember\|my father\|my mother\|childhood\|growing up" _inload/*.md > $OUT_DIR/personal_narrative_files.txt

# Technical/systems content
grep -l -i "API\|code\|system\|protocol\|infrastructure\|server" _inload/*.md > $OUT_DIR/technical_content_files.txt

# Creative content
grep -l -i "art\|music\|creative\|image\|draw\|design" _inload/*.md > $OUT_DIR/creative_content_files.txt

echo "Extended search complete. Results in $OUT_DIR/"
```

## Phase 2: Sample Analysis 

### 2.1 Strategic Content Sampling Script

```bash
#!/bin/bash
# extract_samples.sh

OUT=content_samples.txt
> $OUT

# Function to add file content with clear delimiters
dump_file() {
    local file="$1"
    echo "========================================" >> $OUT
    echo "FILE: $file" >> $OUT
    echo "========================================" >> $OUT
    if [ -f "$file" ]; then
        cat "$file" >> $OUT
    else
        echo "FILE NOT FOUND: $file" >> $OUT
    fi
    echo "" >> $OUT
    echo "" >> $OUT
}

# Sample multi-category files (appear in 3+ search results)
echo "Extracting multi-category files..."

# Extract top 3 files from each category for analysis
head -3 search_results/recovery_content_files.txt | while read file; do dump_file "$file"; done
head -3 search_results/job_content_files.txt | while read file; do dump_file "$file"; done
head -3 search_results/memoir_content_files.txt | while read file; do dump_file "$file"; done

echo "Content extraction complete. Output in $OUT"
echo "File count: $(grep -c "^FILE:" $OUT)"
```

### 2.2 Manual Sample Selection

For targeted analysis, manually select high-value files:
- Files appearing in multiple search results (multi-dimensional content)
- Recent files (likely higher quality)
- Files with descriptive names suggesting memoir value
- Large files (substantial content)

## Phase 3: Content Classification Analysis

### 3.1 Analysis Questions

For each sampled file, determine:

1. **Primary Content Type**: Recovery, memoir, job search, technical, creative
2. **Quality Assessment**: High-value vs processing notes vs duplicates
3. **Tesseract Coordinates**: Structure, transmission, purpose, cognitive terrain
4. **Consolidation Target**: Which vault thread should contain this content
5. **Processing Priority**: Immediate, next batch, or archive

### 3.2 Classification Decision Matrix

| Content Characteristics | Target Thread | Priority |
|-------------------------|---------------|----------|
| Job applications, resumes, cover letters | `work-amends/job-search/` | Immediate |
| Recovery processing, step work, meetings | `recovery/explorations/` | High |
| Personal narratives, life stories | `memoir/spine/` (by cognitive terrain) | High |
| Technical documentation, APIs | `contribution/systems/` | Medium |
| Creative work, art, music | `contribution/creative/` | Medium |
| Medical/therapy content | `recovery/explorations/` or `survival/medical/` | Medium |
| Duplicates, low-quality notes | Archive or delete | Low |

## Phase 4: Consolidation Execution

### 4.1 High-Priority Consolidation Script

```bash
#!/bin/bash
# consolidate_priority_content.sh

# Create staging areas
mkdir -p _tesseract-staging/{work-amends,recovery,memoir,contribution}

# Move high-priority job content
echo "Consolidating job search content..."
while read file; do
    if [[ "$file" == *mayo* ]] || [[ "$file" == *resume* ]] || [[ "$file" == *cover*letter* ]]; then
        mv "$file" _tesseract-staging/work-amends/
        echo "Moved: $file -> work-amends"
    fi
done < search_results/job_content_files.txt

# Move obvious recovery content  
echo "Consolidating recovery content..."
while read file; do
    if [[ "$file" == *recovery* ]] || [[ "$file" == *aa_* ]] || [[ "$file" == *meeting* ]]; then
        mv "$file" _tesseract-staging/recovery/
        echo "Moved: $file -> recovery"
    fi
done < search_results/recovery_content_files.txt

echo "Priority consolidation complete. Review staging areas before final moves."
```

### 4.2 Final Integration Script

```bash
#!/bin/bash
# integrate_staged_content.sh

# Move from staging to final locations
echo "Moving staged content to final threads..."

# Work-amends content
if [ -d "_tesseract-staging/work-amends" ]; then
    mv _tesseract-staging/work-amends/* work-amends/job-search/
    echo "Integrated work-amends content"
fi

# Recovery content  
if [ -d "_tesseract-staging/recovery" ]; then
    mv _tesseract-staging/recovery/* recovery/explorations/
    echo "Integrated recovery content"
fi

# Clean up staging
rmdir _tesseract-staging/* 2>/dev/null
rmdir _tesseract-staging 2>/dev/null

echo "Integration complete."
```

## Phase 5: Quality Assurance

### 5.1 Post-Processing Validation

```bash
#!/bin/bash
# validate_processing.sh

echo "=== Processing Validation ==="

# Count processed files
PROCESSED=$(find _tesseract-staging/ work-amends/ recovery/ memoir/ contribution/ -name "*.md" -newer search_results/ 2>/dev/null | wc -l)
REMAINING=$(find _inload/ -name "*.md" | wc -l)

echo "Files processed this round: $PROCESSED"
echo "Files remaining in _inload: $REMAINING"

# Check for obvious misclassifications
echo ""
echo "=== Potential Misclassifications ==="
grep -l "recovery\|AA" work-amends/**/*.md 2>/dev/null && echo "Recovery content found in work-amends"
grep -l "job\|resume" recovery/**/*.md 2>/dev/null && echo "Job content found in recovery"

# Update Tesseract coordinates
echo ""
echo "Recommend running: curl -X POST http://localhost:5050/api/tesseract/extract-coordinates"
```

## Processing Guidelines

### Content Quality Indicators

**High-Value Content:**
- Personal narratives with emotional depth
- Professional job application materials
- Recovery processing with insights
- Technical documentation with reusable value
- Creative work with artistic merit

**Low-Value Content:**
- Duplicate exports
- Fragment processing notes
- Incomplete drafts
- System-generated metadata
- Outdated technical references

### Cognitive Terrain Classification

For memoir content specifically:

- **Foundations (complex)**: Deep emotional processing, foundational memories, complex relationships
- **Crisis (chaotic)**: Trauma, medical emergencies, addiction episodes, major disruptions  
- **Recovery (complicated)**: Structured recovery work, step processes, systematic healing
- **Integration (obvious)**: Clear insights, lessons learned, wisdom gained, stable perspectives
- **Fragments (confused)**: Unclear states, mixed emotions, processing in progress

### Safety Protocols

1. **Always backup before processing**: Create dated backup of _inload folder
2. **Use staging areas**: Never move directly to final locations without review
3. **Validate moves**: Check that content matches destination thread purpose
4. **Update coordinates**: Re-run Tesseract analysis after major consolidations
5. **Document decisions**: Note why content was classified in specific ways

## Iterative Processing Strategy

### Round-Based Approach

**Round 1**: High-value, obvious content (job applications, clear recovery material)
**Round 2**: Memoir content with clear narrative structure  
**Round 3**: Technical and creative content consolidation
**Round 4**: Threaddump and mixed content analysis
**Round 5**: Archive or delete low-value remaining content

### Success Metrics

- **Reduced _inload chaos**: Decrease file count from 370+ to manageable number
- **Increased thread coherence**: Content properly aligned with thread purposes
- **Improved findability**: Important content moved to logical locations
- **Enhanced memoir readiness**: Narrative content organized by cognitive terrain
- **Crisis preparedness**: Critical job/medical content easily accessible

## Maintenance

### Regular Processing Schedule

- **Weekly**: Quick scan for new _inload content requiring immediate action
- **Monthly**: Full content search and sample analysis for accumulated imports
- **Quarterly**: Comprehensive _inload clearance and thread optimization

### Evolution Indicators

The process should be refined when:
- Search patterns miss significant content types
- Classification accuracy drops below 80%
- Processing time exceeds available time slots
- Thread organization no longer serves user needs

This runbook captures the Tesseract-native approach to content classification: meaning-based organization that serves both daily survival and memoir production while maintaining system coherence across multiple life threads.