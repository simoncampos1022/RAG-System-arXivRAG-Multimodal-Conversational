"""
Image content processor for summarization.
"""
from typing import List, Any, Callable

from langchain_google_genai        import ChatGoogleGenerativeAI
from langchain_core.prompts        import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.config             import MODEL_NAME
from src.processors.prompts import IMAGE_SUMMARY_PROMPT


class ImageProcessor:
    """Image content processor for summarization."""
    
    def __init__(self, model_name: str = MODEL_NAME):
        """
        Initialize the image processor.
        
        Args:
            model_name (str): Name of the LLM model to use
        """
        self.llm   = ChatGoogleGenerativeAI(model=model_name)
        self.chain = self._create_summary_chain()
        
        
    def _create_summary_chain(self) -> Callable:
        """
        Create the image summarization chain.
        
        Returns:
            Callable: The image summarization chain
        """
        messages = [(
            'user',
            [
                {'type': 'text'     , 'text': IMAGE_SUMMARY_PROMPT},
                {'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,{image}'}}
            ]
        )]
        
        return (
            ChatPromptTemplate.from_messages(messages)
            | self.llm
            | StrOutputParser()
        )
    
    
    def process(self, images: List[Any]) -> List[str]:
        """
        Process and summarize image elements.
        
        Args:
            images (List[Any]): List of image elements to summarize
            
        Returns:
            List[str]: List of image summaries
        """
        summaries = []
        for image in images:
            summary = self.chain.invoke({'image': image.metadata.image_base64})
            summaries.append(summary)
        return summaries