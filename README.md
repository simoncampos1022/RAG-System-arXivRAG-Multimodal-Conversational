# DocChat: A Multimodal RAG Application

A fully functional Multi-modal Retrieval-Augmented Generation (RAG) application powered by LangChain and Gemini API, enabling seamless interaction and intelligent querying over PDF documents with text, tables, and images.



## Features

- **PDF Document Processing**: Upload and analyze PDFs with automatic partitioning into text, tables, and images
- **Multimodal RAG Pipeline**: Process and retrieve information from various content types
- **User-configurable Model Settings**: Choose from different Gemini models and set parameters
- **Interactive UI**: Clean and intuitive interface with a 2x2 grid layout
- **Citation Display**: See exactly which parts of your documents were used to generate answers

## Requirements

- Python 3.9+
- Google Gemini API Key
- Dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/DocChat-Multimodal-RAG-Application.git
   cd DocChat-Multimodal-RAG-Application
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python run.py
   ```

4. Open your browser and navigate to `http://localhost:8000`

## Usage

1. **Configure the RAG System**:
   - Enter your Gemini API key
   - Select a model from the available options
   - Set the temperature parameter

2. **Upload PDF Files**:
   - Drag and drop or browse to select PDF files
   - Click "Upload Files" to submit them

3. **Analyze Documents**:
   - Click "Analyze Documents" to process the uploaded PDFs
   - Wait for the processing to complete

4. **Ask Questions**:
   - Type your question in the query box
   - View the answer and supporting citations

## Architecture

- **Backend**: FastAPI with Uvicorn server
- **Frontend**: HTML, CSS, and JavaScript
- **Document Processing**: Unstructured library for PDF partitioning
- **Embedding & Retrieval**: LangChain's MultiVectorRetriever with Hugging Face embeddings
- **Language Model**: Google's Gemini API for summarization and response generation
