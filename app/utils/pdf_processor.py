import logging
from typing import List, Dict
from unstructured.partition.pdf import partition_pdf

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    Process PDFs by partitioning them into Text, Table, and Image components.
    """
    
    def __init__(self, files: List[Dict[str, str]], rag_pipeline):
        """
        Initialize the PDF processor.
        
        Args:
            files       : List of dictionaries with file information
            rag_pipeline: RAG pipeline instance for summarization and storage
        """
        
        self.files              = files
        self.rag_pipeline       = rag_pipeline
        self.processing_results = {}
    
    
    async def process_all(self):
        """Process all PDF files."""
        
        for file_info in self.files:
            file_path     = file_info['path']
            original_name = file_info['original_name']
            
            try:
                logger.info(f"Processing {original_name}...")
                await self.process_single_pdf(file_path, original_name)
                logger.info(f"Completed processing {original_name}")
                
            except Exception as e:
                logger.error(f"Error processing {original_name}: {e}")
                self.processing_results[original_name] = {
                    'status': 'error',
                    'error' : str(e)
                }
    
     
    async def process_single_pdf(self, file_path: str, original_name: str):
        """
        Process a single PDF file by:
        1. Partitioning it into text, tables, and images
        2. Summarizing each chunk
        3. Adding to the RAG pipeline's vector store
        
        Args:
            file_path: Path to the PDF file
            original_name: Original filename
        """
        
        # Step 1: Partition the PDF
        self.processing_results[original_name] = {'status': 'partitioning'}
        chunks = partition_pdf(
            filename                       = file_path,
            infer_table_structure          = True,          # Infer table structure from the PDF
            strategy                       = 'hi_res',      # Better results for PDFs with images
            
            extract_image_block_types      = ['Image'],     # Extract images as blocks
            # image_output_dir_path          = output_path, # If NONE, images and tables will be saved in base64
            extract_image_block_to_payload = True,          # If True, will extract base64 for API usage
            
            chunking_strategy              = 'by_title',    # Chunking strategy to use
            max_characters                 = 10000,         # Maximum characters per chunk
            combine_text_under_n_chars     = 2000,          # Combine text blocks under this many characters
            new_after_n_chars              = 6000           # New chunk after this many characters
        )
        
        
        # Step 2: Separate into text, tables, and images
        texts, tables, images = [], [], []
        
        for chunk in chunks:
            if 'Table' in str(type(chunk)): tables.append(chunk)
            
            elif 'CompositeElement' in str(type(chunk)):
                texts.append(chunk)
                
                for element in chunk.metadata.orig_elements:
                    if   'Image' in str(type(element)): images.append(element.metadata.image_base64)
                    elif 'Table' in str(type(element)): tables.append(element)
        
        logger.info(f"Found {len(texts)} text elements, {len(tables)} table elements, {len(images)} image elements")
        self.processing_results[original_name] = {'status': 'summarizing'}
        
        
        # Step 3: Summarize and store chunks in the RAG pipeline
        await self.rag_pipeline.process_document_chunks(texts, tables, images, original_name)
        self.processing_results[original_name] = {'status': 'complete'}


    def get_processing_status(self):
        """Get the current processing status for all files."""
        return self.processing_results