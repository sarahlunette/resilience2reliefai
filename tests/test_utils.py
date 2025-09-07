"""
Test suite for utils.py
Tests utility functions and helper classes
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# Import the modules to test
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import (
    TextProcessor, ProjectClassifier, DataValidator, FileManager,
    ResponseFormatter, ConfigManager, safe_get, calculate_similarity,
    format_currency, parse_timeframe
)

class TestTextProcessor:
    """Test TextProcessor utility class"""
    
    def test_normalize_text(self):
        """Test text normalization"""
        test_cases = [
            ("Café résumé naïve", "cafe resume naive"),  # Remove accents
            ("MIXED Case Text", "mixed case text"),      # Lowercase
            ("Too    many    spaces", "too many spaces") # Clean spaces
        ]
        
        for input_text, expected in test_cases:
            result = TextProcessor.normalize_text(input_text)
            assert result == expected
    
    def test_extract_keywords(self):
        """Test keyword extraction"""
        text = """
        The cyclone destroyed many houses in Vanuatu. The recovery plan includes
        rebuilding schools, hospitals, and infrastructure. Emergency shelter is
        needed for displaced families. The government requests international aid.
        """
        
        keywords = TextProcessor.extract_keywords(text)
        
        # Should extract meaningful words, not stop words
        assert "cyclone" in keywords
        assert "recovery" in keywords
        assert "infrastructure" in keywords
        assert "vanuatu" in keywords
        
        # Should not include stop words
        assert "the" not in keywords
        assert "and" not in keywords
        assert "is" not in keywords
    
    def test_extract_entities(self):
        """Test entity extraction"""
        text = """
        Cyclone Pam struck Vanuatu in March 2015, causing $200 million USD in damages.
        The UNDP and World Bank provided emergency assistance. Recovery efforts in
        Port Vila involved 50,000 people over 3 years.
        """
        
        entities = TextProcessor.extract_entities(text)
        
        # Check locations
        assert "Vanuatu" in entities["locations"] or "vanuatu" in str(entities["locations"]).lower()
        
        # Check organizations
        assert any("UNDP" in org for org in entities["organizations"])
        assert any("World Bank" in org for org in entities["organizations"])
        
        # Check disasters
        assert any("Cyclone" in disaster for disaster in entities["disasters"])
        
        # Check amounts
        assert any("200" in amount for amount in entities["amounts"])

class TestProjectClassifier:
    """Test ProjectClassifier utility class"""
    
    def test_classify_sector(self):
        """Test sector classification"""
        test_cases = [
            ("Build new roads and bridges", ["infrastructure"]),
            ("Reconstruct damaged houses and shelters", ["housing"]),
            ("Restore crops and livestock", ["agriculture"]),
            ("Rebuild hospitals and clinics", ["health"]),
            ("Construct new schools", ["education"]),
            ("Road construction and hospital building", ["infrastructure", "health"])
        ]
        
        for text, expected_sectors in test_cases:
            result = ProjectClassifier.classify_sector(text)
            
            # Check that at least one expected sector is found
            assert any(sector in result for sector in expected_sectors)
    
    def test_determine_priority(self):
        """Test priority determination"""
        test_cases = [
            ("Emergency response is critical and urgent", "high"),
            ("This project is important for recovery", "medium"), 
            ("Future enhancement would be beneficial", "medium"),
            ("Optional improvement for long-term", "low"),
            ("Normal recovery project", "medium")  # Default
        ]
        
        for text, expected_priority in test_cases:
            result = ProjectClassifier.determine_priority(text)
            assert result == expected_priority

class TestDataValidator:
    """Test DataValidator utility class"""
    
    def test_validate_project_data_valid(self):
        """Test validating valid project data"""
        valid_project = {
            "title": "Housing Reconstruction Project",
            "description": "Rebuild climate-resilient houses for displaced families",
            "sector": ["housing"],
            "budget": "$2.5M USD",
            "timeline": "24 months"
        }
        
        is_valid, errors = DataValidator.validate_project_data(valid_project)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_project_data_invalid(self):
        """Test validating invalid project data"""
        invalid_projects = [
            # Missing required fields
            {"description": "Some description"},
            
            # Wrong data types
            {"title": 123, "description": "desc", "sector": "housing"},
            
            # Invalid budget
            {"title": "test", "description": "desc", "sector": "housing", "budget": "invalid"}
        ]
        
        for project in invalid_projects:
            is_valid, errors = DataValidator.validate_project_data(project)
            assert is_valid is False
            assert len(errors) > 0
    
    def test_validate_document_metadata(self):
        """Test validating document metadata"""
        valid_metadata = {
            "filename": "test.pdf",
            "file_path": "/path/to/test.pdf",
            "file_size": 1024
        }
        
        is_valid, errors = DataValidator.validate_document_metadata(valid_metadata)
        assert is_valid is True
        assert len(errors) == 0
        
        # Test invalid metadata
        invalid_metadata = {"file_size": 1024}  # Missing required fields
        is_valid, errors = DataValidator.validate_document_metadata(invalid_metadata)
        assert is_valid is False
        assert len(errors) > 0

class TestFileManager:
    """Test FileManager utility class"""
    
    def test_ensure_directory(self):
        """Test directory creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / "new" / "nested" / "directory"
            
            # Directory should not exist initially
            assert not test_path.exists()
            
            # Should create directory and return path
            result = FileManager.ensure_directory(test_path)
            
            assert test_path.exists()
            assert test_path.is_dir()
            assert result == test_path
    
    def test_clean_filename(self):
        """Test filename cleaning"""
        test_cases = [
            ("normal_file.txt", "normal_file.txt"),
            ("file with spaces.pdf", "file with spaces.pdf"),
            ("file<with>invalid:chars?.txt", "file_with_invalid_chars_.txt"),
            ("file___with___multiple___underscores.txt", "file_with_multiple_underscores.txt"),
            ("___leading_and_trailing___.txt", "leading_and_trailing.txt")
        ]
        
        for input_name, expected in test_cases:
            result = FileManager.clean_filename(input_name)
            assert result == expected
    
    def test_get_file_hash(self):
        """Test file hashing"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("Test content for hashing")
            temp_path = temp_file.name
        
        try:
            hash1 = FileManager.get_file_hash(temp_path)
            hash2 = FileManager.get_file_hash(temp_path)
            
            # Same file should produce same hash
            assert hash1 == hash2
            assert len(hash1) == 32  # MD5 hash length
            
        finally:
            Path(temp_path).unlink()

class TestResponseFormatter:
    """Test ResponseFormatter utility class"""
    
    def test_format_project_response(self):
        """Test formatting project response"""
        projects = [
            {"title": "Project 1", "sector": "housing", "sectors": ["housing"]},
            {"title": "Project 2", "sector": "infrastructure", "sectors": ["infrastructure", "health"]}
        ]
        
        response = ResponseFormatter.format_project_response(projects)
        
        assert "count" in response
        assert "projects" in response
        assert "generated_at" in response
        assert "sectors" in response
        
        assert response["count"] == 2
        assert len(response["projects"]) == 2
        assert isinstance(response["sectors"], list)
    
    def test_format_error_response(self):
        """Test formatting error response"""
        error_response = ResponseFormatter.format_error_response("Test error", "Error details")
        
        assert error_response["error"] is True
        assert error_response["message"] == "Test error"
        assert error_response["details"] == "Error details"
        assert "timestamp" in error_response
    
    def test_format_success_response(self):
        """Test formatting success response"""
        test_data = {"key": "value"}
        success_response = ResponseFormatter.format_success_response(test_data, "Success message")
        
        assert success_response["success"] is True
        assert success_response["message"] == "Success message"
        assert success_response["data"] == test_data
        assert "timestamp" in success_response

class TestConfigManager:
    """Test ConfigManager utility class"""
    
    def test_load_default_config(self):
        """Test loading default configuration"""
        config = ConfigManager.load_config()
        
        # Should have default values
        assert "chunk_size" in config
        assert "vector_store_path" in config
        assert "supported_languages" in config
        
        assert config["chunk_size"] == 1000
        assert isinstance(config["supported_languages"], list)
    
    def test_load_config_from_file(self):
        """Test loading configuration from file"""
        custom_config = {
            "chunk_size": 500,
            "temperature": 0.5,
            "custom_setting": "test_value"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as config_file:
            json.dump(custom_config, config_file)
            config_path = config_file.name
        
        try:
            config = ConfigManager.load_config(config_path)
            
            # Should have custom values
            assert config["chunk_size"] == 500
            assert config["temperature"] == 0.5
            assert config["custom_setting"] == "test_value"
            
            # Should still have defaults for other settings
            assert "vector_store_path" in config
            
        finally:
            Path(config_path).unlink()
    
    def test_save_config(self):
        """Test saving configuration to file"""
        test_config = {
            "test_setting": "test_value",
            "number_setting": 42
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as config_file:
            config_path = config_file.name
        
        try:
            # Save config
            success = ConfigManager.save_config(test_config, config_path)
            assert success is True
            
            # Load and verify
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
            
            assert loaded_config == test_config
            
        finally:
            Path(config_path).unlink()

class TestUtilityFunctions:
    """Test standalone utility functions"""
    
    def test_safe_get(self):
        """Test safe dictionary access"""
        test_dict = {"key1": "value1", "key2": {"nested": "nested_value"}}
        
        # Normal access
        assert safe_get(test_dict, "key1") == "value1"
        
        # Missing key with default
        assert safe_get(test_dict, "missing_key", "default") == "default"
        
        # Non-dict input
        assert safe_get("not_a_dict", "key", "default") == "default"
        assert safe_get(None, "key", "default") == "default"
    
    def test_calculate_similarity(self):
        """Test text similarity calculation"""
        # Identical texts
        assert calculate_similarity("hello world", "hello world") == 1.0
        
        # Completely different texts
        similarity = calculate_similarity("hello", "goodbye")
        assert 0.0 <= similarity < 1.0
        
        # Partially similar texts
        similarity = calculate_similarity("hello world", "hello universe")
        assert 0.0 < similarity < 1.0
        
        # Empty strings
        assert calculate_similarity("", "") == 0.0
    
    def test_format_currency(self):
        """Test currency formatting"""
        test_cases = [
            (1000, "USD 1.0K"),
            (1_500_000, "USD 1.5M"), 
            (2_500_000_000, "USD 2.5B"),
            (500.50, "USD 500.50")
        ]
        
        for amount, expected in test_cases:
            result = format_currency(amount)
            assert result == expected
        
        # Test different currency
        result = format_currency(1000, "EUR")
        assert result == "EUR 1.0K"
    
    def test_parse_timeframe(self):
        """Test timeframe parsing"""
        test_cases = [
            ("30 days", timedelta(days=30)),
            ("6 months", timedelta(days=180)),
            ("2 years", timedelta(days=730)),
            ("4 weeks", timedelta(weeks=4)),
            ("invalid timeframe", None)
        ]
        
        for timeframe_str, expected in test_cases:
            result = parse_timeframe(timeframe_str)
            if expected is None:
                assert result is None
            else:
                assert result == expected

class TestIntegration:
    """Integration tests for utility functions"""
    
    def test_project_processing_pipeline(self):
        """Test complete project processing pipeline"""
        # Sample project text
        project_text = """
        URGENT: Housing Reconstruction Project for Vanuatu
        
        Following Cyclone Pam, 17,000 houses were destroyed across Vanuatu.
        This project will rebuild climate-resilient homes using modern construction
        techniques and traditional materials. The UNDP and World Bank will provide
        funding support of $50 million USD over 24 months.
        
        Key beneficiaries: 75,000 people in affected communities.
        """
        
        # Process with utilities
        keywords = TextProcessor.extract_keywords(project_text)
        entities = TextProcessor.extract_entities(project_text)
        sectors = ProjectClassifier.classify_sector(project_text)
        priority = ProjectClassifier.determine_priority(project_text)
        
        # Verify processing results
        assert "housing" in keywords or "reconstruction" in keywords
        assert "housing" in sectors
        assert priority == "high"  # Due to "URGENT"
        assert "Vanuatu" in entities["locations"]
        assert any("UNDP" in org for org in entities["organizations"])
        
        # Create project structure
        project = {
            "title": "Housing Reconstruction Project",
            "description": project_text.strip(),
            "sector": sectors,
            "priority": priority,
            "keywords": keywords[:10],  # Top 10 keywords
            "entities": entities
        }
        
        # Validate project
        is_valid, errors = DataValidator.validate_project_data(project)
        assert is_valid is True
        
        # Format response
        response = ResponseFormatter.format_success_response(project)
        assert response["success"] is True
        assert response["data"] == project

if __name__ == "__main__":
    # Run tests if script is executed directly
    import os
    pytest.main([__file__, "-v"])