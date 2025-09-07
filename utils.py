"""
Utility functions for Resilience2Relief AI
Provides helper functions for data processing, validation, and formatting
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import unicodedata

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextProcessor:
    """Advanced text processing utilities"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text by removing accents and special characters"""
        # Remove accents
        text = unicodedata.normalize('NFD', text)
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def extract_keywords(text: str, min_length: int = 3) -> List[str]:
        """Extract meaningful keywords from text"""
        # Common stop words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'within', 'without',
            'a', 'an', 'this', 'that', 'these', 'those', 'is', 'are', 'was', 'were',
            'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can'
        }
        
        # Extract words
        words = re.findall(r'\b[a-z]+\b', TextProcessor.normalize_text(text))
        
        # Filter keywords
        keywords = [
            word for word in words 
            if len(word) >= min_length and word not in stop_words
        ]
        
        # Count frequency and return most common
        from collections import Counter
        word_counts = Counter(keywords)
        return [word for word, count in word_counts.most_common(50)]
    
    @staticmethod
    def extract_entities(text: str) -> Dict[str, List[str]]:
        """Extract named entities like locations, organizations, dates"""
        entities = {
            'locations': [],
            'organizations': [],
            'disasters': [],
            'dates': [],
            'amounts': []
        }
        
        # Location patterns (Pacific focus)
        location_patterns = [
            r'\b(Vanuatu|Samoa|Fiji|Tonga|Solomon Islands?|Papua New Guinea|PNG)\b',
            r'\b(Marshall Islands?|Palau|Micronesia|Nauru|Kiribati|Tuvalu)\b',
            r'\b(Port Vila|Apia|Suva|Nuku\'alofa|Honiara|Port Moresby)\b'
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['locations'].extend(matches)
        
        # Organization patterns
        org_patterns = [
            r'\b(UNDP|World Bank|USAID|European Union|EU|UN|WHO|UNESCO)\b',
            r'\b(Green Climate Fund|GCF|Pacific Disaster Risk Management|PDRM)\b',
            r'\b(Red Cross|Oxfam|Save the Children|Médecins Sans Frontières|MSF)\b'
        ]
        
        for pattern in org_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['organizations'].extend(matches)
        
        # Disaster patterns
        disaster_patterns = [
            r'\b(Cyclone|Hurricane|Typhoon)\s+([A-Z][a-z]+)\b',
            r'\b(Earthquake|Tsunami|Flood|Drought|Volcanic eruption)\b'
        ]
        
        for pattern in disaster_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['disasters'].extend([' '.join(match) if isinstance(match, tuple) else match for match in matches])
        
        # Date patterns
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
            r'\b\d{4}-\d{2}-\d{2}\b',      # YYYY-MM-DD
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['dates'].extend(matches)
        
        # Amount patterns (USD, EUR, etc.)
        amount_patterns = [
            r'\$\s?[\d,]+(?:\.\d{2})?(?:\s?(?:million|billion|thousand|M|B|K))?',
            r'USD\s?[\d,]+(?:\.\d{2})?(?:\s?(?:million|billion|thousand|M|B|K))?',
            r'€\s?[\d,]+(?:\.\d{2})?(?:\s?(?:million|billion|thousand|M|B|K))?'
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['amounts'].extend(matches)
        
        # Remove duplicates and clean
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities

class ProjectClassifier:
    """Classify projects by sector and priority"""
    
    SECTORS = {
        'infrastructure': [
            'road', 'bridge', 'port', 'airport', 'electricity', 'power', 'grid',
            'water', 'sanitation', 'sewage', 'telecommunications', 'internet'
        ],
        'housing': [
            'housing', 'shelter', 'residential', 'accommodation', 'home',
            'building', 'construction', 'repair', 'rebuild', 'reconstruct'
        ],
        'agriculture': [
            'agriculture', 'farming', 'crop', 'livestock', 'fishery', 'aquaculture',
            'food security', 'irrigation', 'fertilizer', 'seed', 'harvest'
        ],
        'health': [
            'health', 'hospital', 'clinic', 'medical', 'healthcare', 'medicine',
            'doctor', 'nurse', 'treatment', 'vaccination', 'epidemic', 'disease'
        ],
        'education': [
            'education', 'school', 'university', 'training', 'capacity building',
            'teacher', 'student', 'learning', 'knowledge', 'skill'
        ],
        'environment': [
            'environment', 'climate', 'forest', 'mangrove', 'coral', 'ecosystem',
            'biodiversity', 'conservation', 'restoration', 'renewable energy'
        ],
        'economic': [
            'economy', 'economic', 'business', 'employment', 'job', 'livelihood',
            'income', 'poverty', 'finance', 'microfinance', 'market', 'trade'
        ],
        'governance': [
            'governance', 'government', 'policy', 'institution', 'capacity',
            'administration', 'management', 'coordination', 'planning'
        ]
    }
    
    PRIORITY_KEYWORDS = {
        'high': [
            'emergency', 'urgent', 'critical', 'immediate', 'life-threatening',
            'essential', 'priority', 'vital', 'crucial', 'catastrophic'
        ],
        'medium': [
            'important', 'significant', 'necessary', 'required', 'needed',
            'beneficial', 'valuable', 'useful', 'recommended'
        ],
        'low': [
            'optional', 'future', 'long-term', 'enhancement', 'improvement',
            'additional', 'supplementary', 'nice-to-have'
        ]
    }
    
    @classmethod
    def classify_sector(cls, text: str) -> List[str]:
        """Classify text into relevant sectors"""
        text_normalized = TextProcessor.normalize_text(text)
        sectors = []
        
        for sector, keywords in cls.SECTORS.items():
            if any(keyword in text_normalized for keyword in keywords):
                sectors.append(sector)
        
        return sectors if sectors else ['general']
    
    @classmethod
    def determine_priority(cls, text: str) -> str:
        """Determine priority level from text"""
        text_normalized = TextProcessor.normalize_text(text)
        
        # Check for high priority keywords first
        for priority in ['high', 'medium', 'low']:
            keywords = cls.PRIORITY_KEYWORDS[priority]
            if any(keyword in text_normalized for keyword in keywords):
                return priority
        
        return 'medium'  # Default priority

class DataValidator:
    """Validate data structures and content"""
    
    @staticmethod
    def validate_project_data(project: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate project data structure"""
        errors = []
        required_fields = ['title', 'description', 'sector']
        
        # Check required fields
        for field in required_fields:
            if field not in project or not project[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate field types
        if 'title' in project and not isinstance(project['title'], str):
            errors.append("Title must be a string")
        
        if 'description' in project and not isinstance(project['description'], str):
            errors.append("Description must be a string")
        
        if 'sector' in project and not isinstance(project['sector'], (str, list)):
            errors.append("Sector must be a string or list")
        
        # Validate optional fields
        if 'budget' in project:
            try:
                float(str(project['budget']).replace('$', '').replace(',', ''))
            except (ValueError, TypeError):
                errors.append("Budget must be a valid number")
        
        if 'timeline' in project and not isinstance(project['timeline'], str):
            errors.append("Timeline must be a string")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_document_metadata(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate document metadata"""
        errors = []
        required_fields = ['filename', 'file_path']
        
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                errors.append(f"Missing required metadata field: {field}")
        
        return len(errors) == 0, errors

class FileManager:
    """File management utilities"""
    
    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """Ensure directory exists, create if it doesn't"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def get_file_hash(file_path: Union[str, Path]) -> str:
        """Get MD5 hash of a file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    @staticmethod
    def clean_filename(filename: str) -> str:
        """Clean filename for safe storage"""
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove multiple underscores
        filename = re.sub(r'_{2,}', '_', filename)
        return filename.strip('_')

class ResponseFormatter:
    """Format API responses and outputs"""
    
    @staticmethod
    def format_project_response(projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format project list response"""
        return {
            'count': len(projects),
            'projects': projects,
            'generated_at': datetime.now().isoformat(),
            'sectors': list(set(
                sector for project in projects
                for sector in (project.get('sectors', []) if isinstance(project.get('sectors'), list) else [project.get('sector', 'general')])
            ))
        }
    
    @staticmethod
    def format_error_response(error: str, details: Optional[str] = None) -> Dict[str, Any]:
        """Format error response"""
        return {
            'error': True,
            'message': error,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def format_success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
        """Format success response"""
        return {
            'success': True,
            'message': message,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }

class ConfigManager:
    """Configuration management"""
    
    DEFAULT_CONFIG = {
        'chunk_size': 1000,
        'chunk_overlap': 200,
        'max_tokens': 512,
        'temperature': 0.3,
        'vector_store_path': 'vectorstore/chroma',
        'documents_path': 'data/documents',
        'templates_path': 'templates',
        'supported_languages': ['en', 'fr'],
        'max_file_size': 10 * 1024 * 1024,  # 10MB
        'max_projects': 10
    }
    
    @classmethod
    def load_config(cls, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        config = cls.DEFAULT_CONFIG.copy()
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        
        return config
    
    @classmethod
    def save_config(cls, config: Dict[str, Any], config_path: str) -> bool:
        """Save configuration to file"""
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save config to {config_path}: {e}")
            return False

# Convenience functions
def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get value from dictionary"""
    return data.get(key, default) if isinstance(data, dict) else default

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity using Jaccard index"""
    words1 = set(TextProcessor.normalize_text(text1).split())
    words2 = set(TextProcessor.normalize_text(text2).split())
    
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0

def format_currency(amount: float, currency: str = 'USD') -> str:
    """Format currency amount"""
    if amount >= 1_000_000_000:
        return f"{currency} {amount/1_000_000_000:.1f}B"
    elif amount >= 1_000_000:
        return f"{currency} {amount/1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"{currency} {amount/1_000:.1f}K"
    else:
        return f"{currency} {amount:,.2f}"

def parse_timeframe(timeframe_str: str) -> Optional[timedelta]:
    """Parse timeframe string to timedelta"""
    timeframe_str = timeframe_str.lower().strip()
    
    patterns = {
        r'(\d+)\s*days?': lambda x: timedelta(days=int(x[0])),
        r'(\d+)\s*weeks?': lambda x: timedelta(weeks=int(x[0])),
        r'(\d+)\s*months?': lambda x: timedelta(days=int(x[0]) * 30),
        r'(\d+)\s*years?': lambda x: timedelta(days=int(x[0]) * 365)
    }
    
    for pattern, converter in patterns.items():
        match = re.search(pattern, timeframe_str)
        if match:
            return converter(match.groups())
    
    return None

# Logging utilities
def setup_logging(level: str = 'INFO', log_file: Optional[str] = None):
    """Set up logging configuration"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            *([] if log_file is None else [logging.FileHandler(log_file)])
        ]
    )

if __name__ == "__main__":
    # Test utilities
    sample_text = """
    The Cyclone Pam assessment for Vanuatu indicates urgent need for 
    infrastructure reconstruction, particularly in Port Vila. The UNDP 
    estimates $50 million required for housing repairs and $25 million 
    for road restoration by December 2024.
    """
    
    print("=== Text Processing ===")
    keywords = TextProcessor.extract_keywords(sample_text)
    print(f"Keywords: {keywords[:10]}")
    
    entities = TextProcessor.extract_entities(sample_text)
    print(f"Entities: {entities}")
    
    print("\n=== Project Classification ===")
    sectors = ProjectClassifier.classify_sector(sample_text)
    print(f"Sectors: {sectors}")
    
    priority = ProjectClassifier.determine_priority(sample_text)
    print(f"Priority: {priority}")
    
    print("\n=== Validation ===")
    sample_project = {
        'title': 'Infrastructure Reconstruction',
        'description': 'Rebuild roads and bridges',
        'sector': sectors,
        'budget': '$75M',
        'timeline': '18 months'
    }
    
    is_valid, errors = DataValidator.validate_project_data(sample_project)
    print(f"Valid project: {is_valid}, Errors: {errors}")