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
        showError('Please enter a valid API key');
        return;
    }

    try {
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
            showSuccess('Configuration saved successfully');
            appState.configured = true;
            updateButtonStates();
        } else {
            showError(data.detail || 'Failed to save configuration');
        }
    } catch (error) {
        showError('Error saving configuration: ' + error.message);
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
        showError('Please select PDF files only');
        return;
    }

    // Upload files
    uploadFiles(pdfFiles);
}

async function uploadFiles(files) {
    try {
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
            showSuccess(`Successfully uploaded ${files.length} files`);
            updateFileList(data.files);
            analyzeBtn.disabled = false;
        } else {
            showError(data.detail || 'Failed to upload files');
        }
    } catch (error) {
        showError('Error uploading files: ' + error.message);
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
        const response = await fetch('/api/analyze', {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess('Document analysis started');
            appState.processingStatus = 'processing';
            progressStatus.textContent = 'Processing...';
            
            // Start polling for status updates
            startStatusPolling();
        } else {
            showError(data.detail || 'Failed to analyze documents');
        }
    } catch (error) {
        showError('Error analyzing documents: ' + error.message);
    }
}

function startStatusPolling() {
    // Clear any existing polling
    if (appState.pollingInterval) {
        clearInterval(appState.pollingInterval);
    }

    // Start polling
    appState.pollingInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();

            appState.processingStatus = data.status;
            
            if (data.status === 'processing') {
                progressStatus.textContent = 'Processing documents...';
            } else if (data.status === 'complete') {
                progressStatus.textContent = 'Analysis complete';
                generateBtn.disabled = false;
                clearInterval(appState.pollingInterval);
            } else if (data.status === 'error') {
                progressStatus.textContent = 'Error during processing';
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
        showError('Please enter a query');
        return;
    }

    try {
        answerContent.innerHTML = '<p>Generating answer...</p>';
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
        } else {
            showError(data.detail || 'Failed to generate answer');
            answerContent.innerHTML = '<p>Error generating answer. Please try again.</p>';
        }
    } catch (error) {
        showError('Error generating answer: ' + error.message);
        answerContent.innerHTML = '<p>Error generating answer. Please try again.</p>';
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

function showError(message) {
    alert(message); // In a real app, use a better notification system
}

function showSuccess(message) {
    console.log(message); // In a real app, use a better notification system
}

// Initialize the application
document.addEventListener('DOMContentLoaded', init);
