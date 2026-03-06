/**
 * Main Application Entry Point
 */

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    initDarkMode();
    initFileUpload();
    updateCompareVisibility();
});

/**
 * File Upload Handling
 */
function initFileUpload() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');

    if (!dropZone || !fileInput) return;

    // Click to select file
    dropZone.addEventListener('click', () => fileInput.click());

    // Drag and drop events
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        handleFile(e.dataTransfer.files[0]);
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });
}

/**
 * Handle File Selection
 */
function handleFile(file) {
    if (!file) return;

    // Validate file type
    if (!file.name.toLowerCase().endsWith(AppConfig.ACCEPTED_FILE_TYPE)) {
        showError('Chỉ chấp nhận file PDF');
        return;
    }

    selectedFile = file;
    displaySelectedFile();
}

/**
 * Display Selected File
 */
function displaySelectedFile() {
    document.getElementById('dropZone').classList.add('hidden');
    document.getElementById('selectedFile').classList.remove('hidden');
    document.getElementById('fileName').textContent = selectedFile.name;
}

/**
 * Remove Selected File
 */
function removeFile() {
    selectedFile = null;
    document.getElementById('dropZone').classList.remove('hidden');
    document.getElementById('selectedFile').classList.add('hidden');
    document.getElementById('fileInput').value = '';
}

// Export functions to global scope for onclick handlers in HTML
// Note: The actual implementations are in api.js (loaded before app.js)
// handleExtractClick and handleRemoveFile are also defined in api.js
// These are fallback definitions in case api.js hasn't loaded

