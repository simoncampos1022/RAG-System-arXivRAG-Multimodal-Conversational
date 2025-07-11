"""
Demo script to show how to use the DocChat application.
"""
from src.config import DATA_DIR
from app        import RAGApp


if __name__ == '__main__':
    app = RAGApp()
    
    pdf_path = DATA_DIR / 'OpenAgentSafety.pdf'
    app.process_document(pdf_path)

    questions = [
        'How many tasks are included in the OpenAgentSafety benchmark?',
        'What are the eight safety risk categories evaluated by the framework?',
        'Which models were evaluated using OpenAgentSafety?',
        'What limitations of rule-based evaluators are addressed by LLM-as-Judge?',
        'What are the birthplaces of the authors of the paper?' # Unanswerable
    ]
    
    for question in questions:
        print(f"\n[Question]: {question}")
        
        response       = app.query(question)
        rag_response   = response['rag_response']
        retrieved_docs = response['retrieved_docs']
        
        print(f"[Answer]: {rag_response['response']}")
        print(f"[Retrieved Documents]:\n{retrieved_docs}")
        
        print('\n' + '-' * 80 + '\n')