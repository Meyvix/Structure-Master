"""
StructureMaster - Web API Module
REST API using FastAPI for remote access.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import tempfile

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from fastapi import FastAPI, HTTPException, Query, UploadFile, File, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


# Models
class ScanRequest(BaseModel):
    path: str
    recursive: bool = True
    include_hidden: bool = False


class BuildRequest(BaseModel):
    structure: Dict[str, Any]
    output_path: str
    force: bool = False
    dry_run: bool = False


class ExtractRequest(BaseModel):
    path: str
    format: str = "json"
    include_content: bool = False
    encrypt: bool = False
    password: Optional[str] = None


class SearchRequest(BaseModel):
    path: str
    pattern: str
    is_regex: bool = True
    case_sensitive: bool = False
    search_content: bool = False


class CompareRequest(BaseModel):
    old_path: str
    new_path: str


def create_app() -> 'FastAPI':
    """Create and configure FastAPI application."""
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI not installed. Run: pip install fastapi uvicorn")
    
    app = FastAPI(
        title="StructureMaster API",
        description="REST API for project structure analysis, generation, and documentation",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Import modules lazily
    from src.modules.scanner import ProjectScanner
    from src.modules.parser import StructureParser
    from src.modules.builder import StructureBuilder
    from src.modules.exporter import Exporter
    from src.modules.content_extractor import ContentExtractor
    from src.modules.diff_compare import DiffCompare
    from src.modules.file_analyzer import FileAnalyzer
    from src.search.search_engine import SearchEngine
    from src.analytics.statistics import ProjectStatistics
    from src.config import ExportFormat
    
    scanner = ProjectScanner()
    parser = StructureParser()
    builder = StructureBuilder()
    exporter = Exporter()
    extractor = ContentExtractor()
    diff = DiffCompare()
    analyzer = FileAnalyzer()
    search = SearchEngine()
    stats = ProjectStatistics()
    
    # ==================== ROUTES ====================
    
    @app.get("/")
    async def root():
        """API root endpoint."""
        return {
            "name": "StructureMaster API",
            "version": "1.0.0",
            "endpoints": {
                "docs": "/docs",
                "scan": "/api/scan",
                "build": "/api/build",
                "extract": "/api/extract",
                "search": "/api/search",
                "compare": "/api/compare",
                "analyze": "/api/analyze",
                "statistics": "/api/statistics",
            }
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    
    # ==================== SCAN ====================
    
    @app.post("/api/scan")
    async def scan_project(request: ScanRequest):
        """Scan a project and extract its structure."""
        path = Path(request.path)
        
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Path not found: {request.path}")
        
        result = scanner.scan(
            path,
            recursive=request.recursive,
            include_hidden=request.include_hidden
        )
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.errors)
        
        return {
            "success": True,
            "project_type": result.project_type.name,
            "structure": result.structure,
            "stats": result.stats,
        }
    
    @app.get("/api/scan/{path:path}")
    async def scan_project_get(
        path: str,
        recursive: bool = True,
        include_hidden: bool = False
    ):
        """Scan a project (GET version)."""
        target = Path(path)
        if not target.exists():
            raise HTTPException(status_code=404, detail=f"Path not found: {path}")
        
        result = scanner.scan(target, recursive=recursive, include_hidden=include_hidden)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.errors)
        
        return {
            "success": True,
            "project_type": result.project_type.name,
            "structure": result.structure,
            "stats": result.stats,
        }
    
    # ==================== BUILD ====================
    
    @app.post("/api/build")
    async def build_structure(request: BuildRequest):
        """Build project structure from definition."""
        output = Path(request.output_path)
        
        result = builder.build(
            request.structure,
            output,
            force=request.force,
            dry_run=request.dry_run
        )
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.errors)
        
        return {
            "success": True,
            "stats": result.stats,
            "operations": [op.to_dict() for op in result.operations[:100]],
        }
    
    @app.post("/api/parse")
    async def parse_structure(content: str = Query(...), format: str = Query("auto")):
        """Parse structure from text."""
        result = parser.parse(content, format if format != "auto" else None)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.errors)
        
        return {
            "success": True,
            "format_detected": result.format_detected.name,
            "structure": result.structure,
            "stats": result.stats,
        }
    
    # ==================== EXTRACT ====================
    
    @app.post("/api/extract")
    async def extract_content(request: ExtractRequest):
        """Extract project content with metadata."""
        path = Path(request.path)
        
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Path not found: {request.path}")
        
        # Scan first
        scan_result = scanner.scan(path)
        if not scan_result.success:
            raise HTTPException(status_code=500, detail=scan_result.errors)
        
        if request.include_content:
            extract_result = extractor.extract(scan_result.files)
            files_data = [f.to_dict() for f in extract_result.files[:100]]
        else:
            files_data = []
        
        return {
            "success": True,
            "structure": scan_result.structure,
            "stats": scan_result.stats,
            "files": files_data,
        }
    
    @app.get("/api/extract/export")
    async def export_structure(
        path: str,
        format: str = "json",
    ):
        """Export structure to file."""
        target = Path(path)
        if not target.exists():
            raise HTTPException(status_code=404, detail=f"Path not found: {path}")
        
        result = scanner.scan(target)
        if not result.success:
            raise HTTPException(status_code=500, detail=result.errors)
        
        format_map = {
            'json': ExportFormat.JSON,
            'txt': ExportFormat.TXT,
            'md': ExportFormat.MARKDOWN,
            'yaml': ExportFormat.YAML,
            'html': ExportFormat.HTML,
        }
        
        fmt = format_map.get(format.lower(), ExportFormat.JSON)
        
        # Export to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format}', delete=False) as f:
            temp_path = Path(f.name)
        
        export_result = exporter.export_structure(result.structure, temp_path, fmt)
        
        if export_result.success:
            return FileResponse(
                temp_path,
                filename=f"structure.{format}",
                media_type="application/octet-stream"
            )
        else:
            raise HTTPException(status_code=500, detail=export_result.errors)
    
    # ==================== SEARCH ====================
    
    @app.post("/api/search")
    async def search_in_project(request: SearchRequest):
        """Search in project files."""
        path = Path(request.path)
        
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Path not found: {request.path}")
        
        if request.search_content:
            result = search.search_content(
                path,
                request.pattern,
                is_regex=request.is_regex,
                case_sensitive=request.case_sensitive
            )
        else:
            result = search.search_filename(
                path,
                request.pattern,
                is_regex=request.is_regex,
                case_sensitive=request.case_sensitive
            )
        
        return result.to_dict()
    
    @app.get("/api/search/todos")
    async def search_todos(path: str):
        """Search for TODO/FIXME markers."""
        target = Path(path)
        if not target.exists():
            raise HTTPException(status_code=404, detail=f"Path not found: {path}")
        
        result = search.search_todos(target)
        return result.to_dict()
    
    # ==================== COMPARE ====================
    
    @app.post("/api/compare")
    async def compare_projects(request: CompareRequest):
        """Compare two project structures."""
        old_path = Path(request.old_path)
        new_path = Path(request.new_path)
        
        if not old_path.exists():
            raise HTTPException(status_code=404, detail=f"Old path not found: {request.old_path}")
        if not new_path.exists():
            raise HTTPException(status_code=404, detail=f"New path not found: {request.new_path}")
        
        result = diff.compare_directories(old_path, new_path)
        
        return {
            "stats": result.stats,
            "added": [item.to_dict() for item in result.added_items[:50]],
            "removed": [item.to_dict() for item in result.removed_items[:50]],
            "modified": [item.to_dict() for item in result.modified_items[:50]],
        }
    
    # ==================== ANALYZE ====================
    
    @app.get("/api/analyze")
    async def analyze_project(path: str):
        """Analyze code quality and metrics."""
        target = Path(path)
        if not target.exists():
            raise HTTPException(status_code=404, detail=f"Path not found: {path}")
        
        result = analyzer.analyze_directory(target)
        return result
    
    # ==================== STATISTICS ====================
    
    @app.get("/api/statistics")
    async def get_statistics(path: str):
        """Get project statistics."""
        target = Path(path)
        if not target.exists():
            raise HTTPException(status_code=404, detail=f"Path not found: {path}")
        
        analysis = stats.analyze(target)
        return analysis.to_dict()
    
    @app.get("/api/statistics/duplicates")
    async def find_duplicates(path: str, limit: int = 20):
        """Find duplicate files."""
        target = Path(path)
        if not target.exists():
            raise HTTPException(status_code=404, detail=f"Path not found: {path}")
        
        duplicates = stats.find_duplicates(target)
        return {
            "count": len(duplicates),
            "duplicates": [d.to_dict() for d in duplicates[:limit]]
        }
    
    return app


# Create default app instance
if FASTAPI_AVAILABLE:
    app = create_app()
else:
    app = None


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server."""
    if not FASTAPI_AVAILABLE:
        print("FastAPI not installed. Run: pip install fastapi uvicorn")
        return
    
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
