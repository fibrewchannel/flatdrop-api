#!/usr/bin/env python3
"""
Single File Content Mining Tester
Test the content fingerprinting system on one file
"""

import re
import json
from pathlib import Path
import sys

def extract_content_signature(file_path):
    """Generate content fingerprint for a single file"""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        
        # Basic metrics
        word_count = len(content.split())
        line_count = len(content.splitlines())
        char_count = len(content)
        
        # Content pattern detection
        patterns = {
            'memoir_markers': len(re.findall(r'\b(I remember|years ago|childhood|growing up|my father|my mother|when I was)\b', content, re.I)),
            'recovery_markers': len(re.findall(r'\b(AA|recovery|sobriety|step work|sponsor|meeting|clean time|twelve steps?)\b', content, re.I)),
            'job_markers': len(re.findall(r'\b(interview|resume|job|employment|salary|work|career|application|hire|employer)\b', content, re.I)),
            'ai_markers': len(re.findall(r'\b(nyx|chatgpt|AI|prompt|assistant|LLM|claude|gpt)\b', content, re.I)),
            'medical_markers': len(re.findall(r'\b(mayo|doctor|medical|therapy|health|cirrhosis|treatment|hospital|clinic)\b', content, re.I)),
            'technical_markers': len(re.findall(r'\b(API|code|system|database|server|function|class|script|programming)\b', content, re.I)),
            'creative_markers': len(re.findall(r'\b(art|music|draw|design|image|creative|story|poem|paint|sketch)\b', content, re.I)),
            'emotional_markers': len(re.findall(r'\b(fear|anxiety|depression|trauma|anger|grief|pain|joy|love|hope)\b', content, re.I))
        }
        
        # Tesseract coordinate hints
        tesseract_hints = {
            'structure_hints': len(re.findall(r'\b(archetype|protocol|shadowcast|expansion|summoning)\b', content, re.I)),
            'purpose_hints': len(re.findall(r'\b(tell.story|help.addict|prevent.death|financial.amends|help.world)\b', content, re.I)),
            'transmission_hints': len(re.findall(r'\b(narrative|text|image|tarot|invocation)\b', content, re.I))
        }
        
        # Advanced content analysis
        advanced_patterns = {
            'first_person_pronouns': len(re.findall(r'\b(I|me|my|mine|myself)\b', content)),
            'temporal_markers': len(re.findall(r'\b(yesterday|today|tomorrow|last week|next month|ago|years old|in \d{4})\b', content, re.I)),
            'dialogue_markers': len(re.findall(r'"[^"]*"', content)),
            'dates': len(re.findall(r'\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{4}\b', content)),
            'urls': len(re.findall(r'https?://[^\s]+', content)),
            'code_blocks': len(re.findall(r'```[\s\S]*?```', content)),
            'yaml_frontmatter': 1 if content.strip().startswith('---') else 0
        }
        
        # Quality scoring
        quality_score = calculate_quality_score(content, patterns, word_count)
        
        # Theme identification
        dominant_theme = identify_dominant_theme(patterns)
        
        # Suggested Tesseract coordinates
        suggested_coordinates = suggest_tesseract_coordinates(patterns, content)
        
        return {
            'file_path': str(file_path),
            'basic_metrics': {
                'word_count': word_count,
                'line_count': line_count,
                'char_count': char_count
            },
            'content_patterns': patterns,
            'tesseract_hints': tesseract_hints,
            'advanced_patterns': advanced_patterns,
            'quality_score': quality_score,
            'dominant_theme': dominant_theme,
            'suggested_coordinates': suggested_coordinates,
            'content_preview': content[:300] + "..." if len(content) > 300 else content
        }
        
    except Exception as e:
        return {'file_path': str(file_path), 'error': str(e)}

