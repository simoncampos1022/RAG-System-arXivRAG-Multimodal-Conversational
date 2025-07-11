"""Main entry point."""

import argparse
import logging
from pathlib import Path
from typing  import Dict, Any, List

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from src.data_extraction.extractor  import extract_from_pdf, separate_content_types
from src.processors.text_processor  import TextProcessor
from src.processors.table_processor import TableProcessor
from src.processors.image_processor import ImageProcessor
from src.storage.vectorstore        import VectorStore
from src.rag.pipeline               import RAGPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGApp:
    """arXivCSRAG: Multimodal RAG Application."""
    
    def __init__(self):
        """Initialize the arXivCSRAG application."""
        self.text_processor  = TextProcessor()
        self.table_processor = TableProcessor()
        self.image_processor = ImageProcessor()
        self.vector_store    = VectorStore()
        self.rag_pipeline    = RAGPipeline(self.vector_store.retriever)


    def process_document(self, pdf_path: Path) -> Dict[str, List[Any]]:
        """
        Process a PDF document.
        
        Args:
            pdf_path (Path): Path to the PDF document
            
        Returns:
            Dict[str, List[Any]]: Dictionary with processed content
        """
        logger.info(f"Processing document: {pdf_path}")
        
        # Extract content from PDF
        chunks = extract_from_pdf(pdf_path)
        logger.info(f"Extracted {len(chunks)} chunks from the document")
        
        # Separate content types
        content = separate_content_types(chunks)
        logger.info(f"Separated into {len(content['texts'])} texts, {len(content['images'])} images, {len(content['tables'])} tables")
        
        
        # Process and summarize content
        logger.info("Summarizing text content...")
        text_summaries = self.text_processor.process(content['texts'])

        logger.info("Summarizing table content...")
        table_summaries = self.table_processor.process(content['tables'])

        logger.info("Summarizing image content...")
        image_summaries = self.image_processor.process(content['images'])
        
        
        # Add to vector store
        logger.info("Adding content to vector store...")
        self.vector_store.add_contents(
            content['texts'] , text_summaries,
            content['tables'], table_summaries,
            content['images'], image_summaries
        )
        
        
    def query(self, question: str) -> Dict[str, Any]:
        """
        Query the RAG pipeline.
        
        Args:
            question (str): The question to answer
            
        Returns:
            Dict[str, Any]: The RAG response
        """
        return {
            'rag_response'  : self.rag_pipeline.query(question),
            'retrieved_docs': self.vector_store.retrieve(question)
        }
    
    
    def reset_vector_store(self) -> None:
        """Reset the vector store."""
        logger.info("Resetting vector store...")
        self.vector_store.reset()
        logger.info("Vector store reset complete.")
       

if __name__ == '__main__':
    logger.info("Starting arXivCSRAG Application...")

    parser = argparse.ArgumentParser(description='arXivCSRAG Application')
    
    parser.add_argument('--pdf'  , type=str           , help='Path to the PDF document')
    parser.add_argument('--query', type=str           , help='Question to ask')
    parser.add_argument('--reset', action='store_true', help='Reset the vector store')
    
    args = parser.parse_args()
    app  = RAGApp()

    if args.reset:
        app.reset_vector_store()
        
    if args.pdf:
        pdf_path = Path(args.pdf)
        app.process_document(pdf_path)
        
    if args.query:
        response       = app.query(args.query)
        rag_response   = response['rag_response']
        retrieved_docs = response['retrieved_docs']

        print(f"\n[Question]: {args.query}")
        print(f"\n[Answer]: {rag_response['response']}")