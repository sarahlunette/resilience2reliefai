"""
Test suite for document_loader.py
Tests document processing functionality
"""

import pytest
import os
import tempfile
from pathlib import Path
from datetime import datetime

# Import the modules to test
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from document_loader import (
    DocumentProcessor, DocumentMetadata, load_documents, load_document,
    clean_text, chunk_text
)

class TestDocumentMetadata:
    """Test DocumentMetadata class"""
    
    def test_metadata_creation(self):
        """Test creating metadata object"""
        metadata = DocumentMetadata(
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            file_size=1024,
            disaster_type="cyclone",
            region="vanuatu"
        )
        
        assert metadata.filename == "test.pdf"
        assert metadata.disaster_type == "cyclone"
        assert metadata.region == "vanuatu"
        assert isinstance(metadata.date_created, datetime)
    
    def test_metadata_to_dict(self):
        """Test converting metadata to dictionary"""
        metadata = DocumentMetadata(
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            file_size=1024
        )
        
        result = metadata.to_dict()
        
        assert isinstance(result, dict)
        assert "filename" in result
        assert "file_path" in result
        assert "file_size" in result
        assert result["filename"] == "test.pdf"

class TestDocumentProcessor:
    """Test DocumentProcessor class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = DocumentProcessor()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_extract_text_from_txt(self):
        """Test extracting text from TXT files"""
        # Create test file
        test_content = "This is a test document about cyclone recovery in Vanuatu."
        test_file = self.temp_path / "test.txt"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        text, metadata = self.processor.extract_text_from_txt(str(test_file))
        
        assert text == test_content
        assert metadata["encoding"] == "utf-8"
        assert metadata["words_count"] == len(test_content.split())
    
    def test_extract_metadata_from_filename(self):
        """Test extracting metadata from filename patterns"""
        test_cases = [
            ("cyclone_pam_vanuatu_2015.pdf", {"disaster_type": "cyclone", "region": "vanuatu"}),
            ("samoa_tsunami_recovery.docx", {"disaster_type": "tsunami", "region": "samoa"}),
            ("fiji_flood_assessment.txt", {"disaster_type": "flood", "region": "fiji"}),
            ("earthquake_response_manual.pdf", {"disaster_type": "earthquake", "region": None}),
            ("general_document.txt", {"disaster_type": None, "region": None})
        ]
        
        for filename, expected in test_cases:
            result = self.processor.extract_metadata_from_filename(filename)
            assert result["disaster_type"] == expected["disaster_type"]
            assert result["region"] == expected["region"]
    
    def test_process_document_txt(self):
        """Test processing a complete TXT document"""
        test_content = """
        CYCLONE PAM RECOVERY PLAN - VANUATU 2015
        
        This document outlines the recovery strategy following Cyclone Pam,
        which struck Vanuatu in March 2015. The plan includes:
        
        1. Housing reconstruction - $50 million USD
        2. Infrastructure repair - $30 million USD
        3. Agriculture rehabilitation - $20 million USD
        
        Total estimated cost: $100 million USD
        Timeline: 36 months
        Beneficiaries: 180,000 people
        """
        
        test_file = self.temp_path / "cyclone_pam_vanuatu_recovery.txt"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        result = self.processor.process_document(str(test_file))
        
        # Verify structure
        assert "text" in result
        assert "metadata" in result
        assert "word_count" in result
        assert "character_count" in result
        
        # Verify content
        assert "Cyclone Pam" in result["text"]
        assert result["metadata"]["disaster_type"] == "cyclone"
        assert result["metadata"]["region"] == "vanuatu"
        assert result["word_count"] > 0
    
    def test_process_directory(self):
        """Test processing multiple documents in directory"""
        # Create multiple test files
        files = [
            ("cyclone_vanuatu.txt", "Cyclone Pam destroyed many buildings in Vanuatu."),
            ("tsunami_samoa.txt", "The 2009 tsunami affected coastal communities in Samoa."),
            ("flood_fiji.txt", "Flooding damaged infrastructure across Fiji.")
        ]
        
        for filename, content in files:
            file_path = self.temp_path / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        results = self.processor.process_directory(str(self.temp_path))
        
        assert len(results) == 3
        for result in results:
            assert "text" in result
            assert "metadata" in result
            assert result["metadata"]["disaster_type"] is not None

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_clean_text(self):
        """Test text cleaning function"""
        dirty_text = "This   is  a    messy    text   with   extra   spaces!!!"
        clean = clean_text(dirty_text)
        
        # Should have single spaces
        assert "  " not in clean
        assert clean.startswith("This is a messy")
    
    def test_chunk_text(self):
        """Test text chunking function"""
        long_text = "This is a very long text. " * 100  # 2600+ characters
        chunks = chunk_text(long_text, chunk_size=500, overlap=50)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 550 for chunk in chunks)  # Allow for overlap
        
        # Test short text
        short_text = "Short text."
        short_chunks = chunk_text(short_text, chunk_size=500)
        assert len(short_chunks) == 1
        assert short_chunks[0] == short_text

class TestIntegration:
    """Integration tests"""
    
    def setup_method(self):
        """Set up integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create realistic test documents
        self.create_test_documents()
    
    def teardown_method(self):
        """Clean up integration test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_documents(self):
        """Create realistic test documents"""
        documents = {
            "cyclone_pam_assessment.txt": """
            POST-CYCLONE PAM DAMAGE ASSESSMENT - VANUATU
            
            Executive Summary:
            Tropical Cyclone Pam struck Vanuatu on March 13, 2015, causing widespread damage.
            
            Damage Summary:
            - 17,000 houses destroyed or damaged
            - 230 schools affected
            - Infrastructure losses: $200 million USD
            - 180,000 people affected
            
            Priority Needs:
            1. Emergency shelter: $25 million
            2. School reconstruction: $35 million  
            3. Healthcare facilities: $15 million
            4. Water and sanitation: $20 million
            
            Recommended Projects:
            - Housing reconstruction with climate-resilient design
            - Multi-hazard school rebuilding program
            - Coastal protection infrastructure
            - Early warning system enhancement
            """,
            
            "samoa_tsunami_recovery.txt": """
            SAMOA TSUNAMI RECOVERY STRATEGY 2010-2015
            
            Background:
            The September 29, 2009 tsunami devastated Samoa's southern coast.
            
            Impact:
            - 189 fatalities
            - 600 houses destroyed  
            - 25 schools damaged
            - Total losses: $200 million USD
            
            Recovery Projects:
            1. Planned Relocation Program: $45 million
            2. Tsunami-Resilient Highway: $85 million
            3. School Reconstruction: $35 million
            4. Mangrove Restoration: $15 million
            
            Timeline: 5 years (2010-2015)
            """,
            
            "undp_schools_guide.txt": """
            UNDP RESILIENT SCHOOLS BUILDING GUIDE
            
            Design Principles:
            - Multi-hazard resistance (wind, flood, earthquake)
            - Community resilience center functionality
            - Environmental sustainability
            
            Construction Standards:
            - Category 5 cyclone wind resistance
            - Elevated above 500-year flood levels
            - Solar power systems
            - Rainwater harvesting
            
            Case Studies:
            - Tafea College, Vanuatu: $2.8 million, 450 students
            - Samoa College Network: 25 schools, standardized design
            
            Typical Costs: $2-3 million per 500-student school
            """
        }
        
        for filename, content in documents.items():
            file_path = self.temp_path / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content.strip())
    
    def test_load_documents_integration(self):
        """Test loading multiple documents"""
        results = load_documents(str(self.temp_path))
        
        assert len(results) == 3
        
        # Verify each document processed correctly
        for result in results:
            assert "text" in result
            assert "metadata" in result
            assert "word_count" in result
            assert result["word_count"] > 0
            
            # Check metadata extraction
            metadata = result["metadata"]
            if "cyclone" in metadata["filename"]:
                assert metadata["disaster_type"] == "cyclone"
            elif "tsunami" in metadata["filename"]:
                assert metadata["disaster_type"] == "tsunami"
    
    def test_load_document_integration(self):
        """Test loading single document"""
        test_file = self.temp_path / "cyclone_pam_assessment.txt"
        result = load_document(str(test_file))
        
        # Verify structure
        assert all(key in result for key in ["text", "metadata", "word_count", "character_count"])
        
        # Verify content extraction
        assert "Cyclone Pam" in result["text"]
        assert "17,000 houses" in result["text"]
        assert "180,000 people" in result["text"]
        
        # Verify metadata
        assert result["metadata"]["disaster_type"] == "cyclone"
        assert result["metadata"]["filename"] == "cyclone_pam_assessment.txt"
        assert result["word_count"] > 100

class TestErrorHandling:
    """Test error handling scenarios"""
    
    def setup_method(self):
        self.processor = DocumentProcessor()
    
    def test_file_not_found(self):
        """Test handling of non-existent files"""
        with pytest.raises(FileNotFoundError):
            self.processor.process_document("/nonexistent/path.txt")
    
    def test_unsupported_format(self):
        """Test handling of unsupported file formats"""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported file format"):
                self.processor.process_document(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_empty_directory(self):
        """Test processing empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            results = self.processor.process_directory(temp_dir)
            assert len(results) == 0

if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])