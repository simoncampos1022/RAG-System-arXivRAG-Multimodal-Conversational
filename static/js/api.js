/**
 * API Service for the arXivCSRAG application
 * Manages all API requests to the backend
 */

class ApiService {
    /**
     * Configure API keys
     * @param   {string} geminiApiKey     - The Google Gemini API key
     * @param   {string} huggingfaceToken - The Hugging Face token
     * @returns {Promise}                 - The API response
     */
    static async configureApiKeys(geminiApiKey, huggingfaceToken) {
        try {
            const response = await fetch('/api/configure', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    gemini_api_key   : geminiApiKey,
                    huggingface_token: huggingfaceToken
                })
            });
            
            return await response.json();
        } catch (error) {
            console.error('Error configuring API keys:', error);
            throw error;
        }
    }


    /**
     * Fetch papers from arXiv
     * @param   {Object} searchParams - The search parameters
     * @returns {Promise}             - The API response
     */
    static async fetchPapers(searchParams) {
        try {
            const response = await fetch('/api/fetch-papers', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(searchParams)
            });
            
            return await response.json();
        } catch (error) {
            console.error('Error fetching papers:', error);
            throw error;
        }
    }


    /**
     * Get paper metadata
     * @param   {string} arxivId - The arXiv ID of the paper
     * @returns {Promise}        - The API response
     */
    static async getPaperMetadata(arxivId) {
        try {
            const response = await fetch('/api/paper-metadata', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    arxiv_id: arxivId
                })
            });
            
            return await response.json();
        } catch (error) {
            console.error('Error getting paper metadata:', error);
            throw error;
        }
    }


    /**
     * Download a paper
     * @param   {string} arxivId - The arXiv ID of the paper
     * @returns {Promise}        - The API response
     */
    static async downloadPaper(arxivId) {
        try {
            const response = await fetch('/api/download-paper', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    arxiv_id: arxivId
                })
            });
            
            return await response.json();
        } catch (error) {
            console.error('Error downloading paper:', error);
            throw error;
        }
    }


    /**
     * Upload a paper
     * @param   {File} file - The PDF file to upload
     * @returns {Promise}   - The API response
     */
    static async uploadPaper(file) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch('/api/upload-paper', {
                method: 'POST',
                body  : formData
            });
            
            return await response.json();
        } catch (error) {
            console.error('Error uploading paper:', error);
            throw error;
        }
    }


    /**
     * Process a paper for RAG
     * @param   {string} filePath - The path to the PDF file
     * @returns {Promise}         - The API response
     */
    static async processPaper(filePath) {
        try {
            const formData = new FormData();
            formData.append('file_path', filePath);
            
            const response = await fetch('/api/process-paper', {
                method: 'POST',
                body  : formData
            });
            
            return await response.json();
        } catch (error) {
            console.error('Error processing paper:', error);
            throw error;
        }
    }


    /**
     * Chat with a processed paper
     * @param   {string} message - The user's message
     * @returns {Promise}        - The API response
     */
    static async chatWithPaper(message) {
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message
                })
            });
            
            return await response.json();
        } catch (error) {
            console.error('Error chatting with paper:', error);
            throw error;
        }
    }


    /**
     * Reset the chat
     * @returns {Promise} - The API response
     */
    static async resetChat() {
        try {
            const response = await fetch('/api/reset-chat', {
                method: 'POST'
            });
            
            return await response.json();
        } catch (error) {
            console.error('Error resetting chat:', error);
            throw error;
        }
    }


    /**
     * Fetch citations for a specific query
     * @param   {string} message - The query message
     * @returns {Promise}        - The API response with citations
     */
    static async fetchCitations(message) {
        try {
            const response = await fetch('/api/fetch-citations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message
                })
            });
            
            return await response.json();
        } catch (error) {
            console.error('Error fetching citations:', error);
            throw error;
        }
    }
}