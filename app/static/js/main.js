// DOM Elements
const apiKeyInput = document.getElementById('api-key');
const modelSelect = document.getElementById('model-select');
const temperatureSlider = document.getElementById('temperature');
const tempValue = document.getElementById('temp-value');
const saveConfigBtn = document.getElementById('save-config');
const uploadDropzone = document.getElementById('upload-dropzone');
const fileInput = document.getElementById('file-input');
const fileList = document.getElementById('file-list');
const analyzeBtn = document.getElementById('analyze-btn');
const progressStatus = document.getElementById('progress-status');
const queryInput = document.getElementById('query-input');
const generateBtn = document.getElementById('generate-btn');
const answerContent = document.getElementById('answer-content');
const citationsContent = document.getElementById('citations-content');
const tabButtons = document.querySelectorAll('.tab-btn');

// Application State
let appState = {
    configured: false,
    uploadedFiles: [],
    processingStatus: 'idle', // idle, processing, complete, error
    pollingInterval: null,
};

// Initialize the application
function init() {
    // Setup event listeners
    setupConfigListeners();
    setupFileUploadListeners();
    setupQueryListeners();
    setupTabsListeners();
}

// ========= Configuration Section =========
function setupConfigListeners() {
    // Temperature slider
    temperatureSlider.addEventListener('input', () => {
        tempValue.textContent = temperatureSlider.value;
    });

    // Save configuration
    saveConfigBtn.addEventListener('click', saveConfiguration);
}

async function saveConfiguration() {
    const apiKey = apiKeyInput.value.trim();
    const model = modelSelect.value;
    const temperature = parseFloat(temperatureSlider.value);

    if (!apiKey) {
        showToast('Please enter a valid API key', 'error');
        return;
    }

    try {
        saveConfigBtn.disabled = true;
        saveConfigBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Configuring...';
        
        const formData = new FormData();
        formData.append('api_key', apiKey);
        formData.append('model', model);
        formData.append('temperature', temperature);

        const response = await fetch('/api/configure', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showToast(`Model ${model} successfully initialized!`, 'success');
            appState.configured = true;
            updateButtonStates();
        } else {
            showToast(data.detail || 'Failed to save configuration', 'error');
        }
    } catch (error) {
        showToast('Error saving configuration: ' + error.message, 'error');
    } finally {
        saveConfigBtn.disabled = false;
        saveConfigBtn.innerHTML = 'Save Configuration';
    }
}

// ========= File Upload Section =========
function setupFileUploadListeners() {
    // Dropzone click to browse
    uploadDropzone.addEventListener('click', () => {
        fileInput.click();
    });

    // File input change
    fileInput.addEventListener('change', handleFileSelection);

    // Drag and drop events
    uploadDropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadDropzone.classList.add('drag-over');
    });

    uploadDropzone.addEventListener('dragleave', () => {
        uploadDropzone.classList.remove('drag-over');
    });

    uploadDropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadDropzone.classList.remove('drag-over');
        
        if (e.dataTransfer.files.length > 0) {
            handleFiles(e.dataTransfer.files);
        }
    });

    // Analyze button
    analyzeBtn.addEventListener('click', analyzeDocuments);
}

function handleFileSelection(e) {
    if (e.target.files.length > 0) {
        handleFiles(e.target.files);
    }
}

function handleFiles(files) {
    // Filter for PDFs
    const pdfFiles = Array.from(files).filter(file => file.type === 'application/pdf');
    
    if (pdfFiles.length === 0) {
        showToast('Please select PDF files only', 'error');
        return;
    }

    // Upload files
    uploadFiles(pdfFiles);
}

async function uploadFiles(files) {
    try {
        // Show upload starting toast
        showToast(`Uploading ${files.length} file(s)...`, 'info');
        
        // Update progress bar to show upload starting
        updateProgressBar(5, 'Uploading files...');
        
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });

        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showToast(`Successfully uploaded ${files.length} file(s)`, 'success');
            updateFileList(data.files);
            analyzeBtn.disabled = false;
            
            // Update progress bar to show upload complete
            updateProgressBar(10, 'Files uploaded. Ready for analysis.');
        } else {
            showToast(data.detail || 'Failed to upload files', 'error');
            updateProgressBar(0, 'Upload failed');
        }
    } catch (error) {
        showToast('Error uploading files: ' + error.message, 'error');
        updateProgressBar(0, 'Upload failed');
    }
}

