"""
Main entry point for the arXivCSRAG application.
"""
import os
import uvicorn
from dotenv import load_dotenv
from utils.setup_logger import setup_logger

load_dotenv()
logger = setup_logger(__name__)


if __name__ == '__main__':
    from src.api import app
    
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Starting arXivCSRAG Application on port {port}...")
    
    uvicorn.run(app, host='0.0.0.0', port=port)