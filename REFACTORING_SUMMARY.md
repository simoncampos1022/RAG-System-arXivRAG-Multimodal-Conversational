# DocChat Multimodal RAG Application - Refactoring Summary

## Files Created

1. **Application Core**
   - `app.py` - Main application class with high-level interfaces
   - `demo.py` - Demo script to showcase the application
   - `src/config.py` - Configuration settings and constants

2. **Data Extraction**
   - `src/data_extraction/__init__.py`
   - `src/data_extraction/extractor.py` - PDF extraction utilities

3. **Content Processors**
   - `src/processors/__init__.py`
   - `src/processors/prompts.py` - LLM prompt templates
   - `src/processors/text_processor.py` - Text summarization
   - `src/processors/table_processor.py` - Table summarization
   - `src/processors/image_processor.py` - Image summarization

4. **Storage**
   - `src/storage/__init__.py`
   - `src/storage/vectorstore.py` - Vector database implementation

5. **RAG Pipeline**
   - `src/rag/__init__.py`
   - `src/rag/pipeline.py` - RAG query pipeline

6. **Documentation**
   - `README.md` - Project documentation

## Key Components

### DocChatApp (app.py)
The main application class that coordinates all components and provides a high-level API.

### Data Extraction (extractor.py)
Extracts and separates content from PDF documents into text, tables, and images.

### Content Processors
Process and summarize different types of content:
- `TextProcessor`: Summarizes text content
- `TableProcessor`: Summarizes table content
- `ImageProcessor`: Summarizes image content

### VectorStore (vectorstore.py)
Handles storage and retrieval of content using embeddings and vector search.

### RAGPipeline (pipeline.py)
Implements the RAG query pipeline, combining retrieval and generation to answer questions.

## Usage Examples

### Basic Usage
```python
from app import DocChatApp

app = DocChatApp()
app.process_document('data/document.pdf')
response = app.query("What is the main topic of this document?")
print(response['response'])
```

### Command Line
```bash
python app.py --pdf data/OpenAgentSafety.pdf --query "What limitations of rule-based evaluators are addressed by LLM-as-Judge?"
```

## Notes

1. The application uses Google's Gemini model for content summarization and question answering.
2. Document processing involves extracting, summarizing, and storing content in a vector database.
3. The RAG pipeline retrieves relevant content and generates answers based on the retrieved content.
4. The modular design makes it easy to extend and customize the application.

## Next Steps

1. Add testing for each component
2. Implement a web interface
3. Add support for more document types
4. Optimize embedding and retrieval for larger document sets
