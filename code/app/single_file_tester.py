#!/usr/bin/env python3
"""
Single File Content Mining Tester - Config-Driven Version
Test the content fingerprinting system on one file using TesseractConfig
"""

import re
import json
from pathlib import Path
import sys
from tesseract_config import get_analyzer, get_config

def extract_content_signature(file_path):
    """Generate content fingerprint for a single file using configuration"""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        analyzer = get_analyzer()
        
        # Basic metrics
        word_count = len(content.split())
        line_count = len(content.splitlines())
        char_count = len(content)
        
        # Content pattern detection using config
        patterns = analyzer.extract_content_patterns(content)
        
        # Tesseract coordinate hints using config
        config = get_config()
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
        
        # Quality scoring using config
        quality_score = analyzer.calculate_quality_score(content, patterns, word_count)
        
        # Theme identification using config
        dominant_theme = analyzer.identify_dominant_theme(patterns)
        
        # Suggested Tesseract coordinates using config
        suggested_coordinates = analyzer.suggest_tesseract_coordinates(patterns, content)
        
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
    
    # Suggest destination using config
    analyzer = get_analyzer()
    destination = analyzer.suggest_destination_folder(coords, signature['dominant_theme'], signature['quality_score'])
    print(f"\n📁 SUGGESTED DESTINATION")
    print(f"  {destination}")
    
    print(f"\n📝 CONTENT PREVIEW")
    print(f"  {signature['content_preview']}")
    
    # Show current configuration summary
    config = get_config()
    patterns_config = config.get_content_patterns()
    print(f"\n⚙️ CONFIGURATION STATUS")
    print(f"  Active patterns: {len(patterns_config)}")
    print(f"  Config file: {config.config_file}")
    print(f"  Memoir weight: {patterns_config['memoir_markers']['weight']}")
    print(f"  Recovery weight: {patterns_config['recovery_markers']['weight']}")
    
    print("\n" + "=" * 60)

def show_config_summary():
    """Display current configuration summary"""
    config = get_config()
    
    print("\n" + "=" * 60)
    print("TESSERACT CONFIGURATION SUMMARY")
    print("=" * 60)
    
    # Content patterns
    patterns = config.get_content_patterns()
    print(f"\n📝 CONTENT PATTERNS ({len(patterns)} active)")
    for name, pattern_config in patterns.items():
        weight = pattern_config['weight']
        print(f"  {name}: weight={weight}")
    
    # Quality config
    quality_config = config.get_quality_config()
    print(f"\n⚖️ QUALITY SCORING")
    print(f"  Length bonuses: {len(quality_config['length_bonuses'])} tiers")
    print(f"  Pattern multipliers: {len(quality_config['pattern_multipliers'])} patterns")
    print(f"  First-person thresholds: high={quality_config['first_person_thresholds']['high']}, medium={quality_config['first_person_thresholds']['medium']}")
    
    # Coordinate rules
    coord_rules = config.get_coordinate_rules()
    print(f"\n🎲 COORDINATE ASSIGNMENT")
    print(f"  Structure rules: {len(coord_rules['structure_thresholds'])}")
    print(f"  Transmission rules: {len(coord_rules['transmission_thresholds'])}")
    print(f"  Purpose rules: {len(coord_rules['purpose_thresholds'])}")
    print(f"  Terrain rules: {len(coord_rules['terrain_thresholds'])}")
    
    # Folder structure
    folder_config = config.get_folder_structure()
    purposes = [key for key in folder_config.keys() if key != 'inbox']
    print(f"\n📁 FOLDER STRUCTURE")
    print(f"  Purpose mappings: {len(purposes)}")
    print(f"  Purposes: {', '.join(purposes)}")
    
    print(f"\n📄 Configuration file: {config.config_file}")
    print("=" * 60)

def main():
    if len(sys.argv) < 2:
        print("Usage: python single_file_tester.py <path_to_md_file> [--config]")
        print("\nOptions:")
        print("  --config    Show configuration summary and exit")
        print("\nExample test files from your shadowcasts:")
        print("  shadowcasts/shadowcast_erased-momentum.md")
        print("  shadowcasts/shadowcast_story-hoarder.md")
        print("  shadowcasts/shadowcast_recovery-cost-invisibility.md")
        sys.exit(1)
    
    # Handle config display option
    if '--config' in sys.argv:
        show_config_summary()
        sys.exit(0)
    
    file_path = Path(sys.argv[1])
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    if not file_path.suffix == '.md':
        print(f"❌ File must be a .md file: {file_path}")
        sys.exit(1)
    
    print(f"🔍 Analyzing: {file_path}")
    print(f"📋 Using configuration-driven analysis")
    
    # Extract content signature using config
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
