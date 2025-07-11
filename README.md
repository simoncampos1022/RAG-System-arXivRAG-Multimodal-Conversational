# arXivRAG - Multimodal RAG Chatbot Application

A modular and extensible multimodal Retrieval-Augmented Generation (RAG) application for document querying.

## Overview

arXivRAG is a RAG application that can:

1. Extract text, tables, and images from PDF documents
2. Process and summarize each type of content using LLM chains
3. Store the content and summaries in a vector database for retrieval
4. Answer questions based on the retrieved documents

## Project Structure

```
DocChat-MultimodalRAG-Application/
├── app.py                    # Main application class
├── demo.py                   # Demo script
├── config.py                 # Configuration settings
├── requirements.txt
├── assets/                   # Project assets
├── data/                     # PDF documents
├── demo/                     # Demo files
└── src/                      # Source code
    ├── data_extraction/      # PDF extraction components
    │   ├── extractor.py
    ├── processors/           # Content processors
    │   ├── text_processor.py
    │   ├── table_processor.py
    │   ├── image_processor.py
    │   ├── prompts.py
    ├── storage/              # Vector storage
    │   ├── vectorstore.py
    └── rag/                  # RAG pipeline
        ├── pipeline.py
```

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd DocChat-MultimodalRAG-Application
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory with your API keys:
   ```
   HF_TOKEN=your_huggingface_token
   GOOGLE_API_KEY=your_google_api_key
   ```

## Usage

### Command Line

Process a document and query it:

```bash
python app.py --pdf data/OpenAgentSafety.pdf --query "What limitations of rule-based evaluators are addressed by LLM-as-Judge?"
```

Reset the vector store:

```bash
python app.py --reset
```

### Run the Demo

```bash
python demo.py
```

## Extending the Application

### Adding New Document Types

Implement a new extractor in `src/data_extraction/` following the pattern in `extractor.py`.

### Adding New Content Processors

Implement a new processor in `src/processors/` following the patterns in the existing processor files.

### Customizing the RAG Pipeline

Modify `src/rag/pipeline.py` to customize the retrieval and generation processes.

## License

See the [LICENSE](LICENSE) file for details.
