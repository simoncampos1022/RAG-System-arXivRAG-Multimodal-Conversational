"""
Configuration settings for the arXivCSRAG application.
"""
import os
import torch
from pathlib         import Path
from dotenv          import load_dotenv
from huggingface_hub import whoami


# Load environment variables
load_dotenv()
user = whoami(token=os.getenv('HF_TOKEN'))


# Base paths
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = ROOT_DIR / 'data'


# PDF Extraction Configuration
PDF_EXTRACTION_CONFIG = {
    'infer_table_structure'         : True,
    'strategy'                      : 'hi_res',
    'extract_image_block_types'     : ['Image'],
    'extract_image_block_to_payload': True,
    'chunking_strategy'             : 'by_title',
    'max_characters'                : 10000,
    'combine_text_under_n_chars'    : 2000,
    'new_after_n_chars'             : 6000
}


# LLM & Embedding model Configuration
MODEL_NAME      = 'gemini-2.5-flash-lite-preview-06-17'
EMBEDDING_MODEL = 'BAAI/bge-base-en-v1.5'
DEVICE          = 'cuda' if torch.cuda.is_available() else 'cpu'


# Vector Store Configuration
COLLECTION_NAME = 'arXiv_CS_RAG'