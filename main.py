"""
Resilience2Relief AI - Main FastAPI Application
Comprehensive disaster recovery project generation system
"""

import os
import shutil
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

# FastAPI and Pydantic imports
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field, validator

# Local imports
from rag_chain_model import generate_project_ideas as generate_projects_hf
from rag_chain import generate_project_ideas as generate_projects_openai
from document_loader import load_documents, load_document, DocumentProcessor
from utils import (
    ResponseFormatter, DataValidator, ProjectClassifier, 
    TextProcessor, FileManager, ConfigManager
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
config = ConfigManager.load_config()

# FastAPI app initialization
app = FastAPI(
    title="Resilience2Relief AI",
    description="AI-powered disaster recovery project generation system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ProjectRequest(BaseModel):
    """Request model for project generation"""
    query: str = Field(..., min_length=10, max_length=500, description="Query describing project needs")
    disaster_type: Optional[str] = Field(None, description="Type of disaster (cyclone, earthquake, etc.)")
    region: Optional[str] = Field(None, description="Geographic region")
    sectors: Optional[List[str]] = Field(None, description="Preferred sectors")
    max_projects: int = Field(5, ge=1, le=20, description="Maximum number of projects to generate")
    budget_range: Optional[str] = Field(None, description="Budget range (e.g., '1M-10M USD')")
    timeline: Optional[str] = Field(None, description="Expected timeline")
    priority: Optional[str] = Field(None, description="Priority level (high, medium, low)")
    llm_model: str = Field("openai", description="LLM model to use (openai, huggingface)")
    
    @validator('llm_model')
    def validate_llm_model(cls, v):
        if v not in ['openai', 'huggingface']:
            raise ValueError('llm_model must be either "openai" or "huggingface"')
        return v

class ProjectResponse(BaseModel):
    """Response model for generated projects"""
    id: str
    title: str
    description: str
    sector: List[str]
    priority: str
    budget: Optional[str]
    timeline: Optional[str]
    beneficiaries: Optional[str]
    sdgs: Optional[List[str]]
    funding_sources: Optional[List[str]]
    risk_factors: Optional[List[str]]
    sustainability_features: Optional[List[str]]
    generated_from: List[str]
    confidence_score: Optional[float]

class DocumentInfo(BaseModel):
    """Document information model"""
    filename: str
    file_size: int
    upload_date: datetime
    processed: bool
    word_count: Optional[int]
    disaster_type: Optional[str]
    region: Optional[str]
    document_type: Optional[str]

class SystemStats(BaseModel):
    """System statistics model"""
    total_documents: int
    total_projects_generated: int
    available_sectors: List[str]
    supported_regions: List[str]
    last_updated: datetime

# Global variables for tracking
stats = {
    'total_projects_generated': 0,
    'documents_processed': 0,
    'last_generation': None
}

# Helper functions
def ensure_directories():
    """Ensure all required directories exist"""
    directories = ['data/documents', 'data/uploads', 'templates', 'logs']
    for directory in directories:
        FileManager.ensure_directory(directory)

def get_document_processor():
    """Get document processor instance"""
    return DocumentProcessor()

def validate_file_upload(file: UploadFile) -> bool:
    """Validate uploaded file"""
    # Check file size
    if hasattr(file.file, 'seek'):
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Seek back to beginning
        
        if file_size > config['max_file_size']:
            return False
    
    # Check file extension
    allowed_extensions = {'.pdf', '.docx', '.txt', '.csv', '.md'}
    file_extension = Path(file.filename).suffix.lower()
    
    return file_extension in allowed_extensions

async def process_document_background(file_path: str):
    """Background task to process uploaded document"""
    try:
        processor = get_document_processor()
        result = processor.process_document(file_path)
        stats['documents_processed'] += 1
        logger.info(f"Successfully processed document: {file_path}")
        return result
    except Exception as e:
        logger.error(f"Failed to process document {file_path}: {str(e)}")
        raise

# Initialize on startup
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Resilience2Relief AI...")
    ensure_directories()
    
    # Load existing documents
    documents_path = Path(config['documents_path'])
    if documents_path.exists():
        existing_docs = list(documents_path.glob('*'))
        stats['documents_processed'] = len([f for f in existing_docs if f.is_file()])
    
    logger.info(f"Application started successfully. {stats['documents_processed']} documents available.")

# API Endpoints

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API information"""
    return ResponseFormatter.format_success_response({
        "name": "Resilience2Relief AI",
        "version": "1.0.0",
        "description": "AI-powered disaster recovery project generation",
        "docs_url": "/docs",
        "endpoints": {
            "generate_projects": "/generate",
            "upload_document": "/upload",
            "list_documents": "/documents",
            "system_stats": "/stats"
        }
    })

@app.post("/upload", response_model=Dict[str, Any])
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload and process a disaster recovery document"""
    
    # Validate file
    if not validate_file_upload(file):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file format or size. Supported: PDF, DOCX, TXT, CSV, MD. Max size: 10MB"
        )
    
    # Generate safe filename
    safe_filename = FileManager.clean_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{timestamp}_{safe_filename}"
    
    # Save file
    file_path = Path(config['documents_path']) / unique_filename
    
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process document in background
        background_tasks.add_task(process_document_background, str(file_path))
        
        return ResponseFormatter.format_success_response({
            "filename": unique_filename,
            "original_filename": file.filename,
            "file_size": len(content),
            "upload_path": str(file_path),
            "processing_status": "queued"
        }, f"Document {file.filename} uploaded successfully")
        
    except Exception as e:
        logger.error(f"Failed to upload document: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload document")

@app.post("/generate", response_model=Dict[str, Any])
async def generate_projects(request: ProjectRequest):
    """Generate disaster recovery project ideas based on query and parameters"""
    
    try:
        # Prepare generation parameters
        generation_params = {
            'query': request.query,
            'disaster_type': request.disaster_type,
            'region': request.region,
            'sectors': request.sectors,
            'max_projects': request.max_projects,
            'budget_range': request.budget_range,
            'timeline': request.timeline,
            'priority': request.priority
        }
        
        # Generate projects using selected model
        if request.llm_model == 'openai':
            try:
                raw_response = generate_projects_openai()
                logger.info("Generated projects using OpenAI model")
            except Exception as e:
                logger.warning(f"OpenAI model failed: {e}. Falling back to HuggingFace.")
                raw_response = generate_projects_hf()
        else:
            raw_response = generate_projects_hf()
            logger.info("Generated projects using HuggingFace model")
        
        # Parse and structure the response
        projects = parse_project_response(raw_response, request)
        
        # Update stats
        stats['total_projects_generated'] += len(projects)
        stats['last_generation'] = datetime.now()
        
        return ResponseFormatter.format_success_response({
            'projects': projects,
            'generation_parameters': generation_params,
            'model_used': request.llm_model,
            'generation_time': datetime.now().isoformat(),
            'total_count': len(projects)
        })
        
    except Exception as e:
        logger.error(f"Project generation failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate projects: {str(e)}"
        )

@app.get("/documents", response_model=Dict[str, Any])
async def list_documents(
    skip: int = Query(0, ge=0, description="Number of documents to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of documents to return")
):
    """List all uploaded and processed documents"""
    
    try:
        documents_path = Path(config['documents_path'])
        documents = []
        
        if documents_path.exists():
            for file_path in documents_path.iterdir():
                if file_path.is_file():
                    try:
                        stat = file_path.stat()
                        
                        # Try to get processing information
                        processor = get_document_processor()
                        metadata = processor.extract_metadata_from_filename(file_path.name)
                        
                        doc_info = DocumentInfo(
                            filename=file_path.name,
                            file_size=stat.st_size,
                            upload_date=datetime.fromtimestamp(stat.st_ctime),
                            processed=True,  # Assume processed if in documents folder
                            disaster_type=metadata.get('disaster_type'),
                            region=metadata.get('region'),
                            document_type=metadata.get('document_type')
                        )
                        
                        documents.append(doc_info.dict())
                        
                    except Exception as e:
                        logger.warning(f"Failed to process document info for {file_path.name}: {e}")
                        continue
        
        # Apply pagination
        total = len(documents)
        documents = documents[skip:skip + limit]
        
        return ResponseFormatter.format_success_response({
            'documents': documents,
            'total': total,
            'skip': skip,
            'limit': limit,
            'has_more': skip + limit < total
        })
        
    except Exception as e:
        logger.error(f"Failed to list documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve documents")

@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    """Delete a specific document"""
    
    try:
        file_path = Path(config['documents_path']) / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path.unlink()
        
        return ResponseFormatter.format_success_response(
            {"filename": filename}, 
            f"Document {filename} deleted successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to delete document: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete document")

@app.get("/search", response_model=Dict[str, Any])
async def search_projects(
    q: str = Query(..., min_length=3, description="Search query"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    region: Optional[str] = Query(None, description="Filter by region"),
    priority: Optional[str] = Query(None, description="Filter by priority level")
):
    """Search for projects based on criteria"""
    
    try:
        # This would implement semantic search through the vector store
        # For now, return a simplified response
        
        search_results = {
            'query': q,
            'filters': {
                'sector': sector,
                'region': region,
                'priority': priority
            },
            'results': [],
            'total_matches': 0
        }
        
        return ResponseFormatter.format_success_response(search_results)
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Search operation failed")

@app.get("/stats", response_model=Dict[str, Any])
async def get_system_stats():
    """Get system statistics and status"""
    
    try:
        documents_path = Path(config['documents_path'])
        document_count = len(list(documents_path.glob('*'))) if documents_path.exists() else 0
        
        system_stats = SystemStats(
            total_documents=document_count,
            total_projects_generated=stats['total_projects_generated'],
            available_sectors=list(ProjectClassifier.SECTORS.keys()),
            supported_regions=['vanuatu', 'samoa', 'fiji', 'tonga', 'solomon_islands', 'papua_new_guinea'],
            last_updated=datetime.now()
        )
        
        return ResponseFormatter.format_success_response(system_stats.dict())
        
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Helper functions for project generation
def parse_project_response(raw_response: str, request: ProjectRequest) -> List[Dict[str, Any]]:
    """Parse and structure the raw LLM response into project objects"""
    
    try:
        # Basic parsing - in production, this would be more sophisticated
        projects = []
        
        # Split response into project sections
        # This is a simplified parser - would need enhancement for production
        sections = raw_response.split('\n\n')
        
        project_count = 0
        for section in sections:
            if project_count >= request.max_projects:
                break
                
            if len(section.strip()) > 100:  # Minimum project description length
                # Extract basic project information
                project = {
                    'id': f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{project_count}",
                    'title': extract_title_from_section(section),
                    'description': section.strip(),
                    'sector': request.sectors or ProjectClassifier.classify_sector(section),
                    'priority': request.priority or ProjectClassifier.determine_priority(section),
                    'budget': request.budget_range,
                    'timeline': request.timeline,
                    'beneficiaries': extract_beneficiaries(section),
                    'sdgs': extract_sdgs(section),
                    'funding_sources': extract_funding_sources(section),
                    'generated_from': [f"Query: {request.query}"],
                    'confidence_score': 0.8  # Placeholder
                }
                
                projects.append(project)
                project_count += 1
        
        return projects
        
    except Exception as e:
        logger.error(f"Failed to parse project response: {str(e)}")
        # Return a single project with the full response
        return [{
            'id': f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}_fallback",
            'title': 'Generated Recovery Project',
            'description': raw_response,
            'sector': request.sectors or ['general'],
            'priority': request.priority or 'medium',
            'generated_from': [f"Query: {request.query}"]
        }]

def extract_title_from_section(section: str) -> str:
    """Extract project title from section"""
    lines = section.split('\n')
    for line in lines[:3]:  # Check first 3 lines
        if len(line.strip()) > 10 and len(line.strip()) < 100:
            return line.strip()
    return "Disaster Recovery Project"

def extract_beneficiaries(section: str) -> Optional[str]:
    """Extract beneficiary information from section"""
    beneficiary_patterns = [
        r'(\d+[,\d]*)\s*people',
        r'(\d+[,\d]*)\s*households',
        r'(\d+[,\d]*)\s*families',
        r'(\d+[,\d]*)\s*communities'
    ]
    
    for pattern in beneficiary_patterns:
        import re
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            return match.group(0)
    
    return None

def extract_sdgs(section: str) -> Optional[List[str]]:
    """Extract SDG references from section"""
    sdg_keywords = {
        'SDG 1': ['poverty', 'poor', 'income'],
        'SDG 2': ['hunger', 'food security', 'agriculture'],
        'SDG 3': ['health', 'medical', 'healthcare'],
        'SDG 4': ['education', 'school', 'learning'],
        'SDG 6': ['water', 'sanitation', 'hygiene'],
        'SDG 7': ['energy', 'electricity', 'power'],
        'SDG 11': ['cities', 'urban', 'housing'],
        'SDG 13': ['climate', 'disaster', 'resilience']
    }
    
    section_lower = section.lower()
    relevant_sdgs = []
    
    for sdg, keywords in sdg_keywords.items():
        if any(keyword in section_lower for keyword in keywords):
            relevant_sdgs.append(sdg)
    
    return relevant_sdgs if relevant_sdgs else None

def extract_funding_sources(section: str) -> Optional[List[str]]:
    """Extract potential funding sources from section"""
    funding_sources = [
        'World Bank', 'UNDP', 'USAID', 'European Union', 
        'Green Climate Fund', 'Asian Development Bank',
        'Australia', 'New Zealand', 'Japan'
    ]
    
    found_sources = []
    section_lower = section.lower()
    
    for source in funding_sources:
        if source.lower() in section_lower:
            found_sources.append(source)
    
    return found_sources if found_sources else None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)