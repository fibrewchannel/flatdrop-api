# _inload Content Mining System
# Automated Tesseract-native content discovery and classification

import os
import re
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
import json

class InloadContentMiner:
    def __init__(self, vault_path):
        self.vault_path = Path(vault_path)
        self.inload_dirs = list(self.vault_path.rglob("*inload*"))
        self.content_signatures = {}
        self.mining_results = {
            "high_value": [],
            "memoir_gold": [],
            "recovery_threads": [],
            "job_survival": [],
            "ai_collaboration": [],
            "technical_assets": [],
            "creative_fragments": [],
            "archive_candidates": []
        }
        
    def extract_content_signature(self, file_path):
        """Generate content fingerprint without full processing"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Quick content metrics
            word_count = len(content.split())
            line_count = len(content.splitlines())
            
            # Content pattern detection
            patterns = {
                'memoir_markers': len(re.findall(r'\b(I remember|years ago|childhood|growing up|my father|my mother)\b', content, re.I)),
                'recovery_markers': len(re.findall(r'\b(AA|recovery|sobriety|step work|sponsor|meeting|clean time)\b', content, re.I)),
                'job_markers': len(re.findall(r'\b(interview|resume|job|employment|salary|work|career|application)\b', content, re.I)),
                'ai_markers': len(re.findall(r'\b(nyx|chatgpt|AI|prompt|assistant|LLM|claude)\b', content, re.I)),
                'medical_markers': len(re.findall(r'\b(mayo|doctor|medical|therapy|health|cirrhosis|treatment)\b', content, re.I)),
                'technical_markers': len(re.findall(r'\b(API|code|system|database|server|function|class)\b', content, re.I)),
                'creative_markers': len(re.findall(r'\b(art|music|draw|design|image|creative|story|poem)\b', content, re.I)),
                'emotional_markers': len(re.findall(r'\b(fear|anxiety|depression|trauma|anger|grief|pain|joy)\b', content, re.I))
            }
            
            # Tesseract coordinate hints
            tesseract_hints = {
                'structure_hints': len(re.findall(r'\b(archetype|protocol|shadowcast|expansion|summoning)\b', content, re.I)),
                'purpose_hints': len(re.findall(r'\b(tell.story|help.addict|prevent.death|financial.amends|help.world)\b', content, re.I)),
                'transmission_hints': len(re.findall(r'\b(narrative|text|image|tarot|invocation)\b', content, re.I))
            }
            
            # Quality indicators
            quality_score = self.calculate_quality_score(content, patterns)
            
            return {
                'file_path': str(file_path.relative_to(self.vault_path)),
                'word_count': word_count,
                'line_count': line_count,
                'patterns': patterns,
                'tesseract_hints': tesseract_hints,
                'quality_score': quality_score,
                'has_yaml': content.startswith('---'),
                'creation_hint': self.extract_creation_date(file_path.name),
                'dominant_theme': self.identify_dominant_theme(patterns)
            }
            
        except Exception as e:
            return {'file_path': str(file_path), 'error': str(e)}
    
    def calculate_quality_score(self, content, patterns):
        """Score content quality for memoir/survival relevance"""
        score = 0
        
        # Base score from length (meaningful content)
        word_count = len(content.split())
        if word_count > 500: score += 3
        elif word_count > 200: score += 2
        elif word_count > 50: score += 1
        
        # Bonus for high-value patterns
        score += patterns['memoir_markers'] * 2
        score += patterns['recovery_markers'] * 2
        score += patterns['job_markers'] * 1.5
        score += patterns['medical_markers'] * 1.5
        score += patterns['ai_markers'] * 1
        
        # Penalty for pure technical/system content
        if patterns['technical_markers'] > 10 and patterns['memoir_markers'] == 0:
            score -= 2
            
        return round(score, 1)
    
    def identify_dominant_theme(self, patterns):
        """Identify the strongest content theme"""
        theme_scores = {
            'memoir': patterns['memoir_markers'] * 2,
            'recovery': patterns['recovery_markers'] * 2,
            'survival': patterns['job_markers'] + patterns['medical_markers'],
            'ai_collaboration': patterns['ai_markers'],
            'technical': patterns['technical_markers'],
            'creative': patterns['creative_markers'],
            'emotional': patterns['emotional_markers']
        }
        
        if max(theme_scores.values()) == 0:
            return 'unclear'
        
        return max(theme_scores, key=theme_scores.get)
    
    def extract_creation_date(self, filename):
        """Extract date hints from filename"""
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{8})',
            r'(2024|2025)'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                return match.group(1)
        return None
    
    def scan_all_inload_content(self):
        """Scan all _inload directories and generate content signatures"""
        print(f"🔍 Scanning {len(self.inload_dirs)} _inload directories...")
        
        total_files = 0
        for inload_dir in self.inload_dirs:
            if inload_dir.is_dir():
                md_files = list(inload_dir.rglob("*.md"))
                print(f"📁 {inload_dir.name}: {len(md_files)} markdown files")
                
                for md_file in md_files:
                    signature = self.extract_content_signature(md_file)
                    if 'error' not in signature:
                        self.content_signatures[signature['file_path']] = signature
                        total_files += 1
                        
                        if total_files % 50 == 0:
                            print(f"   Processed {total_files} files...")
        
        print(f"✅ Total files processed: {total_files}")
        return self.content_signatures
    
    def classify_content(self):
        """Classify content into Tesseract-aligned categories"""
        for file_path, signature in self.content_signatures.items():
            quality = signature['quality_score']
            theme = signature['dominant_theme']
            patterns = signature['patterns']
            
            # High-value content (quality > 5)
            if quality > 5:
                self.mining_results['high_value'].append({
                    'file': file_path,
                    'quality': quality,
                    'theme': theme,
                    'word_count': signature['word_count']
                })
            
            # Memoir gold (narrative + personal content)
            if (theme == 'memoir' or patterns['memoir_markers'] > 2) and quality > 3:
                self.mining_results['memoir_gold'].append({
                    'file': file_path,
                    'memoir_markers': patterns['memoir_markers'],
                    'emotional_markers': patterns['emotional_markers'],
                    'quality': quality
                })
            
            # Recovery threads
            if theme == 'recovery' or patterns['recovery_markers'] > 1:
                self.mining_results['recovery_threads'].append({
                    'file': file_path,
                    'recovery_markers': patterns['recovery_markers'],
                    'quality': quality
                })
            
            # Job/survival critical
            if theme == 'survival' or patterns['job_markers'] > 1 or patterns['medical_markers'] > 1:
                self.mining_results['job_survival'].append({
                    'file': file_path,
                    'job_markers': patterns['job_markers'],
                    'medical_markers': patterns['medical_markers'],
                    'quality': quality
                })
            
            # AI collaboration documentation
            if theme == 'ai_collaboration' or patterns['ai_markers'] > 2:
                self.mining_results['ai_collaboration'].append({
                    'file': file_path,
                    'ai_markers': patterns['ai_markers'],
                    'quality': quality
                })
            
            # Creative fragments
            if theme == 'creative' and quality > 2:
                self.mining_results['creative_fragments'].append({
                    'file': file_path,
                    'creative_markers': patterns['creative_markers'],
                    'quality': quality
                })
            
            # Archive candidates (low quality, unclear theme)
            if quality < 2 and theme in ['unclear', 'technical']:
                self.mining_results['archive_candidates'].append({
                    'file': file_path,
                    'quality': quality,
                    'word_count': signature['word_count']
                })
    
    def generate_mining_report(self):
        """Generate comprehensive mining report"""
        total_files = len(self.content_signatures)
        
        report = {
            'scan_summary': {
                'total_files_scanned': total_files,
                'scan_timestamp': datetime.now().isoformat(),
                'inload_directories': [str(d) for d in self.inload_dirs]
            },
            'content_classification': {
                category: len(files) for category, files in self.mining_results.items()
            },
            'top_priorities': {
                'highest_quality': sorted(
                    [f for f in self.mining_results['high_value']], 
                    key=lambda x: x['quality'], 
                    reverse=True
                )[:10],
                'memoir_candidates': sorted(
                    [f for f in self.mining_results['memoir_gold']], 
                    key=lambda x: x['memoir_markers'], 
                    reverse=True
                )[:10],
                'survival_critical': sorted(
                    [f for f in self.mining_results['job_survival']], 
                    key=lambda x: x['job_markers'] + x['medical_markers'], 
                    reverse=True
                )[:10]
            },
            'archive_opportunities': {
                'low_quality_count': len(self.mining_results['archive_candidates']),
                'potential_space_recovered': sum(
                    sig['word_count'] for sig in self.content_signatures.values()
                    if sig['quality_score'] < 1
                )
            }
        }
        
        return report
    
    def export_results(self, output_dir="mining_results"):
        """Export all mining results for review"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Export classification results
        with open(output_path / "content_classification.json", 'w') as f:
            json.dump(self.mining_results, f, indent=2)
        
        # Export full signatures
        with open(output_path / "content_signatures.json", 'w') as f:
            json.dump(self.content_signatures, f, indent=2)
        
        # Export mining report
        report = self.generate_mining_report()
        with open(output_path / "mining_report.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        # Export human-readable summary
        self.export_human_readable_summary(output_path, report)
        
        print(f"📊 Mining results exported to {output_path}/")
        return output_path
    
    def export_human_readable_summary(self, output_path, report):
        """Export human-readable mining summary"""
        summary_lines = [
            "# _inload Content Mining Report",
            f"**Scan Date**: {report['scan_summary']['scan_timestamp']}",
            f"**Total Files**: {report['scan_summary']['total_files_scanned']}",
            "",
            "## Content Classification Results",
            ""
        ]
        
        for category, count in report['content_classification'].items():
            summary_lines.append(f"- **{category.replace('_', ' ').title()}**: {count} files")
        
        summary_lines.extend([
            "",
            "## Top Priority Files",
            "",
            "### Highest Quality Content",
            ""
        ])
        
        for item in report['top_priorities']['highest_quality']:
            summary_lines.append(f"- `{item['file']}` (Quality: {item['quality']}, Theme: {item['theme']})")
        
        summary_lines.extend([
            "",
            "### Memoir Candidates",
            ""
        ])
        
        for item in report['top_priorities']['memoir_candidates']:
            summary_lines.append(f"- `{item['file']}` (Memoir markers: {item['memoir_markers']})")
        
        summary_lines.extend([
            "",
            "### Survival Critical",
            ""
        ])
        
        for item in report['top_priorities']['survival_critical']:
            summary_lines.append(f"- `{item['file']}` (Job: {item['job_markers']}, Medical: {item['medical_markers']})")
        
        with open(output_path / "mining_summary.md", 'w') as f:
            f.write('\n'.join(summary_lines))

# Usage example
if __name__ == "__main__":
    # Initialize miner
    miner = InloadContentMiner("/path/to/vault")
    
    # Scan all content
    signatures = miner.scan_all_inload_content()
    
    # Classify content
    miner.classify_content()
    
    # Export results
    results_path = miner.export_results()
    
    print("\n🎯 Mining complete! Check results for next actions.")
