document.addEventListener('DOMContentLoaded', function() {
    const dropArea = document.querySelector('.file-drop-area');
    const fileInput = document.querySelector('.file-input');
    const fileMsg = document.querySelector('.file-name');
    const analyzeBtn = document.getElementById('analyze-btn');
    const analysisStatus = document.querySelector('.analysis-status');
    const progressBar = document.querySelector('.analyzer-progress');
    const statusText = document.querySelector('.analyzer-status-text');
    const resultsSection = document.querySelector('.results-section');
    const tempoValue = document.querySelector('.tempo-value');
    const keyValue = document.querySelector('.key-value');

    console.log('Analyzer JS loaded');
    console.log('Elements found:', {
        dropArea: !!dropArea,
        fileInput: !!fileInput,
        fileMsg: !!fileMsg,
        analyzeBtn: !!analyzeBtn,
        analysisStatus: !!analysisStatus,
        progressBar: !!progressBar,
        statusText: !!statusText,
        resultsSection: !!resultsSection,
        tempoValue: !!tempoValue,
        keyValue: !!keyValue
    });

    let selectedFile = null;

    // Drag and drop handlers
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => {
            dropArea.classList.add('drag-over');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => {
            dropArea.classList.remove('drag-over');
        });
    });

    dropArea.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            handleFiles(files);
        }
    }

    function handleFileSelect(e) {
        const files = e.target.files;
        
        if (files.length > 0) {
            handleFiles(files);
        }
    }

    function handleFiles(files) {
        const file = files[0];
        
        // Check if file is audio
        if (!file.type.startsWith('audio/') && 
            !file.name.endsWith('.mid') && 
            !file.name.endsWith('.midi') && 
            !file.name.endsWith('.xml') && 
            !file.name.endsWith('.mxl') && 
            !file.name.endsWith('.abc')) {
            showError('Please select an audio file');
            return;
        }
        
        selectedFile = file;
        fileMsg.textContent = file.name;
        analyzeBtn.disabled = false;
    }

    function showError(message) {
        statusText.textContent = message;
        statusText.style.color = '#ff4081';
        progressBar.style.width = '0%';
        analysisStatus.style.display = 'block';
        resultsSection.style.display = 'none';
        
        // Reset file selection after a delay
        setTimeout(() => {
            fileInput.value = '';
            selectedFile = null;
            fileMsg.textContent = '';
            analyzeBtn.disabled = true;
        }, 3000);
    }

    analyzeBtn.addEventListener('click', async () => {
        console.log('Analyze button clicked');
        if (!selectedFile) {
            console.error('No file selected');
            return;
        }

        const formData = new FormData();
        formData.append('audio_file', selectedFile);
        console.log('FormData created with file:', selectedFile.name);

        // Show analysis status
        analysisStatus.style.display = 'block';
        progressBar.style.width = '0%';
        statusText.style.color = '#F5F5DC';
        statusText.textContent = 'Analyzing...';
        analyzeBtn.disabled = true;
        resultsSection.style.display = 'none';

        try {
            console.log('Starting analysis...');
            progressBar.style.width = '50%';
            
            // Add a timestamp to the URL to prevent caching
            const timestamp = new Date().getTime();
            const response = await fetch(`/audio/analyze?t=${timestamp}`, {
                method: 'POST',
                body: formData
            });
            
            console.log('Response received:', response.status);
            console.log('Response headers:', [...response.headers.entries()]);
            
            if (!response.ok) {
                throw new Error('Server error: ' + response.status);
            }
            
            // Try to parse as JSON
            const data = await response.json().catch(error => {
                console.error('JSON parse error:', error);
                throw new Error('Failed to parse server response');
            });
            
            console.log('Parsed data:', data);

            if (data && data.success) {
                progressBar.style.width = '100%';
                statusText.textContent = 'Analysis complete!';
                
                // Display results
                resultsSection.style.display = 'flex';
                tempoValue.textContent = `${data.tempo} BPM`;
                keyValue.textContent = data.key;
                
                // Reset form
                fileInput.value = '';
                selectedFile = null;
                fileMsg.textContent = '';
                
                // Hide progress after a delay
                setTimeout(() => {
                    analysisStatus.style.display = 'none';
                }, 3000);
            } else {
                showError(data && data.error ? data.error : 'Analysis failed');
            }
        } catch (error) {
            console.error('Analysis error:', error);
            showError(error.message || 'Error during analysis');
        } finally {
            analyzeBtn.disabled = false;
        }
    });
});