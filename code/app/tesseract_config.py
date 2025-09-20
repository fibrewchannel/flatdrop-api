#!/usr/bin/env python3
"""
TesseractConfig System
Central configuration management for Flatdrop API's 4D cognitive architecture
Extracts all hardcoded patterns, weights, and mappings into YAML configuration
"""

from pathlib import Path
import json
import yaml
import re
from typing import Dict, List, Any, Optional

class TesseractConfig:
    """Central configuration for all Tesseract operations"""
    
    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or Path(__file__).parent / "tesseract_config.yaml"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file with fallback to defaults"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Create default config
            default_config = self._create_default_config()
            self._save_config(default_config)
            return default_config
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to YAML file"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create the default Tesseract configuration extracted from single_file_tester.py"""
        return {
            'system': {
                'vault_name': 'flatline-codex',
                'backup_retention_days': 30,
                'api_version': '1.0.0',
                'coordinate_format': 'single_value_per_dimension'
            },
            
            # Extracted from single_file_tester.py lines 22-30
            'content_patterns': {
                'memoir_markers': {
                    'regex': r'\b(I remember|years ago|childhood|growing up|my father|my mother|when I was)\b',
                    'weight': 3.0,
                    'description': 'Indicators of memoir-quality narrative content'
                },
                'recovery_markers': {
                    'regex': r'\b(AA|recovery|sobriety|step work|sponsor|meeting|clean time|twelve steps?)\b',
                    'weight': 2.5,
                    'description': 'Recovery program and addiction-related content'
                },
                'job_markers': {
                    'regex': r'\b(interview|resume|job|employment|salary|work|career|application|hire|employer)\b',
                    'weight': 2.0,
                    'description': 'Employment and career-related content'
                },
                'ai_markers': {
                    'regex': r'\b(nyx|chatgpt|AI|prompt|assistant|LLM|claude|gpt)\b',
                    'weight': 1.0,
                    'description': 'AI collaboration and tool usage'
                },
                'medical_markers': {
                    'regex': r'\b(mayo|doctor|medical|therapy|health|cirrhosis|treatment|hospital|clinic)\b',
                    'weight': 1.5,
                    'description': 'Medical treatment and health management'
                },
                'technical_markers': {
                    'regex': r'\b(API|code|system|database|server|function|class|script|programming)\b',
                    'weight': -0.5,
                    'description': 'Technical implementation details (memoir penalty)'
                },
                'creative_markers': {
                    'regex': r'\b(art|music|draw|design|image|creative|story|poem|paint|sketch)\b',
                    'weight': 1.0,
                    'description': 'Creative and artistic content'
                },
                'emotional_markers': {
                    'regex': r'\b(fear|anxiety|depression|trauma|anger|grief|pain|joy|love|hope)\b',
                    'weight': 0.5,
                    'description': 'Emotional processing and expression'
                }
            },
            
            # Extracted from single_file_tester.py lines 83-98
            'quality_scoring': {
                'length_bonuses': {
                    1000: 4,
                    500: 3,
                    200: 2,
                    50: 1
                },
                'pattern_multipliers': {
                    'memoir_markers': 3,
                    'recovery_markers': 2.5,
                    'job_markers': 2,
                    'medical_markers': 1.5,
                    'ai_markers': 1,
                    'emotional_markers': 0.5
                },
                'penalties': {
                    'technical_dominant': -3,  # Applied when technical > 10 and no personal content
                },
                'bonuses': {
                    'high_first_person': 2,  # >20 first person pronouns
                    'medium_first_person': 1  # 10-20 first person pronouns
                },
                'first_person_thresholds': {
                    'high': 20,
                    'medium': 10
                }
            },
            
            # Extracted from single_file_tester.py lines 125-170
            'coordinate_assignment_rules': {
                'structure_thresholds': {
                    'shadowcast': {'memoir_markers': 2},
                    'protocol': {'recovery_markers': 2},
                    'expansion': {'creative_markers': 2},
                    'summoning': {'ai_markers': 3},
                    'archetype': {'default': True}
                },
                'transmission_thresholds': {
                    'narrative': {'first_person_pronouns': 20, 'memoir_markers': 1},
                    'image': {'creative_markers': 2, 'image_content': True},
                    'invocation': {'has_dialogue': True, 'recovery_markers': 2},
                    'text': {'ai_markers': 2, 'default': True}
                },
                'purpose_thresholds': {
                    'tell-story': {'memoir_markers': 1, 'first_person_pronouns': 15},
                    'help-addict': {'recovery_markers': 1},
                    'prevent-death-poverty': {'job_markers': 1, 'medical_markers': 1},
                    'help-world': {'creative_markers': 2},
                    'financial-amends': {'job_markers': 2}
                },
                'terrain_thresholds': {
                    'chaotic': {'emotional_markers': 5},
                    'complicated': {'technical_markers': 5},
                    'complex': {'memoir_markers': 2, 'first_person_pronouns': 20},
                    'obvious': {'default': True}
                }
            },
            
            # Extracted from single_file_tester.py lines 190-220
            'folder_structure': {
                'tell-story': {
                    'base_path': 'memoir',
                    'structure_mappings': {
                        'shadowcast': 'explorations',
                        'protocol': 'practices', 
                        'archetype': 'personas',
                        'default': 'spine/foundations'
                    }
                },
                'help-addict': {
                    'base_path': 'recovery',
                    'structure_mappings': {
                        'protocol': 'practices',
                        'archetype': 'personas',
                        'shadowcast': 'explorations',
                        'default': 'activations'
                    }
                },
                'prevent-death-poverty': {
                    'base_path': 'survival',
                    'theme_mappings': {
                        'medical': 'medical',
                        'housing': 'housing',
                        'default': 'systems'
                    }
                },
                'financial-amends': {
                    'base_path': 'work-amends',
                    'structure_mappings': {
                        'protocol': 'practices',
                        'archetype': 'personas', 
                        'default': 'job-search'
                    }
                },
                'help-world': {
                    'base_path': 'contribution',
                    'theme_mappings': {
                        'creative': 'creative',
                        'technical': 'systems',
                        'default': 'context'
                    },
                    'structure_mappings': {
                        'expansion': 'context'
                    }
                },
                'inbox': {
                    'base_path': '_tesseract-inbox',
                    'default': 'needs-classification'
                }
            },
            
            # Extracted theme scoring logic from lines 110-125
            'theme_scoring': {
                'memoir': {'memoir_markers': 3},
                'recovery': {'recovery_markers': 2.5},
                'survival': {'job_markers': 1, 'medical_markers': 1},
                'ai_collaboration': {'ai_markers': 1},
                'technical': {'technical_markers': 1},
                'creative': {'creative_markers': 1},
                'emotional': {'emotional_markers': 1}
            },
            
            # Tesseract dimension definitions
            'tesseract_dimensions': {
                'x_structure': {
                    'values': ['archetype', 'protocol', 'shadowcast', 'expansion', 'summoning'],
                    'description': 'How content is organized/structured'
                },
                'y_transmission': {
                    'values': ['narrative', 'text', 'image', 'tarot', 'invocation'],
                    'description': 'How information is transmitted/presented'
                },
                'z_purpose': {
                    'values': ['tell-story', 'help-addict', 'prevent-death-poverty', 'financial-amends', 'help-world'],
                    'description': "Rick's 5 core life intents"
                },
                'w_terrain': {
                    'values': ['obvious', 'complicated', 'complex', 'chaotic', 'confused'],
                    'description': 'Cognitive complexity/emotional terrain'
                }
            }
        }
    
    # Accessor methods for easy configuration retrieval
    def get_content_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Get all content pattern configurations"""
        return self.config['content_patterns']
    
    def get_coordinate_rules(self) -> Dict[str, Dict[str, Any]]:
        """Get Tesseract coordinate assignment rules"""
        return self.config['coordinate_assignment_rules']
    
    def get_quality_config(self) -> Dict[str, Any]:
        """Get quality scoring configuration"""
        return self.config['quality_scoring']
    
    def get_folder_structure(self) -> Dict[str, Any]:
        """Get folder structure mappings"""
        return self.config['folder_structure']
    
    def get_theme_scoring(self) -> Dict[str, Dict[str, int]]:
        """Get theme identification scoring"""
        return self.config['theme_scoring']
    
    def get_tesseract_dimensions(self) -> Dict[str, Dict[str, Any]]:
        """Get the 4D coordinate system definitions"""
        return self.config['tesseract_dimensions']
    
    # Update methods for runtime configuration changes
    def update_pattern_weight(self, pattern_name: str, new_weight: float):
        """Update the weight for a specific content pattern"""
        if pattern_name in self.config['content_patterns']:
            self.config['content_patterns'][pattern_name]['weight'] = new_weight
            self._save_config(self.config)
    
    def add_custom_pattern(self, name: str, regex: str, weight: float, description: str):
        """Add a new content pattern"""
        self.config['content_patterns'][name] = {
            'regex': regex,
            'weight': weight,
            'description': description
        }
        self._save_config(self.config)
    
    def update_coordinate_threshold(self, dimension: str, coordinate: str, threshold_key: str, value: Any):
        """Update coordinate assignment thresholds"""
        threshold_map = f"{dimension}_thresholds"
        if threshold_map in self.config['coordinate_assignment_rules']:
            if coordinate in self.config['coordinate_assignment_rules'][threshold_map]:
                self.config['coordinate_assignment_rules'][threshold_map][coordinate][threshold_key] = value
                self._save_config(self.config)

# Configuration-driven content analyzer to replace hardcoded functions
class ContentAnalyzer:
    """Content analysis using TesseractConfig instead of hardcoded values"""
    
    def __init__(self, config: TesseractConfig):
        self.config = config
        self.patterns = config.get_content_patterns()
        self.quality_config = config.get_quality_config()
        self.coordinate_rules = config.get_coordinate_rules()
        self.theme_scoring = config.get_theme_scoring()
    
    def extract_content_patterns(self, content: str) -> Dict[str, int]:
        """Extract content patterns using configured regex patterns"""
        pattern_counts = {}
        
        for pattern_name, pattern_config in self.patterns.items():
            regex = pattern_config['regex']
            matches = re.findall(regex, content, re.I)
            pattern_counts[pattern_name] = len(matches)
        
        return pattern_counts
    
    def calculate_quality_score(self, content: str, patterns: Dict[str, int], word_count: int) -> float:
        """Calculate quality score using configured weights and bonuses"""
        score = 0
        
        # Length bonuses from config
        for min_words, bonus in sorted(self.quality_config['length_bonuses'].items(), reverse=True):
            if word_count > min_words:
                score += bonus
                break
        
        # Pattern multipliers from config
        for pattern_name, multiplier in self.quality_config['pattern_multipliers'].items():
            if pattern_name in patterns:
                score += patterns[pattern_name] * multiplier
        
        # Technical penalty from config
        if (patterns.get('technical_markers', 0) > 10 and 
            patterns.get('memoir_markers', 0) == 0 and 
            patterns.get('emotional_markers', 0) == 0):
            score += self.quality_config['penalties']['technical_dominant']
        
        # First person bonuses from config
        first_person_count = len(re.findall(r'\b(I|me|my)\b', content))
        thresholds = self.quality_config['first_person_thresholds']
        
        if first_person_count > thresholds['high']:
            score += self.quality_config['bonuses']['high_first_person']
        elif first_person_count > thresholds['medium']:
            score += self.quality_config['bonuses']['medium_first_person']
        
        return round(max(0, score), 1)
    
    def identify_dominant_theme(self, patterns: Dict[str, int]) -> str:
        """Identify dominant theme using configured scoring"""
        theme_scores = {}
        
        for theme_name, theme_config in self.theme_scoring.items():
            score = 0
            for pattern_name, multiplier in theme_config.items():
                if pattern_name in patterns:
                    score += patterns[pattern_name] * multiplier
            theme_scores[theme_name] = score
        
        if max(theme_scores.values()) == 0:
            return 'unclear'
        
        return max(theme_scores, key=theme_scores.get)
    
    def suggest_tesseract_coordinates(self, patterns: Dict[str, int], content: str) -> Dict[str, str]:
        """Suggest Tesseract coordinates using configured rules"""
        coordinates = {}
        
        # Structure (X-axis)
        structure_rules = self.coordinate_rules['structure_thresholds']
        coordinates['x_structure'] = self._find_best_coordinate(patterns, content, structure_rules)
        
        # Transmission (Y-axis)
        transmission_rules = self.coordinate_rules['transmission_thresholds']
        coordinates['y_transmission'] = self._find_best_coordinate(patterns, content, transmission_rules)
        
        # Purpose (Z-axis)
        purpose_rules = self.coordinate_rules['purpose_thresholds']
        coordinates['z_purpose'] = self._find_best_coordinate(patterns, content, purpose_rules)
        
        # Terrain (W-axis)
        terrain_rules = self.coordinate_rules['terrain_thresholds']
        coordinates['w_terrain'] = self._find_best_coordinate(patterns, content, terrain_rules)
        
        coordinates['tesseract_key'] = f"{coordinates['x_structure']}:{coordinates['y_transmission']}:{coordinates['z_purpose']}:{coordinates['w_terrain']}"
        
        return coordinates
    
    def _find_best_coordinate(self, patterns: Dict[str, int], content: str, rules: Dict[str, Dict[str, Any]]) -> str:
        """Find the best coordinate for a dimension using configured rules"""
        for coordinate, thresholds in rules.items():
            if 'default' in thresholds and thresholds['default']:
                default_coord = coordinate
                continue
                
            matches = True
            for threshold_key, threshold_value in thresholds.items():
                if threshold_key == 'default':
                    continue
                elif threshold_key in patterns:
                    if patterns[threshold_key] <= threshold_value:
                        matches = False
                        break
                elif threshold_key == 'first_person_pronouns':
                    first_person_count = len(re.findall(r'\b(I|me|my)\b', content))
                    if first_person_count <= threshold_value:
                        matches = False
                        break
                elif threshold_key == 'has_dialogue':
                    has_dialogue = len(re.findall(r'"[^"]*"', content)) > 0
                    if not has_dialogue:
                        matches = False
                        break
                elif threshold_key == 'image_content':
                    if 'image' not in content.lower():
                        matches = False
                        break
            
            if matches:
                return coordinate
        
        return default_coord if 'default_coord' in locals() else list(rules.keys())[0]
    
    def suggest_destination_folder(self, coordinates: Dict[str, str], theme: str, quality: float) -> str:
        """Suggest destination folder using configured structure mappings"""
        folder_config = self.config.get_folder_structure()
        purpose = coordinates['z_purpose']
        structure = coordinates['x_structure']
        
        if purpose not in folder_config:
            return folder_config['inbox']['base_path'] + '/' + folder_config['inbox']['default']
        
        purpose_config = folder_config[purpose]
        base_path = purpose_config['base_path']
        
        # Try structure mapping first
        if 'structure_mappings' in purpose_config and structure in purpose_config['structure_mappings']:
            subfolder = purpose_config['structure_mappings'][structure]
            return f"{base_path}/{subfolder}/"
        
        # Try theme mapping
        if 'theme_mappings' in purpose_config:
            if theme in purpose_config['theme_mappings']:
                subfolder = purpose_config['theme_mappings'][theme]
                return f"{base_path}/{subfolder}/"
            elif 'default' in purpose_config['theme_mappings']:
                subfolder = purpose_config['theme_mappings']['default']
                return f"{base_path}/{subfolder}/"
        
        # Use structure mapping default
        if 'structure_mappings' in purpose_config and 'default' in purpose_config['structure_mappings']:
            subfolder = purpose_config['structure_mappings']['default']
            return f"{base_path}/{subfolder}/"
        
        # Fallback to inbox
        return folder_config['inbox']['base_path'] + '/' + folder_config['inbox']['default']

# Global configuration instance
tesseract_config = TesseractConfig()
content_analyzer = ContentAnalyzer(tesseract_config)

def get_config() -> TesseractConfig:
    """Get the global Tesseract configuration instance"""
    return tesseract_config

def get_analyzer() -> ContentAnalyzer:
    """Get the global content analyzer instance"""
    return content_analyzer