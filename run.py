import os
import uvicorn
from dotenv import load_dotenv
load_dotenv()

if __name__ == '__main__':
    print('Starting DocChat: Multi-modal RAG Application...')
    
    os.makedirs('app/uploads', exist_ok=True)
    uvicorn.run(
        'app.main:app',
        host   = '0.0.0.0',
        port   = 8000,
        reload = True
    )