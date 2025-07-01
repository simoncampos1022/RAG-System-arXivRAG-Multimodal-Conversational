import os
import torch
import uuid
import asyncio
import logging
from typing import Dict, Any
from bs4 import BeautifulSoup
from operator import itemgetter

# LangChain imports
from langchain_google_genai            import ChatGoogleGenerativeAI
from langchain.vectorstores            import Chroma
from langchain.storage                 import InMemoryStore
from langchain.schema.document         import Document
from langchain.embeddings              import HuggingFaceEmbeddings
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain_core.prompts            import ChatPromptTemplate
from langchain_core.output_parsers     import StrOutputParser
from langchain_core.runnables          import RunnablePassthrough, RunnableLambda
from langchain_core.messages           import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Retrieval-Augmented Generation (RAG) pipeline for multimodal document processing.
    """
    
    def __init__(self, api_key: str, model_name: str, temperature: float = 0.7):
        """
        Initialize the RAG pipeline.
        
        Args:
            api_key    : Google API key for Gemini
            model_name : Gemini model name
            temperature: Temperature parameter for generation
        """
        
        # Set the API key
        os.environ['GOOGLE_API_KEY'] = api_key
        
        # Initialize the LLM
        self.model_name  = model_name
        self.temperature = temperature
        self.llm = ChatGoogleGenerativeAI(
            model       = model_name,
            temperature = temperature
        )
        
        # Initialize vector store
        self.vector_store = Chroma(
            collection_name    = 'multimodal_rag',
            embedding_function = HuggingFaceEmbeddings(
                model_name   = 'sentence-transformers/all-mpnet-base-v2',
                model_kwargs = {'device': 'cuda' if torch.cuda.is_available() else 'cpu'}
            )
        )
        
        # Storage layer for managing documents
        self.doc_store = InMemoryStore()
        self.id_key    = 'doc_id'
        
        # The retriever for querying the vector store
        self.retriever = MultiVectorRetriever(
            vectorstore = self.vector_store,
            docstore    = self.doc_store,
            id_key      = self.id_key
        )
        
        # Build the RAG chain
        self.chain = self._build_rag_chain()
        logger.info(f"Initialized RAG pipeline with model: {model_name}")
    
    
    async def process_document_chunks(self, texts, tables, images, source_name):
        """
        Process and store document chunks.
        
        Args:
            texts      : List of text chunks
            tables     : List of table chunks
            images     : List of image base64 strings
            source_name: Name of the source document
        """
        
        logger.info(f"Processing chunks from {source_name}")
        
        # Summarize texts
        text_summaries = await self._summarize_texts(texts)
        
        # Summarize tables
        tables_html     = [table.metadata.text_as_html for table in tables]
        table_summaries = await self._summarize_texts(tables_html)
        
        # Summarize images
        image_summaries = await self._summarize_images(images)
        
        # Add chunks to retriever
        self._add_chunks_to_retriever(texts,  text_summaries,  source_name, 'text')
        self._add_chunks_to_retriever(tables, table_summaries, source_name, 'table')
        self._add_chunks_to_retriever(images, image_summaries, source_name, 'image')

        logger.info(f"Added {len(texts)} texts, {len(tables)} tables, {len(images)} images to vector store")
    
    
    async def _summarize_texts(self, texts):
        """Summarize text and table chunks."""
        
        prompt_for_txt = """
        ### ROLE ###
        You are an expert summarization engine.

        ### TASK ###
        Analyze the provided text or table and generate a concise, standalone summary.

        ### RULES ###
        1.  **Concise:** Capture only the most critical information.
        2.  **Standalone:** The summary must be fully understandable on its own.
        3.  **No Preamble:** Do not add introductory sentences like "Here is the summary:".
        4.  **Raw Output:** Your response must contain ONLY the summary text and nothing else.

        ### EXAMPLE ###
        INPUT:
        | Region | Sales Q1 | Sales Q2 | Growth |
        |---|---|---|---|
        | North | 1.2M | 1.5M | +25% |
        | South | 2.0M | 2.1M | +5% |

        OUTPUT:
        The North region's sales grew 25% from 1.2M to 1.5M between Q1 and Q2, while the South region saw a 5% increase from 2.0M to 2.1M.

        ---

        ### YOUR TASK ###
        INPUT:
        {element}

        OUTPUT:
        """

        txt_summarize_chain = (
            {'element': lambda x: x}
            | ChatPromptTemplate.from_template(prompt_for_txt)
            | self.llm
            | StrOutputParser()
        )
        
        summaries = []
        for text in texts:
            try:
                summary = await asyncio.to_thread(txt_summarize_chain.invoke, text)
                summaries.append(summary)
            except Exception as e:
                logger.error(f"Error summarizing text: {e}")
                summaries.append('Error generating summary')
        
        return summaries
    
    
    async def _summarize_images(self, images):
        """Summarize image chunks."""
        
        prompt_for_img = """
        ### ROLE ###
        You are an expert summarization engine.

        ### TASK ###
        Analyze the provided image with a focus on its technical and data components. Follow these steps:

        1.  **Overall Summary:**
        - Briefly describe the image and its main subject in one or two sentences.

        2.  **Technical Element Analysis:**
        - Identify and explain any of the following technical elements present:
            - **Diagrams or Schematics:** Describe what they illustrate (e.g., a network architecture, a process flow).
            - **Annotations and Labels:** List key labels and explain what they point to or clarify.
            - **Visual Structures:** Describe any flowcharts, tables, or other organizational layouts.

        3.  **Graph/Chart Breakdown:**
        - If a graph or chart is present, provide the following details. If not, state "No graph present."
            - **Type:** e.g., Bar chart, line graph, pie chart, scatter plot.
            - **X-Axis:** Label and what it represents.
            - **Y-Axis:** Label and what it represents.
            - **Legend:** Explain what each color or symbol represents.
            - **Key Insights:** Summarize the main trend, key comparisons, or significant outliers shown in the data.

        ### RULES ###
        1.  **Concise:** Capture only the most critical information.
        2.  **Standalone:** The summary must be fully understandable on its own.
        3.  **No Preamble:** Do not add introductory sentences like "Here is the summary:".
        4.  **Raw Output:** Your response must contain ONLY the summary text and nothing else.
        """

        messages = [(
            'user',
            [
                {'type': 'text', 'text': prompt_for_img},
                {
                    'type'     : 'image_url',
                    'image_url': {'url': 'data:image/jpeg;base64,{image}'}
                }
            ]
        )]

        img_summarize_chain = (
            ChatPromptTemplate.from_messages(messages)
            | self.llm
            | StrOutputParser()
        )
        
        summaries = []
        for img in images:
            try:
                summary = await asyncio.to_thread(img_summarize_chain.invoke, {"image": img})
                summaries.append(summary)
            except Exception as e:
                logger.error(f"Error summarizing image: {e}")
                summaries.append("Error generating summary")
        
        return summaries
    
    
    def _add_chunks_to_retriever(self, data, data_summaries, source_name, data_type):
        """Add data chunks to the retriever."""
        
        ids = [str(uuid.uuid4()) for _ in data]
        
        summarized_chunks = [
            Document(
                page_content = summary, 
                metadata     = {
                    self.id_key: chunk_id,
                    'source'   : source_name,
                    'type'     : data_type
                }
            )
            for chunk_id, summary in zip(ids, data_summaries)
        ]
        
        self.retriever.vectorstore.add_documents(summarized_chunks)
        self.retriever.docstore.mset(list(zip(ids, data)))
    
    
    def _build_rag_chain(self):
        """Build the RAG chain for querying."""
        
        SYSTEM_MSG = """
        ### ROLE ###
        You are a RAG (Retrieval-Augmented Generation) assistant.

        ### PRIMARY DIRECTIVE ###
        Your answer **MUST** be based **exclusively** on the provided context pieces (e.g., `[Text_id=1]`, `[Table_id=1]`, `[Image_id=1]`). Do not use any prior knowledge.

        ### CRITICAL RULES ###
        1.  **Source Requirement:** You **MUST** ground your entire answer in the provided context.
        2.  **"I Don't Know" Condition:** If the provided context does not contain the information needed to answer the question, you **MUST** reply with the exact phrase: `I don't know.`
        3.  **Table Interpretation:** When processing a context piece with a `Table_id`, correctly interpret any `rowspan` and `colspan` attributes in the HTML.

        ### OUTPUT FORMAT ###
        1.  **Content:** Generate the answer in Markdown.
        2.  **Citations:** The final line of your response **MUST** be the citation list.
            - **Format:** Start the line with `Citations: `
            - **Example:** `Citations: [Text_id=1], [Image_id=2], [Table_id=3]`
        """
        
        # Function to parse retrieved documents
        def parse_docs(docs):
            texts, tables, images = [], [], []
            for doc in docs:
                if   isinstance(doc, str)     : images.append(doc)                       # base64 encod=ed image (str type)
                elif 'Table' in str(type(doc)): tables.append(doc.metadata.text_as_html) # raw HTML data (Table type)
                else                          : texts.append(doc.text)                   # raw text data (CompositeElement type)
            return {'texts': texts, 'tables': tables, 'images': images}
        
        
        # Function to minify HTML tables
        def minify_table(html_str):
            soup = BeautifulSoup(html_str, 'html.parser')
            for tag in soup.find_all(True):
                tag.attrs = {k: v for k, v in tag.attrs.items() if k in ('rowspan', 'colspan')}
            return " ".join(str(soup).split())
        
        
        # Function to build the prompt
        def build_prompt(kwargs):
            ctx = kwargs['context']
            q   = kwargs['question']
            
            messages = [SystemMessage(content=SYSTEM_MSG)]

            # Add text elements to context
            for id, text in enumerate(ctx['texts'], start=1):
                messages.append(
                    HumanMessage(content=[{'type': 'text',
                                           'text': f"[Text_id={id}]\n{text}"}])
                )
            
            # Add table elements to context
            for id, table in enumerate(ctx['tables'], start=1):
                minified_table = minify_table(table)
                messages.append(
                    HumanMessage(content=[{'type': 'text',
                                           'text': f"[Table_id={id}]\n```html\n{minified_table}\n```"}])
                )
                
            # Add image elements to context
            for id, image in enumerate(ctx['images'], start=1):
                messages.append(
                    HumanMessage(content=[{'type': 'text', 
                                           'text': f"[Image_id={id}]\n"},
                                          {'type'     : 'image_url',
                                           'image_url': {'url': f"data:image/jpeg;base64,{image}"}}])
                )

            # Add user question
            messages.append(HumanMessage(content=[{'type': 'text', 
                                                   'text': f"Question: {q}"}]))
            
            return ChatPromptTemplate.from_messages(messages)
        
        
        # Build the chain
        chain = (
            {
                'context' : itemgetter('question') | self.retriever | RunnableLambda(parse_docs),
                'question': itemgetter('question'),
            }
            | RunnablePassthrough().assign(
                response=(
                    RunnableLambda(build_prompt)
                    | self.llm
                    | StrOutputParser()
                )
            )
        )
        
        return chain
    
    
    async def query(self, question: str) -> Dict[str, Any]:
        """
        Process a user query using the RAG pipeline.
        
        Args:
            question: User's question
            
        Returns:
            Dictionary with response and context
        """
        
        try:
            # Invoke the chain
            result = await asyncio.to_thread(self.chain.invoke, {'question': question})
            
            # Extract citations
            response_text = result['response']
            citations     = []
            
            # Extract citation information
            if 'Citations:' in response_text:
                response_parts = response_text.split('Citations:')
                response_text  = response_parts[0].strip()
                citations_text = response_parts[1].strip()
                
                # Parse citation IDs
                import re
                citation_matches = re.findall(r'\[(Text|Table|Image)_id=(\d+)\]', citations_text)
                citations = [{'type': match[0].lower(), 'id': int(match[1])} for match in citation_matches]
            
            # Get context information
            context = result['context']
            
            # Prepare response with citations
            response = {
                'answer'   : response_text,
                'citations': citations,
                'context'  : {
                    'texts' : [{'id': i+1, 'content': text}  for i, text  in enumerate(context['texts'])],
                    'tables': [{'id': i+1, 'content': table} for i, table in enumerate(context['tables'])],
                    'images': [{'id': i+1, 'content': image} for i, image in enumerate(context['images'])]
                }
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'answer'   : 'An error occurred while processing your query.',
                'error'    : str(e),
                'citations': [],
                'context'  : {'texts': [], 'tables': [], 'images': []}
            }