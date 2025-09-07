"""
Test script to validate the Resilience2Relief AI system
Tests core functionality without requiring server to run
"""

import os
import sys
import tempfile
from pathlib import Path
import logging

# Setup test environment
def setup_test_environment():
    """Setup test directories and environment"""
    Path("data/documents").mkdir(parents=True, exist_ok=True)
    Path("templates").mkdir(parents=True, exist_ok=True)
    Path("vectorstore").mkdir(parents=True, exist_ok=True)

def test_document_loader():
    """Test document loading functionality"""
    try:
        from document_loader import DocumentProcessor
        
        # Create test document
        test_content = """
        Cyclone Pam Recovery Plan for Vanuatu
        
        This comprehensive disaster recovery plan addresses the immediate and long-term 
        needs following Cyclone Pam's devastating impact on Vanuatu in March 2015.
        
        Priority Sectors:
        - Housing reconstruction (1,500 homes needed)
        - Infrastructure repair (roads, bridges, airports)
        - Health facility restoration
        - Education system recovery
        - Water and sanitation systems
        
        Budget Requirements: USD 450 million over 3 years
        Target Beneficiaries: 188,000 people (65% of population)
        
        Implementation Partners:
        - World Bank
        - Asian Development Bank
        - European Union
        - UNDP
        - UNICEF
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            test_file = f.name
        
        try:
            processor = DocumentProcessor()
            doc = processor.process_single_file(Path(test_file))
            
            if doc:
                print("✅ Document processing successful!")
                print(f"   - Filename: {doc.metadata.get('filename', 'N/A')}")
                print(f"   - Content length: {len(doc.text)} characters")
                print(f"   - Disaster types: {doc.metadata.get('disaster_types', [])}")
                print(f"   - Sectors: {doc.metadata.get('sectors', [])}")
                print(f"   - Regions: {doc.metadata.get('regions', [])}")
                return True
            else:
                print("❌ Document processing failed - no document returned")
                return False
                
        finally:
            Path(test_file).unlink()
            
    except Exception as e:
        print(f"❌ Document loader test failed: {str(e)}")
        return False

def test_utils():
    """Test utility functions"""
    try:
        from utils import ProjectFormatter, ValidationUtils, TextProcessor
        
        # Test project formatting
        raw_response = """
        1. Emergency Housing Reconstruction
        This project aims to rebuild 500 homes destroyed by Cyclone Pam in Vanuatu.
        Budget: $15 million
        Timeline: 18 months
        Beneficiaries: 2,500 people
        
        2. Water System Rehabilitation
        Restore water treatment facilities and distribution network in Port Vila.
        Budget: $8 million
        Timeline: 12 months
        """
        
        formatted = ProjectFormatter.format_project_response(raw_response)
        if formatted and formatted.get('total_projects', 0) > 0:
            print("✅ Project formatting successful!")
            print(f"   - Total projects: {formatted['total_projects']}")
            print(f"   - First project: {formatted['projects'][0]['title']}")
        else:
            print("❌ Project formatting failed")
            return False
            
        # Test validation
        is_valid, msg = ValidationUtils.validate_file_upload("test.pdf", 1024*1024)
        if is_valid:
            print("✅ File validation successful!")
        else:
            print(f"❌ File validation failed: {msg}")
            return False
            
        # Test text processing
        keywords = TextProcessor.extract_keywords("disaster recovery infrastructure project")
        if len(keywords) > 0:
            print("✅ Text processing successful!")
            print(f"   - Keywords extracted: {keywords[:5]}")
        else:
            print("❌ Text processing failed")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Utils test failed: {str(e)}")
        return False

def test_api_models():
    """Test API model definitions"""
    try:
        from main import ProjectQuery, ProjectResponse, DocumentInfo
        
        # Test model creation
        query = ProjectQuery(
            query="Generate disaster recovery projects for Pacific islands",
            max_projects=3,
            sectors=["infrastructure", "health"],
            regions=["vanuatu"]
        )
        
        if query.query and query.max_projects == 3:
            print("✅ API models successful!")
            print(f"   - Query: {query.query[:50]}...")
            print(f"   - Max projects: {query.max_projects}")
            print(f"   - Sectors: {query.sectors}")
        else:
            print("❌ API models failed")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ API models test failed: {str(e)}")
        return False

def test_mock_generation():
    """Test mock project generation"""
    try:
        # Mock generation function
        def mock_generate():
            return """
            1. Climate-Resilient Housing Program
            Construct 800 cyclone-resistant homes using local materials and improved building standards.
            Sector: Housing, Infrastructure
            Timeline: 24 months
            Budget: $25 million
            Beneficiaries: 4,000 people
            Partners: World Bank, Habitat for Humanity
            
            2. Integrated Water Security Project
            Establish rainwater harvesting systems and upgrade water treatment facilities.
            Sector: Water, Infrastructure
            Timeline: 18 months
            Budget: $12 million
            Beneficiaries: 15,000 people
            Partners: UNICEF, Pacific Water Association
            
            3. Community Health Resilience Initiative
            Rebuild 5 health centers and train 100 community health workers.
            Sector: Health
            Timeline: 15 months
            Budget: $8 million
            Beneficiaries: 25,000 people
            Partners: WHO, Médecins Sans Frontières
            """
        
        from utils import ProjectFormatter
        
        raw_response = mock_generate()
        formatted = ProjectFormatter.format_project_response(raw_response)
        
        if formatted and formatted.get('total_projects', 0) >= 3:
            print("✅ Mock generation successful!")
            print(f"   - Generated {formatted['total_projects']} projects")
            
            for i, project in enumerate(formatted['projects'][:2], 1):
                print(f"   - Project {i}: {project.get('title', 'Unknown')}")
                print(f"     Sector: {', '.join(project.get('sector', []))}")
                budget = project.get('estimated_budget', {}).get('estimated_amount')
                if budget:
                    print(f"     Budget: ${budget:,.0f}")
                    
        else:
            print("❌ Mock generation failed")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Mock generation test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Resilience2Relief AI System")
    print("=" * 50)
    
    setup_test_environment()
    
    tests = [
        ("Document Loader", test_document_loader),
        ("Utilities", test_utils),
        ("API Models", test_api_models),
        ("Mock Generation", test_mock_generation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📝 Testing {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} test failed!")
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready for deployment.")
        return True
    else:
        print(f"⚠️  {total - passed} test(s) failed. Review errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)