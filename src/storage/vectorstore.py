"""
Vector storage and retrieval implementation.
"""
import uuid
from typing import List, Any

from langchain_chroma                  import Chroma
from langchain.storage                 import InMemoryStore
from langchain.schema.document         import Document
from langchain_huggingface             import HuggingFaceEmbeddings
from langchain.retrievers.multi_vector import MultiVectorRetriever

from src.config import EMBEDDING_MODEL, DEVICE, COLLECTION_NAME


class VectorStore:
    """Vector storage and retrieval implementation."""
    
    def __init__(self, collection_name: str = COLLECTION_NAME, embedding_model: str = EMBEDDING_MODEL):
        """
        Initialize the vector store.
        
        Args:
            collection_name (str): Name of the vector store collection
            embedding_model (str): Name of the embedding model to use
        """
        self.embedding_function = self._create_embedding_function(embedding_model)
        self.vector_store       = self._create_vector_store(collection_name)
        self.doc_store          = InMemoryStore()
        self.id_key             = 'doc_id'
        self.retriever          = self._create_retriever()


    def _create_embedding_function(self, model_name: str) -> HuggingFaceEmbeddings:
        """
        Create an embedding function.
        
        Args:
            model_name (str): Name of the embedding model
            
        Returns:
            HuggingFaceEmbeddings: The embedding function
        """
        return HuggingFaceEmbeddings(
            model_name    = model_name,
            model_kwargs  = {'device': DEVICE},
            encode_kwargs = {'normalize_embeddings': True} # Change this if use an already normalized model
        )
    
    
    def _create_vector_store(self, collection_name: str) -> Chroma:
        """
        Create a vector store.
        
        Args:
            collection_name (str): Name of the vector store collection
            
        Returns:
            Chroma: The vector store
        """
        return Chroma(
            collection_name    = collection_name,
            embedding_function = self.embedding_function,
        )
    
    
    def _create_retriever(self) -> MultiVectorRetriever:
        """
        Create a multi-vector retriever.
        
        Returns:
            MultiVectorRetriever: The retriever
        """
        return MultiVectorRetriever(
            vectorstore = self.vector_store,
            docstore    = self.doc_store,
            id_key      = self.id_key,
        )
    
    
    def add_to_retriever(self, data: List[Any], data_summaries: List[str]) -> None:
        """
        Add data and summaries to the retriever.
        
        Args:
            data           (List[Any]): List of data elements
            data_summaries (List[str]): List of data summaries
        """
        if not data:
            return

        if len(data) != len(data_summaries):
            raise ValueError(f"Length mismatch: {len(data)} data but {len(data_summaries)} summaries")
    
        ids = [str(uuid.uuid4()) for _ in range(len(data))]
        
        summaries = [
            Document(
                page_content = f"passage: {summary}", # Change this to suit with model requirements if use a different model
                metadata     = {self.id_key: i}
            )
            for i, summary in zip(ids, data_summaries)
        ]
        
        self.retriever.vectorstore.add_documents(summaries)
        self.retriever.docstore.mset(list(zip(ids, data)))
        
        
    def add_contents(self, 
                     texts : List[Any], text_summaries : List[str],
                     tables: List[Any], table_summaries: List[str],
                     images: List[Any], image_summaries: List[str]) -> None:
        """
        Add all content types and their summaries to the retriever.
        
        Args:
            texts           (List[Any]): List of text elements
            text_summaries  (List[str]): List of text summaries
            tables          (List[Any]): List of table elements
            table_summaries (List[str]): List of table summaries
            images          (List[Any]): List of image elements
            image_summaries (List[str]): List of image summaries
        """
        self.add_to_retriever(texts , text_summaries)
        self.add_to_retriever(tables, table_summaries)
        self.add_to_retriever(images, image_summaries)
        
        
    def reset(self) -> None:
        """Reset the vector store and document store."""
        try:
            self.vector_store.reset_collection()
        except Exception as e:
            raise RuntimeError(f"Failed to reset vector store: {e}")
        
        # self.vector_store = self._create_vector_store(COLLECTION_NAME)
        self.doc_store    = InMemoryStore()
        self.retriever    = self._create_retriever()
        
        
    def retrieve(self, query: str) -> List[Any]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query (str): The query string
            
        Returns:
            List[Any]: List of retrieved documents
        """
        return self.retriever.invoke(query)