function updateFileList(files) {
    fileList.innerHTML = '';
    appState.uploadedFiles = files;

    files.forEach(fileName => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <span><i class="fas fa-file-pdf"></i>${fileName}</span>
            <i class="fas fa-times remove-btn" data-file="${fileName}"></i>
        `;
        fileList.appendChild(fileItem);
    });

    // Add remove button event listeners
    document.querySelectorAll('.remove-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            removeFile(btn.getAttribute('data-file'));
        });
    });

    updateButtonStates();
}

function removeFile(fileName) {
    // In a real application, you might want to call an API to remove the file
    appState.uploadedFiles = appState.uploadedFiles.filter(file => file !== fileName);
    updateFileList(appState.uploadedFiles);
    
    if (appState.uploadedFiles.length === 0) {
        analyzeBtn.disabled = true;
        generateBtn.disabled = true;
        appState.processingStatus = 'idle';
        progressStatus.textContent = 'Ready';
    }
}

async function analyzeDocuments() {
    try {
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
        
        // Reset progress bar
        updateProgressBar(0, 'Starting analysis...');
        
        const response = await fetch('/api/analyze', {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Document analysis started', 'info');
            appState.processingStatus = 'processing';
            
            // Start polling for status updates
            startStatusPolling();
        } else {
            showToast(data.detail || 'Failed to analyze documents', 'error');
            updateProgressBar(0, 'Analysis failed');
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = 'Analyze Documents';
        }
    } catch (error) {
        showToast('Error analyzing documents: ' + error.message, 'error');
        updateProgressBar(0, 'Analysis failed');
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = 'Analyze Documents';
    }
}

function updateProgressBar(percent, statusText) {
    const progressFill = document.querySelector('.progress-fill');
    const progressStatus = document.getElementById('progress-status');
    
    progressFill.style.width = `${percent}%`;
    progressStatus.textContent = statusText;
}

function startStatusPolling() {
    // Clear any existing polling
    if (appState.pollingInterval) {
        clearInterval(appState.pollingInterval);
    }

    let progressPercent = 10; // Start at 10%
    const progressStages = [
        { percent: 10, text: 'Starting analysis...' },
        { percent: 25, text: 'Partitioning documents...' },
        { percent: 40, text: 'Extracting text, tables, and images...' },
        { percent: 60, text: 'Summarizing content...' },
        { percent: 80, text: 'Creating embeddings...' }
    ];
    let currentStage = 0;
    
    // Initial progress update
    updateProgressBar(progressStages[0].percent, progressStages[0].text);

    // Start polling
    appState.pollingInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();

            appState.processingStatus = data.status;
            
            if (data.status === 'processing') {
                // Advance to next stage of progress bar for visual feedback
                if (currentStage < progressStages.length - 1) {
                    currentStage++;
                    updateProgressBar(
                        progressStages[currentStage].percent, 
                        progressStages[currentStage].text
                    );
                }
            } else if (data.status === 'complete') {
                updateProgressBar(100, 'Analysis complete!');
                generateBtn.disabled = false;
                analyzeBtn.disabled = false;
                analyzeBtn.innerHTML = 'Analyze Documents';
                showToast('Document analysis complete!', 'success');
                clearInterval(appState.pollingInterval);
            } else if (data.status === 'error') {
                updateProgressBar(0, 'Error during processing');
                analyzeBtn.disabled = false;
                analyzeBtn.innerHTML = 'Analyze Documents';
                showToast('Error during document processing', 'error');
                clearInterval(appState.pollingInterval);
            }
        } catch (error) {
            console.error('Error polling status:', error);
        }
    }, 2000); // Poll every 2 seconds
}

// ========= Query Section =========
function setupQueryListeners() {
    generateBtn.addEventListener('click', generateAnswer);
}

async function generateAnswer() {
    const query = queryInput.value.trim();
    
    if (!query) {
        showToast('Please enter a query', 'error');
        return;
    }

    try {
        // Disable button and show loading state
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        
        answerContent.innerHTML = '<p><i class="fas fa-spinner fa-spin"></i> Generating answer...</p>';
        showTab('answer');

        const formData = new FormData();
        formData.append('query', query);

        const response = await fetch('/api/query', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            displayAnswer(data);
            displayCitations(data);
            showToast('Answer generated successfully', 'success');
        } else {
            showToast(data.detail || 'Failed to generate answer', 'error');
            answerContent.innerHTML = '<p>Error generating answer. Please try again.</p>';
        }
    } catch (error) {
        showToast('Error generating answer: ' + error.message, 'error');
        answerContent.innerHTML = '<p>Error generating answer. Please try again.</p>';
    } finally {
        // Reset button state
        generateBtn.disabled = false;
        generateBtn.innerHTML = 'Generate Answer';
    }
}

function displayAnswer(data) {
    // Use marked library to render markdown
    answerContent.innerHTML = marked.parse(data.answer);
}

function displayCitations(data) {
    citationsContent.innerHTML = '';
    
    if (!data.citations || data.citations.length === 0) {
        citationsContent.innerHTML = '<p>No citations available for this answer.</p>';
        return;
    }

    // Create citations elements
    data.citations.forEach(citation => {
        const citationType = citation.type;
        const citationId = citation.id;
        
        // Get the content from the context
        let content = '';
        let title = '';
        
        if (citationType === 'text') {
            const textContent = data.context.texts.find(t => t.id === citationId);
            if (textContent) {
                content = textContent.content;
                title = `Text Citation #${citationId}`;
            }
        } else if (citationType === 'table') {
            const tableContent = data.context.tables.find(t => t.id === citationId);
            if (tableContent) {
                content = tableContent.content;
                title = `Table Citation #${citationId}`;
            }
        } else if (citationType === 'image') {
            const imageContent = data.context.images.find(i => i.id === citationId);
            if (imageContent) {
                content = `<img src="data:image/jpeg;base64,${imageContent.content}" alt="Citation Image" style="max-width: 100%;">`;
                title = `Image Citation #${citationId}`;
            }
        }
        
        if (content) {
            const citationElement = document.createElement('div');
            citationElement.className = 'citation';
            
            citationElement.innerHTML = `
                <div class="citation-header">
                    <span>${title}</span>
                </div>
                <div class="citation-content">
                    ${citationType === 'table' ? content : citationType === 'text' ? `<p>${content}</p>` : content}
                </div>
            `;
            
            citationsContent.appendChild(citationElement);
        }
    });
}

