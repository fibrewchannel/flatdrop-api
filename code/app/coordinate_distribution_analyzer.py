#!/usr/bin/env python3
"""
Coordinate Distribution Analyzer
Shows breakdown of chunks by tesseract coordinates
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any
import re

# CONFIGURATION
VAULT_PATH = Path("/Users/rickshangle/Vaults/flatline-codex")

class CoordinateAnalyzer:
    """Analyze distribution of chunks across tesseract coordinates"""
    
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.content_folders = [
            "memoir",
            "recovery", 
            "creative",
            "survival",
            "work-amends",
            "_review/promising",
            "_review/borderline"
        ]
    
    def extract_yaml_field(self, yaml_text: str, field: str) -> str:
        """Extract single field from YAML text"""
        pattern = f'{field}:\\s*(.+)'
        match = re.search(pattern, yaml_text)
        return match.group(1).strip() if match else None
    
    def extract_yaml_list(self, yaml_text: str, field: str) -> List[str]:
        """Extract list field from YAML text"""
        pattern = f'{field}:\\s*'
        match = re.search(pattern, yaml_text)
        if not match:
            return []
        
        start_pos = match.end()
        lines = yaml_text[start_pos:].split('\n')
        items = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('- '):
                items.append(line[2:].strip())
            elif line and not line.startswith('#'):
                break
        
        return items
    
    def load_chunk_metadata(self, chunk_path: Path) -> Dict[str, Any]:
        """Extract metadata from chunk file"""
        try:
            content = chunk_path.read_text(encoding='utf-8')
            
            if not content.startswith('---'):
                return None
            
            yaml_end = content.find('---', 3)
            if yaml_end == -1:
                return None
            
            yaml_content = content[3:yaml_end]
            body_content = content[yaml_end + 3:].strip()
            
            metadata = {
                'file_path': str(chunk_path.relative_to(self.vault_path)),
                'chunk_id': self.extract_yaml_field(yaml_content, 'chunk_id'),
                'quality_score': float(self.extract_yaml_field(yaml_content, 'quality_score') or 0),
                'disposition': self.extract_yaml_field(yaml_content, 'disposition'),
                'tags': self.extract_yaml_list(yaml_content, 'tags'),
                'theme': self.extract_yaml_field(yaml_content, 'theme'),
                'word_count': len(body_content.split()),
                'folder': chunk_path.parent.name
            }
            
            # Extract coordinates from tags
            coords = {}
            for tag in metadata['tags']:
                if '/' in tag:
                    dim, val = tag.split('/', 1)
                    coords[dim] = val
            
            # Build coordinate key
            coord_key = ':'.join([
                coords.get('x-structure', 'unknown'),
                coords.get('y-transmission', 'unknown'),
                coords.get('z-purpose', 'unknown'),
                coords.get('w-terrain', 'unknown')
            ])
            
            metadata['coordinates'] = coords
            metadata['coordinate_key'] = coord_key
            
            return metadata
            
        except Exception as e:
            print(f"Error loading {chunk_path}: {e}")
            return None
    
    def analyze_distribution(self) -> Dict[str, Any]:
        """Analyze chunk distribution across coordinates"""
        
        print("Loading chunks...")
        all_chunks = []
        
        for folder in self.content_folders:
            folder_path = self.vault_path / folder
            if not folder_path.exists():
                continue
            
            for chunk_file in folder_path.rglob("*.md"):
                metadata = self.load_chunk_metadata(chunk_file)
                if metadata:
                    all_chunks.append(metadata)
        
        print(f"Loaded {len(all_chunks)} chunks")
        
        # Group by coordinate key
        coord_groups = defaultdict(lambda: {
            'chunks': [],
            'quality_scores': [],
            'themes': [],
            'word_counts': [],
            'folders': []
        })
        
        for chunk in all_chunks:
            key = chunk['coordinate_key']
            coord_groups[key]['chunks'].append(chunk['chunk_id'])
            coord_groups[key]['quality_scores'].append(chunk['quality_score'])
            coord_groups[key]['themes'].append(chunk['theme'])
            coord_groups[key]['word_counts'].append(chunk['word_count'])
            coord_groups[key]['folders'].append(chunk['folder'])
        
        # Calculate statistics for each coordinate
        distributions = []
        for coord_key, data in coord_groups.items():
            x, y, z, w = coord_key.split(':')
            
            quality_scores = data['quality_scores']
            word_counts = data['word_counts']
            
            # Get top themes
            theme_counts = {}
            for theme in data['themes']:
                theme_counts[theme] = theme_counts.get(theme, 0) + 1
            top_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # Get folder distribution
            folder_counts = {}
            for folder in data['folders']:
                folder_counts[folder] = folder_counts.get(folder, 0) + 1
            
            distributions.append({
                'coordinate_key': coord_key,
                'x_structure': x,
                'y_transmission': y,
                'z_purpose': z,
                'w_terrain': w,
                'chunk_count': len(data['chunks']),
                'total_words': sum(word_counts),
                'avg_words': sum(word_counts) / len(word_counts) if word_counts else 0,
                'min_quality': min(quality_scores) if quality_scores else 0,
                'avg_quality': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
                'max_quality': max(quality_scores) if quality_scores else 0,
                'top_themes': [{'theme': t, 'count': c} for t, c in top_themes],
                'folder_distribution': folder_counts,
                'sample_chunks': data['chunks'][:5]
            })
        
        # Sort by chunk count descending
        distributions.sort(key=lambda x: x['chunk_count'], reverse=True)
        
        # Calculate dimension totals
        z_purpose_totals = defaultdict(int)
        x_structure_totals = defaultdict(int)
        w_terrain_totals = defaultdict(int)
        
        for dist in distributions:
            z_purpose_totals[dist['z_purpose']] += dist['chunk_count']
            x_structure_totals[dist['x_structure']] += dist['chunk_count']
            w_terrain_totals[dist['w_terrain']] += dist['chunk_count']
        
        return {
            'total_chunks': len(all_chunks),
            'unique_coordinates': len(distributions),
            'coordinate_distributions': distributions,
            'dimension_totals': {
                'z_purpose': dict(sorted(z_purpose_totals.items(), key=lambda x: x[1], reverse=True)),
                'x_structure': dict(sorted(x_structure_totals.items(), key=lambda x: x[1], reverse=True)),
                'w_terrain': dict(sorted(w_terrain_totals.items(), key=lambda x: x[1], reverse=True))
            }
        }
    
    def save_report(self, analysis: Dict[str, Any], output_file: Path):
        """Save analysis as JSON"""
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"\nReport saved: {output_file}")
    
    def print_summary(self, analysis: Dict[str, Any]):
        """Print human-readable summary"""
        print("\n" + "=" * 80)
        print("COORDINATE DISTRIBUTION ANALYSIS")
        print("=" * 80)
        
        print(f"\nTotal chunks: {analysis['total_chunks']}")
        print(f"Unique coordinate combinations: {analysis['unique_coordinates']}")
        
        print("\n" + "-" * 80)
        print("TOP COORDINATE COMBINATIONS (by chunk count)")
        print("-" * 80)
        
        for i, dist in enumerate(analysis['coordinate_distributions'][:15], 1):
            print(f"\n{i}. {dist['coordinate_key']}")
            print(f"   Chunks: {dist['chunk_count']}")
            print(f"   Words: {dist['total_words']:,} (avg {dist['avg_words']:.0f} per chunk)")
            print(f"   Quality: {dist['min_quality']:.1f} - {dist['max_quality']:.1f} (avg {dist['avg_quality']:.1f})")
            print(f"   Top themes: {', '.join(t['theme'] or 'unknown' for t in dist['top_themes'])}")
            print(f"   Folders: {', '.join(f'{k}({v})' for k, v in sorted(dist['folder_distribution'].items(), key=lambda x: x[1], reverse=True))}")
        
        print("\n" + "-" * 80)
        print("DIMENSION TOTALS")
        print("-" * 80)
        
        print("\nZ-Purpose (memoir intent):")
        for purpose, count in analysis['dimension_totals']['z_purpose'].items():
            pct = (count / analysis['total_chunks']) * 100
            print(f"  {purpose:30s} {count:4d} ({pct:5.1f}%)")
        
        print("\nX-Structure (narrative form):")
        for structure, count in list(analysis['dimension_totals']['x_structure'].items())[:10]:
            pct = (count / analysis['total_chunks']) * 100
            print(f"  {structure:30s} {count:4d} ({pct:5.1f}%)")
        
        print("\nW-Terrain (cognitive complexity):")
        for terrain, count in analysis['dimension_totals']['w_terrain'].items():
            pct = (count / analysis['total_chunks']) * 100
            print(f"  {terrain:30s} {count:4d} ({pct:5.1f}%)")

def main():
    """Run coordinate distribution analysis"""
    
    analyzer = CoordinateAnalyzer(VAULT_PATH)
    analysis = analyzer.analyze_distribution()
    
    # Print summary
    analyzer.print_summary(analysis)
    
    # Save detailed report
    output_file = VAULT_PATH / "_relocation_logs" / "coordinate_distribution.json"
    analyzer.save_report(analysis, output_file)
    
    print(f"\n" + "=" * 80)
    print("Full report saved to:")
    print(f"  {output_file}")
    print("=" * 80)

if __name__ == "__main__":
    main()
