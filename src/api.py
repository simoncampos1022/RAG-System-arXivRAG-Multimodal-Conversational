"""
FastAPI backend for the arXivCSRAG application.
"""
import os
from typing                  import List, Optional
from pathlib                 import Path
from datetime                import datetime
from pydantic                import BaseModel
from fastapi                 import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles     import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from utils.setup_logger             import setup_logger
from src.config                     import TEMP_DIR, ROOT_DIR
from src.fetcher.arxiv_fetcher      import ArxivFetcher
from src.data_extraction.extractor  import extract_from_pdf, separate_content_types
from src.processors.text_processor  import TextProcessor
from src.processors.table_processor import TableProcessor
from src.processors.image_processor import ImageProcessor
from src.storage.vectorstore        import VectorStore
from src.rag.pipeline               import RAGPipeline


# Configure logging
logger = setup_logger(__name__)


# Initialize the FastAPI app
app = FastAPI(
    title       = 'arXivCSRAG API',
    description = 'API for the arXivCSRAG Multimodal RAG Application',
    version     = '1.0.0',
)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ['*'],
    allow_credentials = True,
    allow_methods     = ['*'],
    allow_headers     = ['*'],
)


# Models
class APIKeys(BaseModel):
    gemini_api_key   : str
    huggingface_token: str

class SearchQuery(BaseModel):
    subject_tags: Optional[List[str]] = None
    start_date  : Optional[str]       = None
    end_date    : Optional[str]       = None
    max_results : int                 = 10
    query       : str

class PaperID(BaseModel):
    arxiv_id: str

class ChatMessage(BaseModel):
    message: str


# Initialize components
arxiv_fetcher   = ArxivFetcher()
text_processor  = TextProcessor()
table_processor = TableProcessor()
image_processor = ImageProcessor()
vector_store    = VectorStore()
rag_pipeline    = RAGPipeline(vector_store.retriever)


# API endpoints
@app.post('/api/configure')
async def configure_api_keys(api_keys: APIKeys):
    """Configure API keys for the application."""
    try:
        # Set environment variables
        os.environ['GOOGLE_API_KEY'] = api_keys.gemini_api_key
        os.environ['HF_TOKEN']       = api_keys.huggingface_token
        
        logger.info('API keys configured successfully')
        
        return {'status' : 'success', 
                'message': 'API keys configured successfully'}
        
    except Exception as e:
        logger.error(f"Error configuring API keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/fetch-papers')
async def fetch_papers(search_query: SearchQuery):
    """Fetch papers from arXiv based on search query and filters."""
    try:
        papers = arxiv_fetcher.fetch_papers(
            subject_tags = search_query.subject_tags,
            start_date   = search_query.start_date,
            end_date     = search_query.end_date,
            max_results  = search_query.max_results,
            query        = search_query.query
        )
        
        logger.info(f"Fetched {len(papers)} papers")
        
        return {'status': 'success', 'papers': papers}

    except Exception as e:
        logger.error(f"Error fetching papers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/paper-metadata')
async def get_paper_metadata(paper_id: PaperID):
    """Get metadata for a specific paper."""
    try:
        search = arxiv_fetcher.fetch_papers(f"id:{paper_id.arxiv_id}", max_results=1)
        if not search:
            raise HTTPException(status_code=404, detail='Paper not found')

        return {'status': 'success', 'metadata': search[0]}

    except Exception as e:
        logger.error(f"Error getting paper metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/download-paper')
async def download_paper(paper_id: PaperID):
    """Download a paper's PDF from arXiv."""
    try:
        pdf_path = arxiv_fetcher.download_paper(paper_id.arxiv_id)
        
        if not pdf_path:
            raise HTTPException(status_code=404, detail="Failed to download paper")
        
        logger.info(f"Downloaded paper {paper_id.arxiv_id} to {pdf_path}")
        
        return {'status': 'success', 'file_path': str(pdf_path)}
    
    except Exception as e:
        logger.error(f"Error downloading paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/upload-paper')
async def upload_paper(file: UploadFile = File(...)):
    """Upload a paper's PDF file."""
    try:
        # Create a unique filename
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename  = f"uploaded_{timestamp}.pdf"
        filepath  = TEMP_DIR / filename
        
        # Save the uploaded file
        with open(filepath, 'wb') as f:
            f.write(await file.read())
        logger.info(f"Uploaded paper saved at {filepath}")
        
        return {'status': 'success', 'file_path': str(filepath)}
    
    except Exception as e:
        logger.error(f"Error uploading paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/process-paper')
async def process_paper(file_path: str = Form(...)):
    """Process a paper for RAG."""
    try:
        # # Reset the vector store
        # vector_store.reset()
        
        # # Set the new retriever for the RAG pipeline
        # rag_pipeline.retriever = vector_store.retriever
        
        # Process the paper
        pdf_path = Path(file_path)
        logger.info(f"Processing paper at {pdf_path}")
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail='PDF file not found')
        
        # Extract content from PDF
        logger.info(f"Extracting content from {pdf_path}")
        chunks = extract_from_pdf(pdf_path)
        
        # Separate content types
        logger.info(f"Separating content types from {len(chunks)} chunks")
        content = separate_content_types(chunks)
        
        
        # Process and summarize content
        logger.info(f"Processing {len(content['texts'])} text content")
        text_summaries  = text_processor.process(content['texts'])

        logger.info(f"Processing {len(content['tables'])} table content")
        table_summaries = table_processor.process(content['tables'])

        logger.info(f"Processing {len(content['images'])} image content")
        image_summaries = image_processor.process(content['images'])
        
        
        # Add to vector store
        logger.info("Adding processed content to vector store")
        vector_store.add_contents(
            content['texts'] , text_summaries,
            content['tables'], table_summaries,
            content['images'], image_summaries
        )
        
        logger.info(f"Processed paper {pdf_path.name} successfully")
        return {
            'status': 'success',
            'stats' : {
                'texts' : len(content['texts']),
                'tables': len(content['tables']),
                'images': len(content['images'])
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/chat')
async def chat_with_paper(message: ChatMessage):
    """Chat with a processed paper."""
    try:
        rag_pipeline.retriever = vector_store.retriever
        
        # Query the RAG pipeline
        logger.info(f"Chatting with paper: {message.message}")
        response = rag_pipeline.query(message.message)
        
        # Get the retrieved documents
        retrieved_docs = vector_store.retrieve(message.message)
        parsed_docs    = rag_pipeline.parse_docs(retrieved_docs)
        
        return {
            'status'   : 'success',
            'response' : response['response'],
            'citations': parsed_docs
        }
    except Exception as e:
        logger.error(f"Error chatting with paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/reset-chat')
async def reset_chat():
    """Reset the chat and vector store."""
    try:
        logger.info("Resetting chat and vector store")
        vector_store.reset()
        rag_pipeline.retriever = vector_store.retriever
        return {'status': 'success', 'message': 'Chat reset successfully'}
    
    except Exception as e:
        logger.error(f"Error resetting chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Serve static files
app.mount('/static', StaticFiles(directory=ROOT_DIR / 'static', html=False), name='static')
app.mount('/data'  , StaticFiles(directory=ROOT_DIR / 'static/data')       , name='data')
app.mount('/'      , StaticFiles(directory=ROOT_DIR / 'static', html=True) , name='root')