"""
Table content processor for summarization.
"""
from typing import List, Any, Callable

from langchain_google_genai        import ChatGoogleGenerativeAI
from langchain_core.prompts        import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.config             import MODEL_NAME
from src.processors.prompts import TABLE_SUMMARY_PROMPT


class TableProcessor:
    """Table content processor for summarization."""
    
    def __init__(self, model_name: str = MODEL_NAME):
        """
        Initialize the table processor.
        
        Args:
            model_name (str): Name of the LLM model to use
        """
        self.llm                 = ChatGoogleGenerativeAI(model=model_name)
        self.chain = self._create_summary_chain()
   
        
    def _create_summary_chain(self) -> Callable:
        """
        Create the table summarization chain.
        
        Returns:
            Callable: The table summarization chain
        """
        return (
            {'table': lambda x: x}
            | ChatPromptTemplate.from_template(TABLE_SUMMARY_PROMPT)
            | self.llm
            | StrOutputParser()
        )
    
    
    def process(self, tables: List[Any]) -> List[str]:
        """
        Process and summarize table elements.
        
        Args:
            tables (List[Any]): List of table elements to summarize
            
        Returns:
            List[str]: List of table summaries
        """
        summaries = []
        
        for table in tables:
            summary = self.chain.invoke(table.metadata.text_as_html)
            summaries.append(summary)
            
        return summaries