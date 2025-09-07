"""
Simplified Resilience2Relief AI - Main FastAPI Application
Basic version for testing and demonstration
"""

import os
import shutil
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# FastAPI and Pydantic imports
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Mount static files will be set up after function definition

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

class DocumentInfo(BaseModel):
    """Document information model"""
    filename: str
    file_size: int
    upload_date: datetime
    processed: bool

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
    directories = ['data/documents', 'data/uploads', 'templates', 'logs', 'static']
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def generate_mock_projects(request: ProjectRequest) -> List[Dict[str, Any]]:
    """Generate mock projects for demonstration"""
    
    # Mock project templates based on common disaster recovery needs
    project_templates = [
        {
            "title": "Climate-Resilient Housing Reconstruction",
            "description": "Rebuild damaged houses with climate-resilient designs and materials. Incorporate traditional building techniques with modern engineering standards for cyclone and flood resistance.",
            "sector": ["housing"],
            "priority": "high",
            "budget": "$2-5M USD",
            "timeline": "18-24 months",
            "beneficiaries": "5,000-10,000 people",
            "sdgs": ["SDG 11", "SDG 13"],
            "funding_sources": ["World Bank", "Green Climate Fund"],
        },
        {
            "title": "Multi-Hazard School Reconstruction",
            "description": "Rebuild schools as community resilience centers with disaster-resistant designs. Include solar power, rainwater harvesting, and emergency shelter capacity.",
            "sector": ["education", "infrastructure"],
            "priority": "high", 
            "budget": "$1-3M USD per school",
            "timeline": "12-18 months",
            "beneficiaries": "2,000-5,000 students",
            "sdgs": ["SDG 4", "SDG 13"],
            "funding_sources": ["UNDP", "UNICEF", "Australia/New Zealand"],
        },
        {
            "title": "Agricultural Resilience Program",
            "description": "Restore agricultural productivity through climate-smart farming, diversified crops, and improved storage facilities. Support farmers with training and resources.",
            "sector": ["agriculture"],
            "priority": "medium",
            "budget": "$3-8M USD",
            "timeline": "24-36 months", 
            "beneficiaries": "15,000-25,000 farmers",
            "sdgs": ["SDG 2", "SDG 13"],
            "funding_sources": ["FAO", "World Bank", "EU"],
        },
        {
            "title": "Coastal Infrastructure Protection",
            "description": "Build coastal defenses including seawalls, mangrove restoration, and drainage systems. Integrate natural and engineered solutions for storm surge protection.",
            "sector": ["infrastructure", "environment"],
            "priority": "high",
            "budget": "$10-25M USD",
            "timeline": "36-48 months",
            "beneficiaries": "50,000-100,000 people",
            "sdgs": ["SDG 11", "SDG 13", "SDG 14"],
            "funding_sources": ["Green Climate Fund", "Asian Development Bank"],
        },
        {
            "title": "Healthcare System Strengthening",
            "description": "Rebuild and upgrade health facilities with emergency response capacity. Include medical equipment, staff training, and disaster preparedness systems.",
            "sector": ["health"],
            "priority": "high",
            "budget": "$5-15M USD",
            "timeline": "18-30 months",
            "beneficiaries": "75,000-150,000 people",
            "sdgs": ["SDG 3", "SDG 13"],
            "funding_sources": ["WHO", "World Bank", "USAID"],
        }
    ]
    
    # Filter and customize projects based on request parameters
    filtered_projects = []
    
    for i, template in enumerate(project_templates[:request.max_projects]):
        project = template.copy()
        
        # Customize based on request parameters
        if request.disaster_type:
            project["description"] = f"Following {request.disaster_type} damage, " + project["description"]
        
        if request.region:
            project["region"] = request.region
            project["description"] = project["description"] + f" Tailored for {request.region} context and needs."
        
        if request.sectors:
            # Prioritize projects that match requested sectors
            project_sectors = set(project["sector"])
            requested_sectors = set(request.sectors)
            if not project_sectors.intersection(requested_sectors):
                continue
        
        if request.budget_range:
            project["budget"] = request.budget_range
        
        if request.timeline:
            project["timeline"] = request.timeline
            
        if request.priority:
            project["priority"] = request.priority
        
        # Add unique ID and generation info
        project["id"] = f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}"
        project["generated_from"] = [f"Query: {request.query}"]
        project["confidence_score"] = 0.85
        
        filtered_projects.append(project)
    
    return filtered_projects

