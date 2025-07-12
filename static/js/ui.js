/**
 * UI Manager for the arXivCSRAG application
 * Handles UI elements, modals, and rendering
 */

class UIManager {
    constructor() {
        // Cache DOM elements
        this.apiKeysModal      = document.getElementById('api-keys-modal');
        this.paperInfoModal    = document.getElementById('paper-info-modal');
        this.loadingOverlay    = document.getElementById('loading-overlay');
        this.loadingMessage    = document.getElementById('loading-message');
        this.resultsContainer  = document.getElementById('results-container');
        this.chatMessages      = document.getElementById('chat-messages');
        this.subjectTagsSelect = document.getElementById('subject-tags-select');
        
        // Initialize UI
        this.initEventListeners();
        this.loadSubjectTags();
    }
    

    /**
     * Initialize event listeners for UI elements
     */
    initEventListeners() {
        // Modal close buttons
        document.querySelectorAll('.close-modal, .close-btn').forEach(button => {
            button.addEventListener('click', () => {
                this.hideModal(this.apiKeysModal);
                this.hideModal(this.paperInfoModal);
            });
        });
        
        // Configure API Keys button
        document.getElementById('configure-api-keys-btn').addEventListener('click', () => {
            this.showModal(this.apiKeysModal);
        });
        
        // Window click to close modals
        window.addEventListener('click', (event) => {
            if (event.target === this.apiKeysModal) {
                this.hideModal(this.apiKeysModal);
            } else if (event.target === this.paperInfoModal) {
                this.hideModal(this.paperInfoModal);
            }
        });
    }
    

    /**
     * Load subject tags from JSON file
     */
    async loadSubjectTags() {
        try {
            const response = await fetch('/data/arxiv_cs_subjects.json');
            const subjects = await response.json();
            
            // Clear existing options
            this.subjectTagsSelect.innerHTML = '';
            
            // Add options to select
            subjects.forEach(subject => {
                const option       = document.createElement('option');
                option.value       = subject.tag;
                option.textContent = `${subject.tag}: ${subject.name}`;
                this.subjectTagsSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading subject tags:', error);
        }
    }
    

    /**
     * Show a modal
     * @param {HTMLElement} modal - The modal to show
     */
    showModal(modal) {
        modal.style.display = 'block';
    }
    

    /**
     * Hide a modal
     * @param {HTMLElement} modal - The modal to hide
     */
    hideModal(modal) {
        modal.style.display = 'none';
    }
    

    /**
     * Show the loading overlay
     * @param {string} message - The loading message to display
     */
    showLoading(message = 'Processing...') {
        this.loadingMessage.textContent   = message;
        this.loadingOverlay.style.display = 'flex';
    }
    

    /**
     * Hide the loading overlay
     */
    hideLoading() {
        this.loadingOverlay.style.display = 'none';
    }

    
    /**
     * Render search results
     * @param {Array} papers - The papers to render
     */
    renderSearchResults(papers) {
        if (!papers || papers.length === 0) {
            this.resultsContainer.innerHTML = '<p class="no-results">No papers found matching your criteria.</p>';
            return;
        }
        
        this.resultsContainer.innerHTML = '';
        papers.forEach(paper => {
            const paperElement           = document.createElement('div');
            paperElement.className       = 'paper-item';
            paperElement.dataset.paperId = paper.arxiv_id;
            
            const categories = paper.categories.map(cat => 
                `<span class="paper-category">${cat}</span>`
            ).join('');
            
            paperElement.innerHTML = `
                <div class="paper-item-header">
                    <h4 class="paper-title">${paper.title}</h4>
                    <span class="paper-date">${paper.published}</span>
                </div>
                <p class="paper-authors">${paper.authors.join(', ')}</p>
                <div class="paper-categories">${categories}</div>
            `;
            
            paperElement.addEventListener('click', () => {
                this.showPaperInfo(paper);
            });
            
            this.resultsContainer.appendChild(paperElement);
        });
    }

    
    /**
     * Show paper information in the modal
     * @param {Object} paper - The paper data
     */
    showPaperInfo(paper) {
        // Set modal content
        document.getElementById('paper-title').textContent      = paper.title;
        document.getElementById('paper-authors').textContent    = paper.authors.join(', ');
        document.getElementById('paper-published').textContent  = paper.published;
        document.getElementById('paper-categories').textContent = paper.categories.join(', ');
        document.getElementById('paper-id').textContent         = paper.arxiv_id;
        document.getElementById('paper-abstract').textContent   = paper.abstract;
        
        // Set data attributes for buttons
        const openArxivBtn     = document.getElementById('open-arxiv-btn');
        const viewPdfBtn       = document.getElementById('view-pdf-btn');
        const downloadPdfBtn   = document.getElementById('download-pdf-btn');
        const chatWithPaperBtn = document.getElementById('chat-with-paper-btn');
        
        openArxivBtn.dataset.url         = paper.entry_id;
        viewPdfBtn.dataset.url           = paper.pdf_url;
        downloadPdfBtn.dataset.paperId   = paper.arxiv_id;
        chatWithPaperBtn.dataset.paperId = paper.arxiv_id;

        // Show the modal
        this.showModal(this.paperInfoModal);
    }
    

    /**
     * Add a message to the chat interface
     * @param {string} message   - The message text
     * @param {boolean} isUser   - Whether the message is from the user
     * @param {Object} citations - Citations from the AI response
     */
    addChatMessage(message, isUser, citations = null) {
        const messageElement     = document.createElement('div');
        messageElement.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        
        // If it's a bot message, parse markdown (simple version)
        if (!isUser) {
            // Simple markdown parsing for links, bold, italic, code
            const formattedMessage = message
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/`(.*?)`/g, '<code>$1</code>')
                .replace(/\n/g, '<br>');
            
            messageElement.innerHTML = formattedMessage;
            
            // Add citations if available
            if (citations && (citations.texts.length > 0 || citations.images.length > 0 || citations.tables.length > 0)) {
                const citationsElement     = document.createElement('div');
                citationsElement.className = 'citations';
                citationsElement.innerHTML = '<strong>Sources:</strong> Text excerpts, tables, and images from the paper were used to generate this response.';
                messageElement.appendChild(citationsElement);
            }
        } else {
            messageElement.textContent = message;
        }
        
        this.chatMessages.appendChild(messageElement);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    

    /**
     * Clear the chat messages
     */
    clearChat() {
        this.chatMessages.innerHTML = '';
        this.addSystemMessage('Chat reset. You can now ask questions about the paper.');
    }
    

    /**
     * Add a system message to the chat
     * @param {string} message - The system message
     */
    addSystemMessage(message) {
        const systemMessage = document.createElement('div');
        systemMessage.className = 'system-message';
        systemMessage.innerHTML = `<p>${message}</p>`;
        this.chatMessages.appendChild(systemMessage);
    }
    

    /**
     * Enable chat functionality
     */
    enableChat() {
        document.getElementById('chat-input').disabled       = false;
        document.getElementById('send-message-btn').disabled = false;
        document.getElementById('reset-chat-btn').disabled   = false;
    }
    

    /**
     * Disable chat functionality
     */
    disableChat() {
        document.getElementById('chat-input').disabled       = true;
        document.getElementById('send-message-btn').disabled = true;
        document.getElementById('reset-chat-btn').disabled   = true;
    }
}