// ========= Tabs Section =========
function setupTabsListeners() {
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            showTab(tabName);
        });
    });
}

function showTab(tabName) {
    // Update tab buttons
    tabButtons.forEach(button => {
        if (button.getAttribute('data-tab') === tabName) {
            button.classList.add('active');
        } else {
            button.classList.remove('active');
        }
    });
    
    // Update tab panes
    document.querySelectorAll('.tab-pane').forEach(pane => {
        if (pane.id === `${tabName}-tab`) {
            pane.classList.add('active');
        } else {
            pane.classList.remove('active');
        }
    });
}

// ========= Utility Functions =========
function updateButtonStates() {
    analyzeBtn.disabled = !appState.configured || appState.uploadedFiles.length === 0;
    generateBtn.disabled = appState.processingStatus !== 'complete';
}

// Toast notification system
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    const toast = document.createElement('div');
    
    // Configure toast type & icon
    let iconClass = '';
    toast.className = `toast toast-${type}`;
    
    switch (type) {
        case 'success':
            iconClass = 'fa-check-circle';
            break;
        case 'error':
            iconClass = 'fa-exclamation-circle';
            break;
        case 'info':
        default:
            iconClass = 'fa-info-circle';
            break;
    }
    
    // Create toast content
    toast.innerHTML = `
        <i class="fas ${iconClass} toast-icon"></i>
        <div class="toast-message">${message}</div>
        <button class="toast-close"><i class="fas fa-times"></i></button>
    `;
    
    // Add to container
    toastContainer.appendChild(toast);
    
    // Add close button functionality
    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.remove();
    });
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 3000);
}

function showError(message) {
    showToast(message, 'error');
}

function showSuccess(message) {
    showToast(message, 'success');
}

// Initialize the application
document.addEventListener('DOMContentLoaded', init);
