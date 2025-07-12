"""
PDF document extraction utilities.
"""
from pathlib                    import Path
from typing                     import List, Dict, Any, Union
from unstructured.partition.pdf import partition_pdf

from src.config import PDF_EXTRACTION_CONFIG


def extract_from_pdf(pdf_path: Union[str, Path]) -> List[Any]:
    """
    Extract content from a PDF file using unstructured.
    
    Args:
        pdf_path (Union[str, Path]): Path to the PDF file
        
    Returns:
        List[Any]: List of extracted elements (text, tables, images)
    """
    pdf_path = Path(pdf_path) if isinstance(pdf_path, str) else pdf_path
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Extract content from PDF
    chunks = partition_pdf(filename=pdf_path, **PDF_EXTRACTION_CONFIG)
    return chunks


def separate_content_types(chunks: List[Any]) -> Dict[str, List[Any]]:
    """
    Separate the extracted content into text, images, and tables.
    
    Args:
        chunks (List[Any]): List of extracted elements from the PDF
        
    Returns:
        Dict[str, List[Any]]: Dictionary with keys 'texts', 'images', 'tables'
    """
    texts, images, tables = [], [], []
    for chunk in chunks:
        if   type(chunk).__name__ == 'Table': tables.append(chunk)
        elif type(chunk).__name__ == 'Image': images.append(chunk)
        
        elif type(chunk).__name__ == 'CompositeElement':
            texts.append(chunk)
            
            for element in chunk.metadata.orig_elements:
                if   type(element).__name__ == 'Image': images.append(element)
                elif type(element).__name__ == 'Table': tables.append(element)
    
    return {'texts': texts, 'images': images, 'tables': tables}