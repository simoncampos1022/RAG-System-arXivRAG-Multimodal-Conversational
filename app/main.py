import os
import uuid
import shutil
import logging
from typing import List

from fastapi                 import FastAPI, File, Form, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses       import JSONResponse
from fastapi.staticfiles     import StaticFiles
from fastapi.templating      import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests      import Request

# Import utilities
from app.utils.pdf_processor import PDFProcessor
from app.utils.rag_pipeline  import RAGPipeline


# Setup logging
logging.basicConfig(
    level  = logging.INFO,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Initialize FastAPI
app = FastAPI(title='DocChat: Multi-modal RAG Application')

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ['*'],
    allow_credentials = True,
    allow_methods     = ['*'],
    allow_headers     = ['*'],
)


# Mount static files and templates
app.mount('/static', StaticFiles(directory='app/static'), name='static')
templates = Jinja2Templates(directory='app/templates')

# Create upload directory if it doesn't exist
UPLOAD_DIR = 'app/uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Global variable to store application state
app_state = {
    'api_key'          : None,
    'model'            : None,
    'temperature'      : 0.7,
    'processor'        : None,
    'pipeline'         : None,
    'files'            : [],
    'processing_status': 'idle' # idle, processing, complete, error
}


@app.get('/')
async def read_root(request: Request):
    """Render the main application page."""
    return templates.TemplateResponse('index.html', {'request': request})


@app.post('/api/configure')
async def configure(
    api_key    : str   = Form(...),
    model      : str   = Form(...),
    temperature: float = Form(0.7)
):
    """Configure the RAG system with API key and model settings."""
    
    try:
        # Validate the model name
        valid_models = [
            'gemini-2.0-flash-lite',
            'gemini-2.0-flash',
            'gemini-2.5-flash-lite-preview-06-17',
            'gemini-2.5-flash'
        ]
        
        if model not in valid_models:
            raise HTTPException(status_code=400, detail=f"Invalid model. Choose from: {', '.join(valid_models)}")
        
        # Validate temperature
        if not (0.0 <= temperature <= 1.0):
            raise HTTPException(status_code=400, detail='Temperature must be between 0.0 and 1.0')
        
        # Update application state
        app_state['api_key']     = api_key
        app_state['model']       = model
        app_state['temperature'] = temperature

        # Initialize the RAG pipeline
        app_state['pipeline'] = RAGPipeline(api_key, model, temperature)
        
        return JSONResponse(content={'status': 'success', 'message': 'Configuration saved'})
    
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")


@app.post('/api/upload')
async def upload_files(files: List[UploadFile] = File(...)):
    """Handle file uploads."""
    
    try:
        # Check if configuration is done
        if not app_state['api_key'] or not app_state['model']:
            raise HTTPException(
                status_code = 400, 
                detail      = 'Please configure API key and model first'
            )
        
        uploaded_files = []
        
        for file in files:
            # Validate file type
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code = 400, 
                    detail      = f"File {file.filename} is not a PDF"
                )
            
            # Create a unique filename
            unique_filename = f"{uuid.uuid4()}_{file.filename}"
            file_path       = os.path.join(UPLOAD_DIR, unique_filename)
            
            # Save the file
            with open(file_path, 'wb') as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            uploaded_files.append({
                'original_name': file.filename,
                'path'         : file_path
            })
        
        # Update application state
        app_state['files'] = uploaded_files

        return JSONResponse(
            content={
                'status' : 'success',
                'message': f"Successfully uploaded {len(uploaded_files)} files",
                'files'  : [f['original_name'] for f in uploaded_files]
            }
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")


@app.post('/api/analyze')
async def analyze_files(background_tasks: BackgroundTasks):
    """Process uploaded PDFs in the background."""
    
    try:
        # Check if files are uploaded
        if not app_state['files']:
            raise HTTPException(
                status_code = 400, 
                detail      = 'No files uploaded. Please upload files first.'
            )
        
        # Check if configuration is done
        if not app_state['pipeline']:
            raise HTTPException(
                status_code = 400, 
                detail      = 'Please configure API key and model first'
            )
        
        # Update processing status
        app_state['processing_status'] = 'processing'
        
        # Initialize PDF processor
        app_state['processor'] = PDFProcessor(
            app_state['files'], 
            app_state['pipeline']
        )
        
        # Process PDFs in background
        background_tasks.add_task(
            process_pdfs_background,
            app_state['processor']
        )
        
        return JSONResponse(
            content={
                'status' : 'success',
                'message': 'PDF processing started'
            }
        )
    
    except Exception as e:
        app_state['processing_status'] = 'error'
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


async def process_pdfs_background(processor: PDFProcessor):
    """Background task to process PDFs."""
    
    try:
        await processor.process_all()
        app_state['processing_status'] = 'complete'
    except Exception as e:
        app_state['processing_status'] = 'error'
        logger.error(f"Background processing error: {e}")


@app.get("/api/status")
async def get_status():
    """Get the current processing status."""
    
    return JSONResponse(
        content={
            'status'     : app_state['processing_status'],
            'files_count': len(app_state['files']),
            'files'      : [f['original_name'] for f in app_state['files']]
        }
    )


@app.post('/api/query')
async def handle_query(query: str = Form(...)):
    """Process a user query using the RAG pipeline."""
    
    try:
        # Check if processing is complete
        if app_state['processing_status'] != 'complete':
            raise HTTPException(
                status_code = 400, 
                detail      = 'PDF processing is not complete. Please wait.'
            )
        
        # Get response from RAG pipeline
        response = await app_state['pipeline'].query(query)

        return JSONResponse(content=response)
    
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")


@app.post('/api/reset')
async def reset_application():
    """Reset the application state."""
    try:
        # Clear upload directory
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)
        
        # Reset application state
        app_state.update({
            'api_key'          : None,
            'model'            : None,
            'temperature'      : 0.7,
            'processor'        : None,
            'pipeline'         : None,
            'files'            : [],
            'processing_status': 'idle'
        })
        
        return JSONResponse(
            content={
                'status' : 'success',
                'message': 'Application reset successfully'
            }
        )
    
    except Exception as e:
        logger.error(f"Reset error: {e}")
        raise HTTPException(status_code=500, detail=f"Reset error: {str(e)}")


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.main:app', host='0.0.0.0', port=8000, reload=True)