def calculate_quality_score(content, patterns, word_count):
    """Score content quality for memoir/survival relevance"""
    score = 0
    
    # Base score from length (meaningful content)
    if word_count > 1000: score += 4
    elif word_count > 500: score += 3
    elif word_count > 200: score += 2
    elif word_count > 50: score += 1
    
    # High-value pattern bonuses
    score += patterns['memoir_markers'] * 3
    score += patterns['recovery_markers'] * 2.5
    score += patterns['job_markers'] * 2
    score += patterns['medical_markers'] * 1.5
    score += patterns['ai_markers'] * 1
    score += patterns['emotional_markers'] * 0.5
    
    # Penalty for pure technical/system content with no personal content
    if patterns['technical_markers'] > 10 and patterns['memoir_markers'] == 0 and patterns['emotional_markers'] == 0:
        score -= 3
        
    # Bonus for narrative indicators
    first_person_count = len(re.findall(r'\b(I|me|my)\b', content))
    if first_person_count > 20:
        score += 2
    elif first_person_count > 10:
        score += 1
        
    return round(max(0, score), 1)

def identify_dominant_theme(patterns):
    """Identify the strongest content theme"""
    theme_scores = {
        'memoir': patterns['memoir_markers'] * 3,
        'recovery': patterns['recovery_markers'] * 2.5,
        'survival': patterns['job_markers'] + patterns['medical_markers'],
        'ai_collaboration': patterns['ai_markers'],
        'technical': patterns['technical_markers'],
        'creative': patterns['creative_markers'],
        'emotional': patterns['emotional_markers']
    }
    
    if max(theme_scores.values()) == 0:
        return 'unclear'
    
    return max(theme_scores, key=theme_scores.get)

def suggest_tesseract_coordinates(patterns, content):
    """Suggest appropriate Tesseract coordinates based on content analysis"""
    
    # Suggest Structure (X-axis)
    if patterns['memoir_markers'] > 2:
        structure = 'shadowcast'  # Emotional exploration
    elif patterns['recovery_markers'] > 2:
        structure = 'protocol'   # Structured practices
    elif patterns['creative_markers'] > 2:
        structure = 'expansion'  # Creative context
    elif patterns['ai_markers'] > 3:
        structure = 'summoning'  # Invoking assistance
    else:
        structure = 'archetype'  # Identity/persona work
    
    # Suggest Transmission (Y-axis)
    first_person = len(re.findall(r'\b(I|me|my)\b', content))
    has_dialogue = len(re.findall(r'"[^"]*"', content)) > 0
    
    if first_person > 20 or patterns['memoir_markers'] > 1:
        transmission = 'narrative'
    elif patterns['creative_markers'] > 2 or 'image' in content.lower():
        transmission = 'image'
    elif has_dialogue or patterns['recovery_markers'] > 2:
        transmission = 'invocation'
    elif patterns['ai_markers'] > 2:
        transmission = 'text'
    else:
        transmission = 'text'
    
    # Suggest Purpose (Z-axis)
    if patterns['memoir_markers'] > 1 or first_person > 15:
        purpose = 'tell-story'
    elif patterns['recovery_markers'] > 1:
        purpose = 'help-addict'
    elif patterns['job_markers'] > 1 or patterns['medical_markers'] > 1:
        purpose = 'prevent-death-poverty'
    elif patterns['creative_markers'] > 2:
        purpose = 'help-world'
    else:
        purpose = 'help-addict'  # Default for unclear content
    
    # Suggest Cognitive Terrain (W-axis)
    if patterns['emotional_markers'] > 5:
        terrain = 'chaotic'
    elif patterns['technical_markers'] > 5:
        terrain = 'complicated'
    elif patterns['memoir_markers'] > 2 or first_person > 20:
        terrain = 'complex'
    else:
        terrain = 'obvious'
    
    return {
        'x_structure': structure,
        'y_transmission': transmission,
        'z_purpose': purpose,
        'w_terrain': terrain,
        'tesseract_key': f"{structure}:{transmission}:{purpose}:{terrain}"
    }

