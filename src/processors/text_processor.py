"""
Text content processor for summarization.
"""
from typing import List, Any, Callable

from langchain_google_genai        import ChatGoogleGenerativeAI
from langchain_core.prompts        import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.config             import MODEL_NAME
from src.processors.prompts import TEXT_SUMMARY_PROMPT


class TextProcessor:
    """Text content processor for summarization."""
    
    def __init__(self, model_name: str = MODEL_NAME):
        """
        Initialize the text processor.
        
        Args:
            model_name (str): Name of the LLM model to use
        """
        self.llm   = ChatGoogleGenerativeAI(model=model_name)
        self.chain = self._create_summary_chain()
        
        
    def _create_summary_chain(self) -> Callable:
        """
        Create the text summarization chain.
        
        Returns:
            Callable: The text summarization chain
        """
        return (
            {'text': lambda x: x}
            | ChatPromptTemplate.from_template(TEXT_SUMMARY_PROMPT)
            | self.llm
            | StrOutputParser()
        )
    
    
    def process(self, texts: List[Any]) -> List[str]:
        """
        Process and summarize text elements.
        
        Args:
            texts (List[Any]): List of text elements to summarize
            
        Returns:
            List[str]: List of text summaries
        """
        summaries = []
        for text in texts:
            summary = self.chain.invoke(text.text)
            summaries.append(summary) 
        return summaries