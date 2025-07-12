/**
 * Main application entry point for arXivCSRAG
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize UI and Chat managers
    const uiManager = new UIManager();
    const chatManager = new ChatManager(uiManager);
    
    // API Keys configuration
    const saveApiKeysBtn = document.getElementById('save-api-keys-btn');
    saveApiKeysBtn.addEventListener('click', async () => {
        const geminiApiKey = document.getElementById('gemini-api-key').value.trim();
        const huggingfaceToken = document.getElementById('huggingface-token').value.trim();
        
        if (!geminiApiKey || !huggingfaceToken) {
            alert('Please enter both API keys.');
            return;
        }
        
        uiManager.showLoading('Configuring API keys...');
        
        try {
            const response = await ApiService.configureApiKeys(geminiApiKey, huggingfaceToken);
            
            if (response.status === 'success') {
                uiManager.hideModal(uiManager.apiKeysModal);
                alert('API keys configured successfully!');
            } else {
                alert('Failed to configure API keys. Please try again.');
            }
        } catch (error) {
            console.error('Error saving API keys:', error);
            alert('An unexpected error occurred. Please try again.');
        } finally {
            uiManager.hideLoading();
        }
    });
    
    // Paper search functionality
    const searchButton = document.getElementById('search-button');
    searchButton.addEventListener('click', async () => {
        // Get search parameters
        const subjectTags = Array.from(document.getElementById('subject-tags-select').selectedOptions).map(option => option.value);
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;
        const maxResults = parseInt(document.getElementById('max-results').value) || 10;
        const query = document.getElementById('search-query').value.trim();
        
        if (!query) {
            alert('Please enter a search query.');
            return;
        }
        
        uiManager.showLoading('Searching for papers...');
        
        try {
            const response = await ApiService.fetchPapers({
                subject_tags: subjectTags.length > 0 ? subjectTags : null,
                start_date: startDate || null,
                end_date: endDate || null,
                max_results: maxResults,
                query: query
            });
            
            if (response.status === 'success') {
                uiManager.renderSearchResults(response.papers);
            } else {
                alert('Failed to fetch papers. Please try again.');
            }
        } catch (error) {
            console.error('Error searching papers:', error);
            alert('An unexpected error occurred. Please try again.');
        } finally {
            uiManager.hideLoading();
        }
    });
    
    // Upload paper functionality
    const uploadButton = document.getElementById('upload-button');
    uploadButton.addEventListener('click', async () => {
        const fileInput = document.getElementById('pdf-upload');
        const file = fileInput.files[0];
        
        if (!file) {
            alert('Please select a PDF file to upload.');
            return;
        }
        
        if (file.type !== 'application/pdf') {
            alert('Please select a valid PDF file.');
            return;
        }
        
        uiManager.showLoading('Uploading paper...');
        
        try {
            const response = await ApiService.uploadPaper(file);
            
            if (response.status === 'success') {
                await chatManager.processPaper(response.file_path);
            } else {
                alert('Failed to upload paper. Please try again.');
                uiManager.hideLoading();
            }
        } catch (error) {
            console.error('Error uploading paper:', error);
            alert('An unexpected error occurred. Please try again.');
            uiManager.hideLoading();
        }
    });
    
    // Paper info modal buttons
    document.getElementById('open-arxiv-btn').addEventListener('click', function() {
        const url = this.dataset.url;
        if (url) {
            window.open(url, '_blank');
        }
    });
    
    document.getElementById('view-pdf-btn').addEventListener('click', function() {
        const url = this.dataset.url;
        if (url) {
            window.open(url, '_blank');
        }
    });
    
    document.getElementById('download-pdf-btn').addEventListener('click', function() {
        const paperId = this.dataset.paperId;
        if (paperId) {
            // Create a temporary link to download the file
            uiManager.showLoading('Preparing download...');
            
            ApiService.downloadPaper(paperId)
                .then(response => {
                    if (response.status === 'success') {
                        // Create a link to download the file directly
                        const a = document.createElement('a');
                        a.href = response.file_path;
                        a.download = `${paperId.replace('/', '_')}.pdf`;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                    } else {
                        alert('Failed to download paper. Please try again.');
                    }
                })
                .catch(error => {
                    console.error('Error downloading paper:', error);
                    alert('An unexpected error occurred. Please try again.');
                })
                .finally(() => {
                    uiManager.hideLoading();
                });
        }
    });
    
    document.getElementById('chat-with-paper-btn').addEventListener('click', function() {
        const paperId = this.dataset.paperId;
        if (paperId) {
            chatManager.downloadAndProcessPaper(paperId);
        }
    });
    
    // Show API keys modal on first load
    setTimeout(() => {
        uiManager.showModal(uiManager.apiKeysModal);
    }, 500);
});
