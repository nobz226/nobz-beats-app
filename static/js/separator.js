document.addEventListener('DOMContentLoaded', function() {
    const dropArea = document.querySelector('.file-drop-area');
    const fileInput = document.querySelector('.file-input');
    const fileMsg = document.querySelector('.file-name');
    const separateBtn = document.getElementById('separate-btn');
    const separationStatus = document.querySelector('.separation-status');
    const progressBar = document.querySelector('.separator-progress');
    const statusText = document.querySelector('.separator-status-text');
    const stemsSection = document.querySelector('.stems-section');
    
    // Warning section elements
    const separationWarning = document.getElementById('separation-warning');
    const cancelSeparationBtn = document.getElementById('cancel-separation');
    const confirmSeparationBtn = document.getElementById('confirm-separation');

    let selectedFile = null;
    let currentSessionId = null;
    let isProcessing = false;

    // Function to show the warning
    function showWarning() {
        separationWarning.style.display = 'block';
        
        // Scroll to the warning box with smooth animation
        separationWarning.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    // Function to hide the warning
    function hideWarning() {
        separationWarning.style.display = 'none';
    }

    // Add event listener for the cancel button
    cancelSeparationBtn.addEventListener('click', function() {
        // Hide the warning
        hideWarning();
    });

    // Function to set up audio visualizers for stem cards
    function setupAudioVisualizers() {
        const stemCards = document.querySelectorAll('.stem-card');
        
        stemCards.forEach(card => {
            const audio = card.querySelector('audio');
            const visualizer = card.querySelector('.audio-visualizer');
            
            if (audio && visualizer) {
                // Remove any existing event listeners
                const newAudio = audio.cloneNode(true);
                audio.parentNode.replaceChild(newAudio, audio);
                
                // Add event listeners for play, pause, and ended events
                newAudio.addEventListener('play', function() {
                    visualizer.classList.add('active');
                });
                
                newAudio.addEventListener('pause', function() {
                    visualizer.classList.remove('active');
                });
                
                newAudio.addEventListener('ended', function() {
                    visualizer.classList.remove('active');
                });
            }
        });
    }

    // Call setupAudioVisualizers when the page loads
    setupAudioVisualizers();

    // Prevent defaults for drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, function(e) {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    // Visual feedback for drag and drop
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, function() {
            dropArea.classList.add('drag-over');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, function() {
            dropArea.classList.remove('drag-over');
        });
    });

    // Handle file selection
    dropArea.addEventListener('drop', function(e) {
        handleFiles(e.dataTransfer.files);
    });

    fileInput.addEventListener('change', function(e) {
        handleFiles(e.target.files);
    });

    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            
            // Check if file is audio
            if (!file.type.startsWith('audio/')) {
                showError('Please select an audio file (MP3, WAV, FLAC, or M4A)');
                return;
            }
            
            // Check if file extension is supported
            const fileName = file.name.toLowerCase();
            if (!fileName.endsWith('.mp3') && !fileName.endsWith('.wav') && 
                !fileName.endsWith('.flac') && !fileName.endsWith('.m4a')) {
                showError('Please select an MP3, WAV, FLAC, or M4A file');
                return;
            }

            selectedFile = file;
            fileMsg.textContent = file.name;
            separateBtn.disabled = false;
        }
    }

    function showError(message) {
        statusText.textContent = message;
        statusText.style.color = '#ff4081';
        progressBar.style.width = '0%';
        stemsSection.style.display = 'none';
        
        // Reset file selection
        fileInput.value = '';
        selectedFile = null;
        fileMsg.textContent = '';
        separateBtn.disabled = true;
    }

    function updateStemsSection(data) {
        stemsSection.style.display = 'grid';
        currentSessionId = data.session_id;

        // Update each stem card
        Object.entries(data.stems).forEach(([stem, url]) => {
            const card = document.querySelector(`.stem-card[data-stem="${stem}"]`);
            if (!card) return;

            // Update audio player
            const audio = card.querySelector('audio');
            if (audio) {
                const source = audio.querySelector('source');
                if (source) {
                    source.src = url;
                }
                audio.load();
            }

            // Set up download button with proper filename
            const downloadBtn = card.querySelector('.download-btn');
            if (downloadBtn) {
                const originalName = selectedFile ? selectedFile.name.split('.')[0] : 'audio';
                const stemFilename = `${originalName}_${stem}.mp3`;
                
                // Remove any existing listeners
                const newBtn = downloadBtn.cloneNode(true);
                downloadBtn.parentNode.replaceChild(newBtn, downloadBtn);
                
                newBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    
                    // Create temporary link for download
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = stemFilename;
                    document.body.appendChild(link);
                    
                    // Trigger download
                    link.click();
                    
                    // Clean up
                    document.body.removeChild(link);
                });
            }
        });

        // Set up audio visualizers after updating the stems section
        setupAudioVisualizers();
    }

    // Modify the separate button click handler to show the warning first
    separateBtn.addEventListener('click', function() {
        if (!selectedFile) return;
        
        // Show the warning section instead of starting the process immediately
        showWarning();
    });
    
    // Add event listener for the confirm button to actually start the separation
    confirmSeparationBtn.addEventListener('click', async function() {
        // Hide the warning
        hideWarning();
        
        // Start the separation process
        await startSeparation();
    });
    
    // Function to actually start the separation process
    async function startSeparation() {
        if (!selectedFile) return;

        const formData = new FormData();
        formData.append('audio_file', selectedFile);

        // Reset and show status
        separationStatus.style.display = 'block';
        progressBar.style.width = '0%';
        statusText.style.color = '#F5F5DC';
        statusText.textContent = 'Processing... This may take a few minutes.';
        separateBtn.disabled = true;
        stemsSection.style.display = 'none';
        isProcessing = true;

        try {
            progressBar.style.width = '50%';
            
            const response = await fetch('/audio/separator', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Separation failed');
            }

            const data = await response.json();
            
            if (data.success) {
                progressBar.style.width = '100%';
                statusText.textContent = 'Separation complete! Click to download stems.';
                currentSessionId = data.session_id;
                updateStemsSection(data);
                isProcessing = false;
            } else {
                throw new Error(data.error || 'Separation failed');
            }
        } catch (error) {
            console.error('Separation error:', error);
            progressBar.style.width = '100%';
            statusText.style.color = '#ff4081';
            showError(error.message || 'Error during separation');
            isProcessing = false;
        } finally {
            separateBtn.disabled = false;
        }
    }

    // Clean up when leaving page
    window.addEventListener('beforeunload', function(e) {
        if (currentSessionId && isProcessing) {
            // Show a warning message when leaving during processing
            const message = 'Stem separation is still in progress. If you leave, it will continue but results may be lost.';
            e.returnValue = message;
            return message;
        }
        
        if (currentSessionId) {
            console.log(`Cleaning up session: ${currentSessionId}`);
            // Use sendBeacon for reliable delivery during page unload
            const success = navigator.sendBeacon(`/audio/cleanup_stems/${currentSessionId}`);
            console.log(`Cleanup beacon sent: ${success}`);
        }
    });
});