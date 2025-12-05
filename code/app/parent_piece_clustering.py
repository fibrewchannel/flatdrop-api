#!/usr/bin/env python3
"""
Parent Piece Clustering System
Analyzes memoir-grade chunks and suggests natural chapter groupings
"""

import json
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Any, Set
from datetime import datetime
import re

# CONFIGURATION
VAULT_PATH = Path("/Users/rickshangle/Vaults/flatline-codex")
OUTPUT_DIR = VAULT_PATH / "_relocation_logs"

class ParentPieceClusterer:
    """Suggests chapter/piece groupings for memoir-grade chunks"""
    
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.memoir_folders = [
            "memoir",
            "recovery", 
            "creative",
            "survival",
            "work-amends"
        ]
        
    def load_chunk_metadata(self, chunk_path: Path) -> Dict[str, Any]:
        """Extract metadata from chunk file"""
        try:
            content = chunk_path.read_text(encoding='utf-8')
            
            # Parse YAML frontmatter
            if not content.startswith('---'):
                return None
            
            yaml_end = content.find('---', 3)
            if yaml_end == -1:
                return None
            
            yaml_content = content[3:yaml_end]
            body_content = content[yaml_end + 3:].strip()
            
            # Extract key fields (simple parsing, not full YAML)
            metadata = {
                'file_path': str(chunk_path.relative_to(self.vault_path)),
                'chunk_id': self.extract_yaml_field(yaml_content, 'chunk_id'),
                'quality_score': float(self.extract_yaml_field(yaml_content, 'quality_score') or 0),
                'disposition': self.extract_yaml_field(yaml_content, 'disposition'),
                'chunk_source': self.extract_yaml_field(yaml_content, 'chunk_source'),
                'content_date': self.extract_yaml_field(yaml_content, 'content_date'),
                'tags': self.extract_yaml_list(yaml_content, 'tags'),
                'theme': self.extract_yaml_field(yaml_content, 'theme'),
                'word_count': len(body_content.split()),
                'body': body_content[:500]  # First 500 chars for analysis
            }
            
            # Extract tesseract coordinates from tags
            coords = {}
            for tag in metadata['tags']:
                if '/' in tag:
                    dim, val = tag.split('/', 1)
                    coords[dim] = val
            metadata['coordinates'] = coords
            
            return metadata
            
        except Exception as e:
            print(f"Error loading {chunk_path}: {e}")
            return None
    
    def extract_yaml_field(self, yaml_text: str, field: str) -> str:
        """Extract single field from YAML text"""
        pattern = f'{field}:\\s*(.+)'
        match = re.search(pattern, yaml_text)
        return match.group(1).strip() if match else None
    
    def extract_yaml_list(self, yaml_text: str, field: str) -> List[str]:
        """Extract list field from YAML text"""
        # Find the field
        pattern = f'{field}:\\s*'
        match = re.search(pattern, yaml_text)
        if not match:
            return []
        
        # Extract list items
        start_pos = match.end()
        lines = yaml_text[start_pos:].split('\n')
        items = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('- '):
                items.append(line[2:].strip())
            elif line and not line.startswith('#'):
                # Hit next field
                break
        
        return items
    
    def calculate_coordinate_similarity(self, coords1: Dict, coords2: Dict) -> float:
        """Calculate similarity between two tesseract coordinate sets"""
        dimensions = ['x-structure', 'y-transmission', 'z-purpose', 'w-terrain']
        matches = 0
        
        for dim in dimensions:
            if coords1.get(dim) == coords2.get(dim):
                matches += 1
        
        return matches / len(dimensions)
    
    def extract_key_entities(self, text: str) -> Set[str]:
        """Extract likely proper nouns and key terms"""
        # Simple heuristic: capitalized words that aren't sentence starts
        words = text.split()
        entities = set()
        
        for i, word in enumerate(words):
            # Clean word
            word = word.strip('.,!?;:()"\'')
            
            # Skip if empty or too short
            if len(word) < 3:
                continue
            
            # Capitalized and not sentence start
            if word[0].isupper() and i > 0:
                entities.add(word)
        
        # Known entities to always capture
        key_terms = ['Mayo', 'Kelly', 'Rochester', 'Nyx', 'AA', 'ChatGPT', 'Mercor']
        for term in key_terms:
            if term in text:
                entities.add(term)
        
        return entities
    
    def find_clusters(self, chunks: List[Dict]) -> List[Dict[str, Any]]:
        """Find natural groupings of chunks"""
        clusters = []
        processed = set()
        
        for i, chunk in enumerate(chunks):
            if chunk['chunk_id'] in processed:
                continue
            
            # Start new cluster
            cluster = {
                'seed_chunk': chunk['chunk_id'],
                'chunks': [chunk],
                'cluster_score': 0,
                'coordinate_pattern': chunk['coordinates'],
                'shared_entities': self.extract_key_entities(chunk['body']),
                'date_range': [chunk.get('content_date'), chunk.get('content_date')],
                'avg_quality': chunk['quality_score'],
                'total_words': chunk['word_count']
            }
            
            processed.add(chunk['chunk_id'])
            
            # Find similar chunks
            for j, other_chunk in enumerate(chunks):
                if i == j or other_chunk['chunk_id'] in processed:
                    continue
                
                # Calculate similarity
                coord_sim = self.calculate_coordinate_similarity(
                    chunk['coordinates'], 
                    other_chunk['coordinates']
                )
                
                # Check for shared entities
                other_entities = self.extract_key_entities(other_chunk['body'])
                entity_overlap = len(cluster['shared_entities'] & other_entities)
                
                # Check same source file
                same_source = chunk['chunk_source'] == other_chunk['chunk_source']
                
                # Clustering criteria
                should_cluster = (
                    coord_sim >= 0.75 or  # 3+ matching coordinates
                    entity_overlap >= 2 or  # 2+ shared entities
                    same_source  # From same source conversation
                )
                
                if should_cluster:
                    cluster['chunks'].append(other_chunk)
                    cluster['shared_entities'].update(other_entities)
                    cluster['total_words'] += other_chunk['word_count']
                    processed.add(other_chunk['chunk_id'])
            
            # Calculate cluster statistics
            cluster['chunk_count'] = len(cluster['chunks'])
            cluster['avg_quality'] = sum(c['quality_score'] for c in cluster['chunks']) / cluster['chunk_count']
            
            # Only keep clusters with 2+ chunks or very high quality singles
            if cluster['chunk_count'] >= 2 or cluster['avg_quality'] >= 90:
                clusters.append(cluster)
        
        return clusters
    
    def suggest_chapter_title(self, cluster: Dict) -> str:
        """Generate suggested chapter title from cluster"""
        # Use dominant entities
        entities = list(cluster['shared_entities'])[:3]
        
        # Use z-purpose
        z_purpose = cluster['coordinate_pattern'].get('z-purpose', 'story')
        
        if entities:
            return f"Chapter: {', '.join(entities)}"
        else:
            return f"Chapter: {z_purpose}"
    
    def analyze_memoir_structure(self) -> Dict[str, Any]:
        """Main analysis function"""
        print("Loading memoir-grade chunks...")
        
        all_chunks = []
        for folder in self.memoir_folders:
            folder_path = self.vault_path / folder
            if not folder_path.exists():
                continue
            
            for chunk_file in folder_path.rglob("*.md"):
                metadata = self.load_chunk_metadata(chunk_file)
                if metadata and metadata['disposition'] == 'memoir-grade':
                    all_chunks.append(metadata)
        
        print(f"Found {len(all_chunks)} memoir-grade chunks")
        
        # Find clusters
        print("\nAnalyzing clusters...")
        clusters = self.find_clusters(all_chunks)
        
        # Sort clusters by size and quality
        clusters.sort(key=lambda c: (c['chunk_count'], c['avg_quality']), reverse=True)
        
        # Generate chapter suggestions
        chapter_suggestions = []
        for i, cluster in enumerate(clusters, 1):
            suggestion = {
                'chapter_id': f"chapter-{i:02d}",
                'suggested_title': self.suggest_chapter_title(cluster),
                'chunk_count': cluster['chunk_count'],
                'total_words': cluster['total_words'],
                'avg_quality': round(cluster['avg_quality'], 1),
                'coordinate_pattern': cluster['coordinate_pattern'],
                'key_entities': list(cluster['shared_entities'])[:5],
                'chunk_ids': [c['chunk_id'] for c in cluster['chunks']],
                'chunk_files': [c['file_path'] for c in cluster['chunks']]
            }
            chapter_suggestions.append(suggestion)
        
        # Generate summary
        analysis = {
            'analysis_date': datetime.now().isoformat(),
            'total_memoir_chunks': len(all_chunks),
            'total_clusters': len(clusters),
            'chapter_candidates': len([c for c in clusters if c['chunk_count'] >= 5]),
            'singleton_high_quality': len([c for c in clusters if c['chunk_count'] == 1]),
            'chapter_suggestions': chapter_suggestions,
            'coordinate_distribution': self.analyze_coordinate_distribution(all_chunks),
            'coverage_gaps': self.identify_coverage_gaps(clusters)
        }
        
        return analysis
    
    def analyze_coordinate_distribution(self, chunks: List[Dict]) -> Dict:
        """Analyze how chunks distribute across coordinates"""
        z_purposes = Counter()
        x_structures = Counter()
        
        for chunk in chunks:
            coords = chunk['coordinates']
            z_purposes[coords.get('z-purpose', 'unknown')] += 1
            x_structures[coords.get('x-structure', 'unknown')] += 1
        
        return {
            'z_purpose': dict(z_purposes.most_common()),
            'x_structure': dict(x_structures.most_common())
        }
    
    def identify_coverage_gaps(self, clusters: List[Dict]) -> List[str]:
        """Identify potential gaps in memoir coverage"""
        gaps = []
        
        # Check for expected life areas
        expected_entities = {
            'childhood': ['family', 'childhood', 'school'],
            'addiction': ['drinking', 'drugs', 'addiction'],
            'recovery': ['AA', 'sobriety', 'sponsor'],
            'health': ['Mayo', 'cirrhosis', 'medical'],
            'relationships': ['Kelly', 'wife', 'marriage'],
            'current': ['Mercor', 'homeless', 'Rochester']
        }
        
        for area, keywords in expected_entities.items():
            # Check if any cluster has these entities
            found = False
            for cluster in clusters:
                entities_lower = [e.lower() for e in cluster['shared_entities']]
                if any(kw in ' '.join(entities_lower) for kw in keywords):
                    found = True
                    break
            
            if not found:
                gaps.append(f"Limited content about: {area}")
        
        return gaps
    
    def save_analysis(self, analysis: Dict):
        """Save analysis results"""
        output_file = OUTPUT_DIR / "parent_piece_clustering.json"
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print(f"\nAnalysis saved to: {output_file}")
        
        # Also create human-readable summary
        summary_file = OUTPUT_DIR / "chapter_suggestions.md"
        with open(summary_file, 'w') as f:
            f.write("# Memoir Chapter Suggestions\n\n")
            f.write(f"Generated: {analysis['analysis_date']}\n\n")
            f.write(f"**Summary:**\n")
            f.write(f"- Total memoir-grade chunks: {analysis['total_memoir_chunks']}\n")
            f.write(f"- Natural clusters found: {analysis['total_clusters']}\n")
            f.write(f"- Chapter candidates (5+ chunks): {analysis['chapter_candidates']}\n\n")
            
            f.write("## Suggested Chapters\n\n")
            for chapter in analysis['chapter_suggestions']:
                if chapter['chunk_count'] >= 3:  # Only show substantial chapters
                    f.write(f"### {chapter['suggested_title']}\n")
                    f.write(f"- **Chunks:** {chapter['chunk_count']}\n")
                    f.write(f"- **Words:** {chapter['total_words']:,}\n")
                    f.write(f"- **Avg Quality:** {chapter['avg_quality']}\n")
                    f.write(f"- **Key entities:** {', '.join(chapter['key_entities'])}\n")
                    f.write(f"- **Coordinates:** {chapter['coordinate_pattern']}\n")
                    f.write(f"- **Files:**\n")
                    for file_path in chapter['chunk_files'][:5]:
                        f.write(f"  - `{file_path}`\n")
                    if len(chapter['chunk_files']) > 5:
                        f.write(f"  - ... and {len(chapter['chunk_files']) - 5} more\n")
                    f.write("\n")
            
            f.write("## Coverage Gaps\n\n")
            for gap in analysis['coverage_gaps']:
                f.write(f"- {gap}\n")
        
        print(f"Human-readable summary: {summary_file}")

def main():
    """Run parent piece clustering analysis"""
    
    print("=" * 60)
    print("PARENT PIECE CLUSTERING SYSTEM")
    print("=" * 60)
    
    clusterer = ParentPieceClusterer(VAULT_PATH)
    analysis = clusterer.analyze_memoir_structure()
    clusterer.save_analysis(analysis)
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"\nFound {analysis['total_clusters']} natural clusters")
    print(f"Chapter candidates (5+ chunks): {analysis['chapter_candidates']}")
    print(f"\nTop chapter suggestions:")
    
    for i, chapter in enumerate(analysis['chapter_suggestions'][:5], 1):
        print(f"\n{i}. {chapter['suggested_title']}")
        print(f"   {chapter['chunk_count']} chunks, {chapter['total_words']:,} words")
        print(f"   Quality: {chapter['avg_quality']}")

if __name__ == "__main__":
    main()
