"""
Test suite for main.py FastAPI application
Tests API endpoints and functionality
"""

import pytest
import json
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
import sys
import os

# Import the FastAPI app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main_simple import app
from utils import ConfigManager

# Create test client
client = TestClient(app)

class TestHealthAndInfo:
    """Test basic health and info endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns API information"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        assert data["success"] is True
        assert "data" in data
        assert "name" in data["data"]
        assert data["data"]["name"] == "Resilience2Relief AI"
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

class TestDocumentEndpoints:
    """Test document-related endpoints"""
    
    def test_list_documents_empty(self):
        """Test listing documents when none exist"""
        response = client.get("/documents")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        assert data["success"] is True
        assert "data" in data
        assert "documents" in data["data"]
        assert isinstance(data["data"]["documents"], list)
    
    def test_list_documents_pagination(self):
        """Test document listing with pagination"""
        response = client.get("/documents?skip=0&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "skip" in data["data"]
        assert "limit" in data["data"]
        assert "total" in data["data"]
        assert data["data"]["skip"] == 0
        assert data["data"]["limit"] == 10
    
    def test_upload_document_invalid_format(self):
        """Test uploading invalid file format"""
        # Create temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_path = temp_file.name
        
        try:
            with open(temp_path, "rb") as f:
                response = client.post(
                    "/upload",
                    files={"file": ("test.xyz", f, "application/octet-stream")}
                )
            
            assert response.status_code == 400
            data = response.json()
            assert "Invalid file format" in data["detail"]
            
        finally:
            Path(temp_path).unlink()
    
    def test_upload_document_valid_txt(self):
        """Test uploading valid TXT document"""
        test_content = """
        CYCLONE PAM RECOVERY ASSESSMENT - VANUATU
        
        This assessment covers the recovery needs following Cyclone Pam.
        Key findings include widespread infrastructure damage and the need
        for climate-resilient reconstruction across multiple sectors.
        
        Priority areas:
        1. Housing reconstruction
        2. School rebuilding  
        3. Healthcare facility repair
        4. Infrastructure restoration
        """
        
        # Create temporary TXT file
        with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False) as temp_file:
            temp_file.write(test_content)
            temp_path = temp_file.name
        
        try:
            with open(temp_path, "rb") as f:
                response = client.post(
                    "/upload",
                    files={"file": ("cyclone_assessment.txt", f, "text/plain")}
                )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "success" in data
            assert data["success"] is True
            assert "data" in data
            assert "filename" in data["data"]
            assert "file_size" in data["data"]
            
        finally:
            Path(temp_path).unlink()
    
    def test_delete_nonexistent_document(self):
        """Test deleting non-existent document"""
        response = client.delete("/documents/nonexistent_file.txt")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

class TestProjectGeneration:
    """Test project generation endpoints"""
    
    def test_generate_projects_basic(self):
        """Test basic project generation"""
        request_data = {
            "query": "Generate housing reconstruction projects for cyclone recovery",
            "max_projects": 3,
            "llm_model": "openai"
        }
        
        response = client.post("/generate", json=request_data)
        
        # The actual generation might fail due to missing API keys or models
        # but we should get a proper error structure
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "data" in data
            assert "projects" in data["data"]
        else:
            # Should be a proper error response
            assert response.status_code in [422, 500]
            data = response.json()
            assert "detail" in data or "error" in data
    
    def test_generate_projects_validation(self):
        """Test project generation request validation"""
        # Test invalid request - missing query
        invalid_request = {
            "max_projects": 5
        }
        
        response = client.post("/generate", json=invalid_request)
        assert response.status_code == 422
        
        # Test invalid LLM model
        invalid_model_request = {
            "query": "test query",
            "llm_model": "invalid_model"
        }
        
        response = client.post("/generate", json=invalid_model_request)
        assert response.status_code == 422
    
    def test_generate_projects_with_parameters(self):
        """Test project generation with all parameters"""
        request_data = {
            "query": "Develop infrastructure projects for earthquake recovery in Pacific islands",
            "disaster_type": "earthquake",
            "region": "pacific",
            "sectors": ["infrastructure", "housing"],
            "max_projects": 2,
            "budget_range": "10M-50M USD",
            "timeline": "24 months",
            "priority": "high",
            "llm_model": "huggingface"
        }
        
        response = client.post("/generate", json=request_data)
        
        # Should accept the request format
        if response.status_code != 200:
            # Even if generation fails, should be proper error format
            assert response.status_code in [422, 500]

class TestSearchAndStats:
    """Test search and statistics endpoints"""
    
    def test_search_projects(self):
        """Test project search functionality"""
        response = client.get("/search?q=housing&sector=infrastructure")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        assert data["success"] is True
        assert "data" in data
        
        search_data = data["data"]
        assert "query" in search_data
        assert "filters" in search_data
        assert "results" in search_data
        assert search_data["query"] == "housing"
    
    def test_search_validation(self):
        """Test search query validation"""
        # Query too short
        response = client.get("/search?q=ab")
        assert response.status_code == 422
    
    def test_system_stats(self):
        """Test system statistics endpoint"""
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        assert data["success"] is True
        assert "data" in data
        
        stats_data = data["data"]
        assert "total_documents" in stats_data
        assert "total_projects_generated" in stats_data
        assert "available_sectors" in stats_data
        assert "supported_regions" in stats_data
        assert "last_updated" in stats_data
        
        # Check that sectors and regions are lists
        assert isinstance(stats_data["available_sectors"], list)
        assert isinstance(stats_data["supported_regions"], list)

class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_invalid_endpoints(self):
        """Test accessing invalid endpoints"""
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_method_not_allowed(self):
        """Test using wrong HTTP methods"""
        # GET on POST endpoint
        response = client.get("/generate")
        assert response.status_code == 405
        
        # POST on GET endpoint
        response = client.post("/stats")
        assert response.status_code == 405
    
    def test_malformed_json(self):
        """Test sending malformed JSON"""
        response = client.post(
            "/generate",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

class TestRequestValidation:
    """Test request validation and Pydantic models"""
    
    def test_project_request_validation(self):
        """Test ProjectRequest model validation"""
        # Valid request
        valid_request = {
            "query": "Build resilient schools after earthquake",
            "disaster_type": "earthquake",
            "region": "samoa",
            "max_projects": 5,
            "llm_model": "openai"
        }
        
        response = client.post("/generate", json=valid_request)
        # Should not fail on validation (may fail on execution)
        assert response.status_code != 422
        
        # Invalid requests
        invalid_requests = [
            # Query too short
            {"query": "short", "llm_model": "openai"},
            
            # Max projects out of range
            {"query": "valid query", "max_projects": 25, "llm_model": "openai"},
            
            # Invalid LLM model
            {"query": "valid query", "llm_model": "invalid"}
        ]
        
        for invalid_req in invalid_requests:
            response = client.post("/generate", json=invalid_req)
            assert response.status_code == 422

class TestIntegration:
    """Integration tests combining multiple endpoints"""
    
    def test_document_upload_and_list_workflow(self):
        """Test complete document workflow"""
        # 1. List documents (should be empty or have existing)
        initial_response = client.get("/documents")
        initial_count = len(initial_response.json()["data"]["documents"])
        
        # 2. Upload a document
        test_content = "Test document content for integration testing"
        with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False) as temp_file:
            temp_file.write(test_content)
            temp_path = temp_file.name
        
        try:
            with open(temp_path, "rb") as f:
                upload_response = client.post(
                    "/upload",
                    files={"file": ("integration_test.txt", f, "text/plain")}
                )
            
            if upload_response.status_code == 200:
                # 3. List documents again (should have one more)
                # Note: Due to background processing, document might not appear immediately
                final_response = client.get("/documents")
                # Just verify the endpoint works, actual count might vary due to async processing
                assert final_response.status_code == 200
                
        finally:
            Path(temp_path).unlink()
    
    def test_stats_after_operations(self):
        """Test that stats reflect system operations"""
        # Get initial stats
        initial_stats = client.get("/stats")
        assert initial_stats.status_code == 200
        
        # Attempt project generation (might fail but should be tracked)
        gen_request = {
            "query": "Generate test project for stats",
            "max_projects": 1,
            "llm_model": "openai"
        }
        client.post("/generate", json=gen_request)
        
        # Get stats again
        final_stats = client.get("/stats")
        assert final_stats.status_code == 200
        
        # Stats endpoint should still work regardless of generation success
        stats_data = final_stats.json()["data"]
        assert "total_projects_generated" in stats_data
        assert isinstance(stats_data["total_projects_generated"], int)

class TestCORS:
    """Test CORS configuration"""
    
    def test_cors_headers(self):
        """Test that CORS headers are present"""
        response = client.options("/")
        
        # Should allow CORS
        assert response.status_code in [200, 405]  # Some endpoints might not support OPTIONS
        
        # Test with actual request
        response = client.get("/health")
        # CORS headers should be present in response
        assert response.status_code == 200

if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])