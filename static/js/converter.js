// Wait for the DOM to be fully loaded
window.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    var fileInput = document.getElementById('audio-file');
    var formatButtons = document.querySelectorAll('.format-btn');
    var convertButton = document.getElementById('convert-btn');
    var fileNameDisplay = document.querySelector('.file-name');
    var dropArea = document.querySelector('.file-drop-area');
    var progressBar = document.querySelector('.converter-progress');
    var statusText = document.querySelector('.converter-status-text');
    var conversionStatus = document.querySelector('.conversion-status');
    var downloadSection = document.querySelector('.download-section');
    var downloadBtn = document.querySelector('.download-btn');
    
    console.log('Converter JS loaded');
    console.log('Elements found:', {
        fileInput: !!fileInput,
        formatButtons: !!formatButtons,
        convertButton: !!convertButton,
        fileNameDisplay: !!fileNameDisplay,
        dropArea: !!dropArea,
        progressBar: !!progressBar,
        statusText: !!statusText,
        conversionStatus: !!conversionStatus,
        downloadSection: !!downloadSection,
        downloadBtn: !!downloadBtn
    });
    
    // Variables to track state
    var hasFile = false;
    var selectedFormat = '';
    var selectedFile = null;
    
    // Function to check if convert button should be enabled
    function updateButtonState() {
        if (hasFile && selectedFormat) {
            convertButton.removeAttribute('disabled');
        } else {
            convertButton.setAttribute('disabled', 'disabled');
        }
    }
    
    // Handle file selection
    fileInput.onchange = function() {
        if (this.files && this.files.length > 0) {
            var file = this.files[0];
            
            // Check if file is audio
            if (!file.type.startsWith('audio/')) {
                showError('Please select an audio file (MP3, WAV, or FLAC)');
                return;
            }
            
            // Check if file extension is supported
            var fileName = file.name.toLowerCase();
            if (!fileName.endsWith('.mp3') && !fileName.endsWith('.wav') && !fileName.endsWith('.flac')) {
                showError('Please select an MP3, WAV, or FLAC file');
                return;
            }
            
            hasFile = true;
            selectedFile = file;
            fileNameDisplay.textContent = file.name;
            updateButtonState();
        }
    };
    
    // Handle format selection
    formatButtons.forEach(function(button) {
        button.onclick = function() {
            // Remove selected class from all buttons
            formatButtons.forEach(function(btn) {
                btn.classList.remove('selected');
            });
            
            // Add selected class to clicked button
            this.classList.add('selected');
            
            // Update selected format
            selectedFormat = this.getAttribute('data-format');
            
            // Update button state
            updateButtonState();
        };
    });
    
    // Handle drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(function(eventName) {
        dropArea.addEventListener(eventName, function(e) {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });
    
    ['dragenter', 'dragover'].forEach(function(eventName) {
        dropArea.addEventListener(eventName, function() {
            this.classList.add('drag-over');
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(function(eventName) {
        dropArea.addEventListener(eventName, function() {
            this.classList.remove('drag-over');
        }, false);
    });
    
    dropArea.addEventListener('drop', function(e) {
        if (e.dataTransfer.files.length > 0) {
            var file = e.dataTransfer.files[0];
            
            // Check if file is audio
            if (!file.type.startsWith('audio/')) {
                showError('Please select an audio file (MP3, WAV, or FLAC)');
                return;
            }
            
            // Check if file extension is supported
            var fileName = file.name.toLowerCase();
            if (!fileName.endsWith('.mp3') && !fileName.endsWith('.wav') && !fileName.endsWith('.flac')) {
                showError('Please select an MP3, WAV, or FLAC file');
                return;
            }
            
            fileInput.files = e.dataTransfer.files;
            hasFile = true;
            selectedFile = file;
            fileNameDisplay.textContent = file.name;
            updateButtonState();
        }
    }, false);
    
    // Show error message
    function showError(message) {
        conversionStatus.style.display = 'block';
        downloadSection.style.display = 'none';
        statusText.textContent = message;
        statusText.style.color = '#ff4081';
        progressBar.style.width = '0%';
        
        // Reset file selection after a delay
        setTimeout(function() {
            fileInput.value = '';
            hasFile = false;
            selectedFile = null;
            fileNameDisplay.textContent = '';
            updateButtonState();
        }, 3000);
    }
    
    // Handle convert button click
    convertButton.onclick = function(e) {
        e.preventDefault();
        
        if (!hasFile || !selectedFormat) {
            return;
        }
        
        // Create form data
        var formData = new FormData();
        formData.append('audio_file', selectedFile);
        formData.append('target_format', selectedFormat);
        
        // Show conversion status
        conversionStatus.style.display = 'block';
        downloadSection.style.display = 'none';
        progressBar.style.width = '0%';
        statusText.textContent = 'Converting...';
        statusText.style.color = '#F5F5DC'; // Reset color
        convertButton.setAttribute('disabled', 'disabled');
        
        // Animate progress bar to show activity
        progressBar.style.width = '50%';
        
        console.log('Sending conversion request...');
        
        // Add a timestamp to the URL to prevent caching
        var timestamp = new Date().getTime();
        
        // Send request
        fetch(`/audio/converter?t=${timestamp}`, {
            method: 'POST',
            body: formData
        })
        .then(function(response) {
            console.log('Response received:', response.status);
            console.log('Response headers:', [...response.headers.entries()]);
            
            if (!response.ok) {
                throw new Error('Server error: ' + response.status);
            }
            
            // Try to parse as JSON
            return response.json().catch(function(err) {
                console.error('JSON parse error:', err);
                throw new Error('Failed to parse server response');
            });
        })
        .then(function(data) {
            console.log('Data received:', data);
            if (data && data.success) {
                // Show completion
                progressBar.style.width = '100%';
                statusText.textContent = 'Conversion complete!';
                
                // Update download button
                downloadBtn.href = data.download_url;
                downloadBtn.download = data.filename || 'converted_file';
                
                // Show download section
                downloadSection.style.display = 'block';
                
                // Add click handler for download button
                downloadBtn.onclick = function() {
                    // Reset form after download is initiated
                    setTimeout(function() {
                        fileInput.value = '';
                        hasFile = false;
                        selectedFile = null;
                        fileNameDisplay.textContent = '';
                        formatButtons.forEach(function(btn) {
                            btn.classList.remove('selected');
                        });
                        selectedFormat = '';
                        convertButton.setAttribute('disabled', 'disabled');
                        
                        // Hide sections
                        downloadSection.style.display = 'none';
                        conversionStatus.style.display = 'none';
                    }, 1000);
                };
            } else {
                showError(data && data.error ? data.error : 'Conversion failed');
            }
        })
        .catch(function(error) {
            console.error('Conversion error:', error);
            showError(error.message || 'Error during conversion');
            // Re-enable convert button to try again
            convertButton.removeAttribute('disabled');
        });
    };
});