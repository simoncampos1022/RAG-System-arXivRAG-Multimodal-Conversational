"""
RAG pipeline implementation.
"""
from typing   import Dict, List, Any, Callable
from operator import itemgetter

from langchain_google_genai            import ChatGoogleGenerativeAI
from langchain_core.prompts            import ChatPromptTemplate
from langchain_core.messages           import SystemMessage, HumanMessage
from langchain_core.runnables          import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers     import StrOutputParser
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain.memory.summary          import ConversationSummaryMemory

from src.config             import MODEL_NAME
from src.processors.prompts import RAG_SYSTEM_MESSAGE


class RAGPipeline:
    """RAG pipeline implementation."""
    
    def __init__(self, retriever: MultiVectorRetriever, model_name: str = MODEL_NAME):
        """
        Initialize the RAG pipeline.
        
        Args:
            retriever (MultiVectorRetriever): The document retriever
            model_name                 (str): Name of the LLM model to use
        """
        self.retriever = retriever
        self.llm       = ChatGoogleGenerativeAI(model=model_name)
        self.rag_chain = self._create_rag_chain()
        self.memory    = ConversationSummaryMemory(
            llm=self.llm,
            memory_key="chat_history",
            return_messages=True,
            input_key="question",
            output_key="response"
        )
        
        
    def parse_docs(self, docs: List[Any]) -> Dict[str, List[Any]]:
        """
        Parse the retrieved documents into text, image, and table lists.
        
        Args:
            docs (List[Any]): List of retrieved documents
            
        Returns:
            Dict[str, List[Any]]: Dictionary with keys 'texts', 'images', 'tables'
        """
        parsed_texts, parsed_images, parsed_tables = [], [], []

        for doc in docs:
            if   type(doc).__name__ == 'Table'           : parsed_tables.append(doc.metadata.text_as_html)
            elif type(doc).__name__ == 'Image'           : parsed_images.append(doc.metadata.image_base64)
            elif type(doc).__name__ == 'CompositeElement': parsed_texts.append(doc.text)

        return {'texts': parsed_texts, 'images': parsed_images, 'tables': parsed_tables}
    
    
    def _build_prompt(self, kwargs: Dict[str, Any]) -> ChatPromptTemplate:
        """
        Build the prompt template for the RAG query.
        
        Args:
            kwargs (Dict[str, Any]): Dictionary with keys 'context', 'question', and 'chat_history'
            
        Returns:
            ChatPromptTemplate: The chat prompt template
        """
        context      = kwargs['context']
        question     = kwargs['question']
        chat_history = kwargs.get('chat_history', [])
    
        messages = [SystemMessage(content=RAG_SYSTEM_MESSAGE)]
        
        # Add conversation history if available
        if chat_history:
            messages.extend(chat_history)
        
        for txt in context['texts'] : messages.append(HumanMessage(content=[{'type': 'text', 'text': f"[TEXT]:\n{txt}"}]))
        for tbl in context['tables']: messages.append(HumanMessage(content=[{'type': 'text', 'text': f"[TABLE]:\n```html\n{tbl}\n```"}]))
        for img in context['images']:
            messages.append(
                HumanMessage(content=[{'type': 'text'     , 'text': f"[IMAGE]:\n"},
                                      {'type': 'image_url', 'image_url': {'url': f"data:image/jpeg;base64,{img}"}}])
            )
            
        messages.append(
            HumanMessage(content=[{'type': 'text',
                                   'text': f"Based on the above contexts and our conversation history, answer the question: {question}"}])
        )
        return ChatPromptTemplate.from_messages(messages)
    
    
    def _create_rag_chain(self) -> Callable:
        """
        Create the RAG chain.
        
        Returns:
            Callable: The RAG chain
        """
        return (
            {
                'context'     : itemgetter('question') | RunnableLambda(lambda q: f"query: {q}") | self.retriever | RunnableLambda(self.parse_docs),
                'question'    : itemgetter('question'),
                'chat_history': itemgetter('chat_history')
            }
            | RunnablePassthrough().assign(
                response=(
                    RunnableLambda(self._build_prompt)
                    | self.llm
                    | StrOutputParser()
                )
            )
        )
    
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Query the RAG pipeline.
        
        Args:
            question (str): The question to answer
            
        Returns:
            Dict[str, Any]: Dictionary with keys 'question', 'context', and 'response'
        """
        # Get chat history from memory
        chat_history = self.memory.load_memory_variables({})
        
        # Execute the query with the chat history
        result = self.rag_chain.invoke({
            'question': question, 
            'chat_history': chat_history.get('chat_history', [])
        })
        
        # Update memory with the new interaction
        self.memory.save_context(
            {"question": question},
            {"response": result['response']}
        )
        
        return result
        
    def reset_memory(self):
        """Reset the conversation memory."""
        self.memory.clear()