def suggest_destination_folder(coordinates, theme, quality):
    """Suggest where this file should be moved in the Tesseract structure"""
    purpose = coordinates['z_purpose']
    structure = coordinates['x_structure']
    
    if purpose == 'tell-story':
        if structure == 'shadowcast':
            return 'memoir/explorations/'
        elif structure == 'protocol':
            return 'memoir/practices/'
        elif structure == 'archetype':
            return 'memoir/personas/'
        else:
            return 'memoir/spine/foundations/'
    
    elif purpose == 'help-addict':
        if structure == 'protocol':
            return 'recovery/practices/'
        elif structure == 'archetype':
            return 'recovery/personas/'
        elif structure == 'shadowcast':
            return 'recovery/explorations/'
        else:
            return 'recovery/activations/'
    
    elif purpose == 'prevent-death-poverty':
        if theme == 'survival' and quality > 3:
            return 'survival/medical/' if 'medical' in theme else 'survival/housing/'
        else:
            return 'survival/systems/'
    
    elif purpose == 'financial-amends':
        if structure == 'protocol':
            return 'work-amends/practices/'
        elif structure == 'archetype':
            return 'work-amends/personas/'
        else:
            return 'work-amends/job-search/'
    
    elif purpose == 'help-world':
        if structure == 'expansion':
            return 'contribution/context/'
        elif theme == 'creative':
            return 'contribution/creative/'
        else:
            return 'contribution/systems/'
    
    else:
        return '_tesseract-inbox/needs-classification/'

def print_analysis_report(signature):
    """Print a human-readable analysis report"""
    print("=" * 60)
    print(f"CONTENT ANALYSIS: {Path(signature['file_path']).name}")
    print("=" * 60)
    
    if 'error' in signature:
        print(f"❌ ERROR: {signature['error']}")
        return
    
    metrics = signature['basic_metrics']
    patterns = signature['content_patterns']
    coords = signature['suggested_coordinates']
    
    print(f"\n📊 BASIC METRICS")
    print(f"  Words: {metrics['word_count']:,}")
    print(f"  Lines: {metrics['line_count']:,}")
    print(f"  Characters: {metrics['char_count']:,}")
    
    print(f"\n🎯 QUALITY & THEME")
    print(f"  Quality Score: {signature['quality_score']}/10")
    print(f"  Dominant Theme: {signature['dominant_theme']}")
    
    print(f"\n🔍 CONTENT PATTERNS")
    for pattern, count in patterns.items():
        if count > 0:
            print(f"  {pattern.replace('_', ' ').title()}: {count}")
    
    print(f"\n🎲 TESSERACT COORDINATES")
    print(f"  Structure (X): {coords['x_structure']}")
    print(f"  Transmission (Y): {coords['y_transmission']}")
    print(f"  Purpose (Z): {coords['z_purpose']}")
    print(f"  Terrain (W): {coords['w_terrain']}")
    print(f"  Key: {coords['tesseract_key']}")
    
    # Suggest destination
    destination = suggest_destination_folder(coords, signature['dominant_theme'], signature['quality_score'])
    print(f"\n📁 SUGGESTED DESTINATION")
    print(f"  {destination}")
    
    print(f"\n📝 CONTENT PREVIEW")
    print(f"  {signature['content_preview']}")
    
    print("\n" + "=" * 60)

def main():
    if len(sys.argv) != 2:
        print("Usage: python single_file_tester.py <path_to_md_file>")
        print("\nExample test files from your shadowcasts:")
        print("  shadowcasts/shadowcast_erased-momentum.md")
        print("  shadowcasts/shadowcast_story-hoarder.md")
        print("  shadowcasts/shadowcast_recovery-cost-invisibility.md")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    if not file_path.suffix == '.md':
        print(f"❌ File must be a .md file: {file_path}")
        sys.exit(1)
    
    print(f"🔍 Analyzing: {file_path}")
    
    # Extract content signature
    signature = extract_content_signature(file_path)
    
    # Print analysis report
    print_analysis_report(signature)
    
    # Export JSON for further analysis
    json_output = file_path.parent / f"{file_path.stem}_analysis.json"
    with open(json_output, 'w') as f:
        json.dump(signature, f, indent=2)
    
    print(f"\n💾 Detailed analysis saved to: {json_output}")

if __name__ == "__main__":
    main()
