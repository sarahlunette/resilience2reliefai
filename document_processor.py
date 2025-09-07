"""
Document processing functionality for Resilience2Relief AI
Handles loading and processing of disaster recovery documents
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

class Document:
    """Document object with content and metadata"""
    def __init__(self, text: str, metadata: Dict[str, Any]):
        self.text = text
        self.metadata = metadata

class DocumentProcessor:
    """Process various document formats for RAG system"""
    
    def __init__(self):
        self.supported_formats = ['.txt', '.md', '.csv']
    
    def process_single_file(self, file_path: Path) -> Optional[Document]:
        """Process a single file and return Document object"""
        
        if not file_path.exists():
            return None
            
        file_extension = file_path.suffix.lower()
        if file_extension not in self.supported_formats:
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata
            metadata = self._extract_metadata(content, file_path)
            
            return Document(text=content, metadata=metadata)
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return None
    
    def _extract_metadata(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from document content"""
        
        metadata = {
            'filename': file_path.name,
            'file_path': str(file_path),
            'file_size': len(content),
            'processed_date': datetime.now().isoformat()
        }
        
        # Extract disaster types
        disaster_patterns = [
            r'cyclone', r'hurricane', r'typhoon', r'earthquake', r'tsunami',
            r'flood', r'drought', r'volcanic', r'eruption'
        ]
        
        found_disasters = []
        for pattern in disaster_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_disasters.append(pattern)
        
        metadata['disaster_types'] = found_disasters
        
        # Extract sectors
        sector_patterns = [
            'housing', 'infrastructure', 'health', 'education', 'agriculture',
            'water', 'energy', 'environment', 'economic', 'governance'
        ]
        
        found_sectors = []
        for sector in sector_patterns:
            if re.search(sector, content, re.IGNORECASE):
                found_sectors.append(sector)
        
        metadata['sectors'] = found_sectors
        
        # Extract regions (Pacific focus)
        region_patterns = [
            'vanuatu', 'samoa', 'fiji', 'tonga', 'solomon islands',
            'papua new guinea', 'marshall islands', 'palau'
        ]
        
        found_regions = []
        for region in region_patterns:
            if re.search(region, content, re.IGNORECASE):
                found_regions.append(region.replace(' ', '_'))
        
        metadata['regions'] = found_regions
        
        return metadata

def load_documents_from_directory(directory: str = "data/documents") -> List[Document]:
    """Load all documents from a directory"""
    
    processor = DocumentProcessor()
    documents = []
    
    directory_path = Path(directory)
    if not directory_path.exists():
        return documents
    
    for file_path in directory_path.iterdir():
        if file_path.is_file():
            doc = processor.process_single_file(file_path)
            if doc:
                documents.append(doc)
    
    return documents