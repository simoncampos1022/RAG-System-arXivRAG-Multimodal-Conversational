/**
 * Chat Manager for the arXivCSRAG application
 * Handles chat interactions and state
 */

class ChatManager {
    constructor(uiManager) {
        this.uiManager        = uiManager;
        this.currentPaperPath = null;
        this.isProcessed      = false;
        
        // Initialize chat events
        this.initEvents();
    }
    
    /**
     * Initialize chat event listeners
     */
    initEvents() {
        const chatInput   = document.getElementById('chat-input');
        const sendButton  = document.getElementById('send-message-btn');
        const resetButton = document.getElementById('reset-chat-btn');
        
        // Send message on button click
        sendButton.addEventListener('click', () => {
            this.sendMessage();
        });
        
        // Send message on Enter key (but allow Shift+Enter for new lines)
        chatInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                this.sendMessage();
            }
        });
        
        // Reset chat
        resetButton.addEventListener('click', () => {
            this.resetChat();
        });
    }
    
    /**
     * Send a message to the API
     */
    async sendMessage() {
        const chatInput = document.getElementById('chat-input');
        const message   = chatInput.value.trim();
        
        if (!message || !this.isProcessed) {
            return;
        }
        
        // Add user message to chat
        this.uiManager.addChatMessage(message, true);
        
        // Clear input
        chatInput.value = '';
        
        // Disable chat while waiting for response
        this.uiManager.disableChat();
        this.uiManager.showLoading('Getting answer...');
        
        try {
            // Send message to API
            const response = await ApiService.chatWithPaper(message);
            
            if (response.status === 'success') {
                // Add bot response to chat
                this.uiManager.addChatMessage(response.response, false, response.citations);
            } else {
                this.uiManager.addSystemMessage('Error: Failed to get a response. Please try again.');
            }
        } catch (error) {
            console.error('Error in chat:', error);
            this.uiManager.addSystemMessage('Error: An unexpected error occurred. Please try again.');
        } finally {
            // Re-enable chat
            this.uiManager.enableChat();
            this.uiManager.hideLoading();
        }
    }
    

    /**
     * Process a paper for chatting
     * @param {string} filePath - Path to the paper file
     */
    async processPaper(filePath) {
        if (!filePath) {
            this.uiManager.addSystemMessage('Error: No paper file specified.');
            return;
        }
        
        this.currentPaperPath = filePath;
        this.uiManager.clearChat();
        this.uiManager.disableChat();
        this.uiManager.showLoading('Processing paper... This may take about 1-2 minutes.');
        
        try {
            const response = await ApiService.processPaper(filePath);
            
            if (response.status === 'success') {
                this.isProcessed = true;
                this.uiManager.enableChat();
                this.uiManager.addSystemMessage(
                    `Extracted ${response.stats.texts} text chunks, ${response.stats.tables} tables, and ${response.stats.images} images.<br>
                    Paper processed successfully! You can now ask question about the paper.<br>`
                );
            } else {
                this.uiManager.addSystemMessage('Error: Failed to process paper. Please try again.');
            }
        } catch (error) {
            console.error('Error processing paper:', error);
            this.uiManager.addSystemMessage('Error: An unexpected error occurred while processing the paper. Please try again.');
        } finally {
            this.uiManager.hideLoading();
        }
    }
    

    /**
     * Reset the chat session
     */
    async resetChat() {
        this.uiManager.showLoading('Resetting chat...');
        
        try {
            await ApiService.resetChat();
            this.isProcessed = false;
            this.currentPaperPath = null;
            this.uiManager.clearChat();
            this.uiManager.disableChat();
            this.uiManager.addSystemMessage('Select a paper from the search results or upload a PDF to start chatting.');
        } catch (error) {
            console.error('Error resetting chat:', error);
            this.uiManager.addSystemMessage('Error: Failed to reset chat. Please try again.');
        } finally {
            this.uiManager.hideLoading();
        }
    }
    

    /**
     * Download and process a paper by arXiv ID
     * @param {string} arxivId - The arXiv ID of the paper
     */
    async downloadAndProcessPaper(arxivId) {
        this.uiManager.showLoading('Downloading paper...');
        
        try {
            const response = await ApiService.downloadPaper(arxivId);
            
            if (response.status === 'success') {
                this.uiManager.hideModal(this.uiManager.paperInfoModal);
                await this.processPaper(response.file_path);
            } else {
                this.uiManager.addSystemMessage('Error: Failed to download paper. Please try again.');
                this.uiManager.hideLoading();
            }
        } catch (error) {
            console.error('Error downloading paper:', error);
            this.uiManager.addSystemMessage('Error: An unexpected error occurred while downloading the paper. Please try again.');
            this.uiManager.hideLoading();
        }
    }
}