# Initialize on startup
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Resilience2Relief AI...")
    ensure_directories()
    
    # Mount static files after directories are created
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Count existing documents
    documents_path = Path("data/documents")
    if documents_path.exists():
        existing_docs = list(documents_path.glob('*'))
        stats['documents_processed'] = len([f for f in existing_docs if f.is_file()])
    
    logger.info(f"Application started successfully. {stats['documents_processed']} documents available.")

# API Endpoints
@app.get("/")
async def root():
    """Serve the main application interface"""
    return FileResponse("static/index.html")

@app.get("/api", response_model=Dict[str, Any])
async def api_info():
    """API information endpoint"""
    return {
        "success": True,
        "message": "Welcome to Resilience2Relief AI API",
        "data": {
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
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/upload", response_model=Dict[str, Any])
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a disaster recovery document"""
    
    # Validate file extension
    allowed_extensions = {'.pdf', '.docx', '.txt', '.csv', '.md'}
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Supported: PDF, DOCX, TXT, CSV, MD"
        )
    
    # Generate safe filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    
    # Save file
    file_path = Path("data/documents") / safe_filename
    
    try:
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Update stats
        stats['documents_processed'] += 1
        
        return {
            "success": True,
            "message": f"Document {file.filename} uploaded successfully",
            "data": {
                "filename": safe_filename,
                "original_filename": file.filename,
                "file_size": len(content),
                "upload_path": str(file_path),
                "processing_status": "completed"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to upload document: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload document")

@app.post("/generate", response_model=Dict[str, Any])
async def generate_projects(request: ProjectRequest):
    """Generate disaster recovery project ideas based on query and parameters"""
    
    try:
        # Generate mock projects
        projects = generate_mock_projects(request)
        
        # Update stats
        stats['total_projects_generated'] += len(projects)
        stats['last_generation'] = datetime.now()
        
        return {
            "success": True,
            "message": f"Generated {len(projects)} project ideas successfully",
            "data": {
                "projects": projects,
                "generation_parameters": {
                    "query": request.query,
                    "disaster_type": request.disaster_type,
                    "region": request.region,
                    "sectors": request.sectors,
                    "max_projects": request.max_projects,
                    "budget_range": request.budget_range,
                    "timeline": request.timeline,
                    "priority": request.priority
                },
                "generation_time": datetime.now().isoformat(),
                "total_count": len(projects)
            },
            "timestamp": datetime.now().isoformat()
        }
        
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
        documents_path = Path("data/documents")
        documents = []
        
        if documents_path.exists():
            for file_path in documents_path.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    
                    doc_info = {
                        "filename": file_path.name,
                        "file_size": stat.st_size,
                        "upload_date": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "processed": True
                    }
                    
                    documents.append(doc_info)
        
        # Apply pagination
        total = len(documents)
        documents = documents[skip:skip + limit]
        
        return {
            "success": True,
            "message": f"Retrieved {len(documents)} documents",
            "data": {
                "documents": documents,
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": skip + limit < total
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve documents")

@app.get("/stats", response_model=Dict[str, Any])
async def get_system_stats():
    """Get system statistics and status"""
    
    try:
        documents_path = Path("data/documents")
        document_count = len(list(documents_path.glob('*'))) if documents_path.exists() else 0
        
        system_stats = {
            "total_documents": document_count,
            "total_projects_generated": stats['total_projects_generated'],
            "available_sectors": [
                "infrastructure", "housing", "agriculture", "health", 
                "education", "environment", "economic", "governance"
            ],
            "supported_regions": [
                "vanuatu", "samoa", "fiji", "tonga", "solomon_islands", 
                "papua_new_guinea", "marshall_islands", "palau"
            ],
            "last_updated": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "message": "System statistics retrieved successfully",
            "data": system_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

@app.get("/search", response_model=Dict[str, Any])
async def search_projects(
    q: str = Query(..., min_length=3, description="Search query"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    region: Optional[str] = Query(None, description="Filter by region"),
    priority: Optional[str] = Query(None, description="Filter by priority level")
):
    """Search for projects based on criteria"""
    
    try:
        # Mock search results
        search_results = {
            "query": q,
            "filters": {
                "sector": sector,
                "region": region,
                "priority": priority
            },
            "results": [
                {
                    "id": "search_result_1",
                    "title": f"Project matching '{q}'",
                    "description": f"This project addresses {q} with focus on {sector or 'multiple sectors'}",
                    "relevance_score": 0.92
                }
            ],
            "total_matches": 1
        }
        
        return {
            "success": True,
            "message": f"Found {len(search_results['results'])} matching projects",
            "data": search_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Search operation failed")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "uptime": "operational"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)