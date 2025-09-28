#!/usr/bin/env python3
"""
Tesseract Training Nibbler
Processes Rick's _testtraining files to learn content patterns and calibrate thresholds
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import statistics

# Import existing TesseractConfig system
from tesseract_config import get_analyzer, get_config

@dataclass
class ProcessingResult:
    """Result of processing a single file"""
    file_path: str
    batch_id: int
    processing_status: str  # 'simple', 'complex', 'garbage', 'error'
    quality_score: float
    word_count: int
    extracted_chunks: List[Dict[str, Any]]
    suggested_coordinates: Dict[str, str]
    dominant_theme: str
    error_message: Optional[str] = None

class TrainingNibbler:
    """Content digestion system for training Rick's memoir detection patterns"""
    
    def __init__(self, source_dir: str, output_dir: str):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.config = get_config()
        self.analyzer = get_analyzer()
        
        # Training parameters - ultra permissive
        self.TRAINING_QUALITY_THRESHOLD = 1.0  # Save almost everything
        self.CHUNK_MIN_WORDS = 20              # Very small chunks OK
        self.SAVE_TRASH = True                 # Keep discarded content for learning
        self.BATCH_SIZE = 5                    # Process 5 files at a time
        
        # Initialize output structure
        self.setup_output_directories()
        
    def setup_output_directories(self):
        """Create the training output directory structure"""
        dirs_to_create = [
            "batch_outputs",
            "aggregate_analysis", 
            "manual_review/borderline_cases",
            "manual_review/pattern_mismatches",
            "training_logs"
        ]
        
        for dir_path in dirs_to_create:
            (self.output_dir / dir_path).mkdir(parents=True, exist_ok=True)
    
    def pre_clean_content(self, content: str) -> str:
        """Remove formatting detritus before analysis"""
        # Remove broken YAML frontmatter
        content = re.sub(r'^---[\s\S]*?---\s*', '', content.strip())
        
        # Remove ChatGPT artifacts
        chatgpt_patterns = [
            r"Here's what I found[:.]\s*",
            r"I'll help you[^.]*\.\s*",
            r"Based on (?:the|this)[^.]*\.\s*",
            r"Let me (?:analyze|review|examine)[^.]*\.\s*"
        ]
        for pattern in chatgpt_patterns:
            content = re.sub(pattern, '', content, flags=re.I)
        
        # Clean markdown artifacts
        content = re.sub(r'```[\s\S]*?```', '', content)  # Remove code blocks
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)  # Convert links to text
        content = re.sub(r'#{1,6}\s*', '', content)  # Remove header markers
        
        # Normalize whitespace
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)  # Multiple newlines to double
        content = re.sub(r'[ \t]+', ' ', content)  # Multiple spaces to single
        
        return content.strip()
    
    def analyze_file_complexity(self, content: str, word_count: int) -> str:
        """Determine processing complexity using training-optimized rules"""
        
        # Garbage detection (but save for analysis)
        if word_count < 10:
            return 'garbage'
        
        if len(content.strip()) < 50:
            return 'garbage'
        
        # Check for pure technical garbage
        tech_noise_ratio = len(re.findall(r'[{}()\[\]<>/\\|]', content)) / len(content)
        if tech_noise_ratio > 0.3:
            return 'garbage'
        
        # Detect multiple topics (complex processing needed)
        topic_markers = [
            r'\b(AA|recovery|sobriety|step work|sponsor|meeting)\b',  # Recovery
            r'\b(Mayo|clinic|doctor|medical|cirrhosis|liver)\b',       # Medical  
            r'\b(memoir|story|childhood|I remember|years ago)\b',      # Memoir
            r'\b(housing|homeless|sober house|rent|shelter)\b',        # Survival
            r'\b(work|job|interview|employment|income)\b',             # Work
            r'\b(AI|creative|art|music|philosophy)\b'                  # Creative
        ]
        
        topic_hits = 0
        for pattern in topic_markers:
            if re.search(pattern, content, re.I):
                topic_hits += 1
        
        # Multiple topics = complex processing
        if topic_hits >= 3:
            return 'complex'
        
        # Single clear topic = simple processing
        if topic_hits >= 1:
            return 'simple'
        
        # Unclear content
        return 'complex'
    
    def extract_chunks_from_complex_file(self, content: str) -> List[Dict[str, Any]]:
        """Extract meaningful chunks from complex multi-topic files"""
        chunks = []
        
        # Split content into paragraphs/sections
        sections = re.split(r'\n\s*\n', content)
        
        for i, section in enumerate(sections):
            section = section.strip()
            if len(section.split()) < self.CHUNK_MIN_WORDS:
                continue
            
            # Analyze this chunk
            patterns = self.analyzer.extract_content_patterns(section)
            quality_score = self.analyzer.calculate_quality_score(section, patterns, len(section.split()))
            
            # Even save low-quality chunks during training
            if quality_score >= self.TRAINING_QUALITY_THRESHOLD:
                coordinates = self.analyzer.suggest_tesseract_coordinates(patterns, section)
                theme = self.analyzer.identify_dominant_theme(patterns)
                
                chunks.append({
                    'chunk_id': i,
                    'content': section,
                    'word_count': len(section.split()),
                    'quality_score': quality_score,
                    'coordinates': coordinates,
                    'theme': theme,
                    'patterns': patterns
                })
        
        return chunks
    
    def process_single_file(self, file_path: Path, batch_id: int) -> ProcessingResult:
        """Process a single file through the nibbling pipeline"""
        try:
            # Read and pre-clean content
            raw_content = file_path.read_text(encoding='utf-8', errors='ignore')
            clean_content = self.pre_clean_content(raw_content)
            word_count = len(clean_content.split())
            
            # Analyze complexity
            complexity = self.analyze_file_complexity(clean_content, word_count)
            
            # Extract patterns and score content
            patterns = self.analyzer.extract_content_patterns(clean_content)
            quality_score = self.analyzer.calculate_quality_score(clean_content, patterns, word_count)
            theme = self.analyzer.identify_dominant_theme(patterns)
            coordinates = self.analyzer.suggest_tesseract_coordinates(patterns, clean_content)
            
            # Handle based on complexity
            chunks = []
            
            if complexity == 'simple':
                # Single chunk for simple files
                if quality_score >= self.TRAINING_QUALITY_THRESHOLD:
                    chunks.append({
                        'chunk_id': 0,
                        'content': clean_content,
                        'word_count': word_count,
                        'quality_score': quality_score,
                        'coordinates': coordinates,
                        'theme': theme,
                        'patterns': patterns
                    })
            
            elif complexity == 'complex':
                # Extract multiple chunks
                chunks = self.extract_chunks_from_complex_file(clean_content)
            
            elif complexity == 'garbage':
                # Save for analysis but no chunks
                if self.SAVE_TRASH:
                    chunks.append({
                        'chunk_id': 0,
                        'content': clean_content,
                        'word_count': word_count,
                        'quality_score': quality_score,
                        'coordinates': coordinates,
                        'theme': 'garbage',
                        'patterns': patterns,
                        'marked_as_trash': True
                    })
            
            return ProcessingResult(
                file_path=str(file_path),
                batch_id=batch_id,
                processing_status=complexity,
                quality_score=quality_score,
                word_count=word_count,
                extracted_chunks=chunks,
                suggested_coordinates=coordinates,
                dominant_theme=theme
            )
            
        except Exception as e:
            return ProcessingResult(
                file_path=str(file_path),
                batch_id=batch_id,
                processing_status='error',
                quality_score=0.0,
                word_count=0,
                extracted_chunks=[],
                suggested_coordinates={},
                dominant_theme='error',
                error_message=str(e)
            )
    
    def process_batch(self, files: List[Path], batch_id: int) -> Dict[str, Any]:
        """Process a batch of files and generate analysis"""
        batch_results = []
        batch_stats = {
            'batch_id': batch_id,
            'file_count': len(files),
            'processing_date': datetime.now().isoformat(),
            'status_distribution': {},
            'quality_distribution': {},
            'theme_distribution': {},
            'coordinate_distribution': {},
            'total_chunks_extracted': 0,
            'files_processed': []
        }
        
        print(f"\n🔄 Processing Batch {batch_id}: {len(files)} files")
        
        for i, file_path in enumerate(files):
            print(f"  [{i+1}/{len(files)}] {file_path.name}")
            result = self.process_single_file(file_path, batch_id)
            batch_results.append(result)
            
            # Update stats
            status = result.processing_status
            batch_stats['status_distribution'][status] = batch_stats['status_distribution'].get(status, 0) + 1
            batch_stats['theme_distribution'][result.dominant_theme] = batch_stats['theme_distribution'].get(result.dominant_theme, 0) + 1
            batch_stats['total_chunks_extracted'] += len(result.extracted_chunks)
            
            # Track coordinate distribution
            if result.suggested_coordinates:
                coord_key = result.suggested_coordinates.get('tesseract_key', 'unknown')
                batch_stats['coordinate_distribution'][coord_key] = batch_stats['coordinate_distribution'].get(coord_key, 0) + 1
            
            batch_stats['files_processed'].append({
                'file': file_path.name,
                'status': status,
                'quality': result.quality_score,
                'chunks': len(result.extracted_chunks),
                'theme': result.dominant_theme
            })
        
        # Calculate quality distribution
        quality_scores = [r.quality_score for r in batch_results if r.quality_score > 0]
        if quality_scores:
            batch_stats['quality_distribution'] = {
                'mean': statistics.mean(quality_scores),
                'median': statistics.median(quality_scores),
                'min': min(quality_scores),
                'max': max(quality_scores),
                'count': len(quality_scores),
                'percentiles': {
                    '25th': statistics.quantiles(quality_scores, n=4)[0] if len(quality_scores) >= 4 else 0,
                    '65th': statistics.quantiles(quality_scores, n=20)[12] if len(quality_scores) >= 20 else 0,  # Rick's target
                    '75th': statistics.quantiles(quality_scores, n=4)[2] if len(quality_scores) >= 4 else 0,
                    '90th': statistics.quantiles(quality_scores, n=10)[8] if len(quality_scores) >= 10 else 0
                }
            }
        
        # Save batch results
        batch_output_dir = self.output_dir / f"batch_outputs/batch_{batch_id:02d}"
        batch_output_dir.mkdir(exist_ok=True)
        
        # Save extracted chunks as JSON for analysis
        chunks_file = batch_output_dir / "extracted_chunks.json"
        all_chunks = []
        for result in batch_results:
            for chunk in result.extracted_chunks:
                chunk['source_file'] = Path(result.file_path).name
                chunk['batch_id'] = batch_id
                all_chunks.append(chunk)
        
        with open(chunks_file, 'w') as f:
            json.dump(all_chunks, f, indent=2)
        
        # Save batch statistics
        stats_file = batch_output_dir / "batch_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(batch_stats, f, indent=2)
        
        # Save processing log
        log_file = batch_output_dir / "processing_log.json"
        results_for_log = []
        for result in batch_results:
            results_for_log.append({
                'file_path': result.file_path,
                'status': result.processing_status,
                'quality_score': result.quality_score,
                'word_count': result.word_count,
                'chunks_extracted': len(result.extracted_chunks),
                'coordinates': result.suggested_coordinates,
                'theme': result.dominant_theme,
                'error': result.error_message
            })
        
        with open(log_file, 'w') as f:
            json.dump(results_for_log, f, indent=2)
        
        print(f"✅ Batch {batch_id} complete: {batch_stats['total_chunks_extracted']} chunks extracted")
        print(f"   Status distribution: {batch_stats['status_distribution']}")
        print(f"   Quality range: {batch_stats['quality_distribution'].get('min', 0):.1f} - {batch_stats['quality_distribution'].get('max', 0):.1f}")
        
        return batch_stats
    
    def process_all_training_files(self) -> Dict[str, Any]:
        """Process all files in _testtraining directory"""
        
        # Get all .md files
        md_files = list(self.source_dir.glob("*.md"))
        if not md_files:
            print(f"❌ No .md files found in {self.source_dir}")
            return {}
        
        print(f"🎯 Training Nibbler Starting")
        print(f"📁 Source: {self.source_dir} ({len(md_files)} files)")
        print(f"📁 Output: {self.output_dir}")
        print(f"⚙️ Config: {self.config.config_file}")
        print(f"🎲 Quality threshold: {self.TRAINING_QUALITY_THRESHOLD} (ultra-permissive)")
        
        # Process files in batches
        all_batch_stats = []
        batch_id = 1
        
        for i in range(0, len(md_files), self.BATCH_SIZE):
            batch_files = md_files[i:i + self.BATCH_SIZE]
            batch_stats = self.process_batch(batch_files, batch_id)
            all_batch_stats.append(batch_stats)
            batch_id += 1
        
        # Generate aggregate analysis
        self.generate_aggregate_analysis(all_batch_stats)
        
        print(f"\n🎉 Training complete! Processed {len(md_files)} files in {len(all_batch_stats)} batches")
        print(f"📊 Review results in: {self.output_dir}")
        
        return {
            'total_files': len(md_files),
            'total_batches': len(all_batch_stats),
            'output_directory': str(self.output_dir),
            'batch_summaries': all_batch_stats
        }
    
    def generate_aggregate_analysis(self, batch_stats: List[Dict[str, Any]]):
        """Generate cross-batch analysis and recommendations"""
        
        # Aggregate quality scores across all batches
        all_quality_scores = []
        all_coordinates = {}
        all_themes = {}
        all_statuses = {}
        total_chunks = 0
        
        for batch in batch_stats:
            total_chunks += batch['total_chunks_extracted']
            
            # Collect quality scores
            if 'quality_distribution' in batch and batch['quality_distribution']:
                # This is approximate since we don't have individual scores
                # In real implementation, we'd collect all individual scores
                qual_dist = batch['quality_distribution']
                if qual_dist.get('count', 0) > 0:
                    # Estimate distribution
                    for _ in range(qual_dist['count']):
                        all_quality_scores.append(qual_dist['mean'])
            
            # Aggregate coordinate distribution
            for coord, count in batch.get('coordinate_distribution', {}).items():
                all_coordinates[coord] = all_coordinates.get(coord, 0) + count
            
            # Aggregate themes
            for theme, count in batch.get('theme_distribution', {}).items():
                all_themes[theme] = all_themes.get(theme, 0) + count
            
            # Aggregate statuses
            for status, count in batch.get('status_distribution', {}).items():
                all_statuses[status] = all_statuses.get(status, 0) + count
        
        # Calculate recommendations
        recommendations = {
            'analysis_date': datetime.now().isoformat(),
            'total_files_analyzed': sum(batch['file_count'] for batch in batch_stats),
            'total_chunks_extracted': total_chunks,
            'processing_distribution': all_statuses,
            'coordinate_distribution': all_coordinates,
            'theme_distribution': all_themes,
            'quality_insights': {},
            'threshold_recommendations': {},
            'pattern_effectiveness': {},
            'next_steps': []
        }
        
        # Quality analysis
        if all_quality_scores:
            recommendations['quality_insights'] = {
                'mean_quality': statistics.mean(all_quality_scores),
                'median_quality': statistics.median(all_quality_scores),
                'quality_range': [min(all_quality_scores), max(all_quality_scores)],
                'suggested_65th_percentile': statistics.quantiles(all_quality_scores, n=20)[12] if len(all_quality_scores) >= 20 else 0
            }
            
            # Threshold recommendations
            percentile_65 = recommendations['quality_insights']['suggested_65th_percentile']
            recommendations['threshold_recommendations'] = {
                'current_training_threshold': self.TRAINING_QUALITY_THRESHOLD,
                'suggested_production_threshold': max(percentile_65, 3.0),  # Don't go below 3.0
                'rationale': f"65th percentile is {percentile_65:.1f}, recommended as Rick's 'worth keeping' threshold"
            }
        
        # Generate next steps
        garbage_ratio = all_statuses.get('garbage', 0) / sum(all_statuses.values())
        complex_ratio = all_statuses.get('complex', 0) / sum(all_statuses.values())
        
        recommendations['next_steps'].append(f"Review {total_chunks} extracted chunks for quality patterns")
        
        if garbage_ratio > 0.3:
            recommendations['next_steps'].append(f"High garbage ratio ({garbage_ratio:.1%}) - review garbage detection patterns")
        
        if complex_ratio > 0.5:
            recommendations['next_steps'].append(f"Many complex files ({complex_ratio:.1%}) - AI processing pipeline will be heavily used")
        
        recommendations['next_steps'].append("Manually review borderline cases to refine quality thresholds")
        recommendations['next_steps'].append("Test production pipeline on small batch before full _inload processing")
        
        # Save aggregate analysis
        aggregate_file = self.output_dir / "aggregate_analysis/training_summary.json"
        with open(aggregate_file, 'w') as f:
            json.dump(recommendations, f, indent=2)
        
        print(f"\n📈 Aggregate Analysis Summary:")
        print(f"   Total chunks extracted: {total_chunks}")
        print(f"   Processing distribution: {all_statuses}")
        print(f"   Top themes: {dict(list(sorted(all_themes.items(), key=lambda x: x[1], reverse=True))[:5])}")
        print(f"   Suggested production threshold: {recommendations['threshold_recommendations'].get('suggested_production_threshold', 'TBD')}")

def main():
    """Run the training nibbler on Rick's _testtraining files"""
    
    # Configuration - proper paths for Flatdrop API context
    source_dir = "/Users/rickshangle/Vaults/flatline-codex/_testtraining"
    output_dir = "/Users/rickshangle/Vaults/flatline-codex/_training_output"
    
    # Verify source directory exists
    if not Path(source_dir).exists():
        print(f"❌ Source directory not found: {source_dir}")
        return
    
    # Initialize and run training nibbler
    nibbler = TrainingNibbler(source_dir, output_dir)
    results = nibbler.process_all_training_files()
    
    print(f"\n🎯 Training complete! Check results in:")
    print(f"   {output_dir}")
    print(f"\n📋 Next steps:")
    print(f"   1. Review aggregate_analysis/training_summary.json")
    print(f"   2. Examine extracted chunks in batch_outputs/")
    print(f"   3. Adjust TesseractConfig based on learnings")
    print(f"   4. Test production pipeline on small batch")

if __name__ == "__main__":
    main()
