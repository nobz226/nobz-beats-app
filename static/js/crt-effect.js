// CRT Effect Controller

document.addEventListener('DOMContentLoaded', function() {
    // Create CRT elements
    createCRTElements();
    
    // Initialize CRT effect
    initCRTEffect();
    
    // Load saved settings
    loadCRTSettings();
});

function createCRTElements() {
    // Create CRT overlay elements
    const body = document.body;
    
    // Add CRT effect class to body
    body.classList.add('crt-effect');
    
    // Create curvature element
    const curvature = document.createElement('div');
    curvature.className = 'crt-curvature';
    body.appendChild(curvature);
    
    // Create flicker element
    const flicker = document.createElement('div');
    flicker.className = 'crt-flicker';
    body.appendChild(flicker);
    
    // Find the hero section or main content to append the control
    const mainContent = document.querySelector('main');
    if (!mainContent) return;
    
    // Create control panel with higher default value
    const controlPanel = document.createElement('div');
    controlPanel.className = 'crt-control';
    controlPanel.innerHTML = `
        <label for="crt-intensity">CRT:</label>
        <input type="range" id="crt-intensity" min="0" max="1" step="0.01" value="0.7">
    `;
    
    // Insert at the beginning of main content
    mainContent.insertBefore(controlPanel, mainContent.firstChild);
}

function initCRTEffect() {
    const intensitySlider = document.getElementById('crt-intensity');
    if (!intensitySlider) return;
    
    // Update CRT intensity when slider changes
    intensitySlider.addEventListener('input', function() {
        updateCRTIntensity(this.value);
        saveCRTSettings(this.value);
    });
}

function updateCRTIntensity(value) {
    // Update CRT intensity
    document.documentElement.style.setProperty('--crt-intensity', value);
    
    // Dynamically adjust brightness based on CRT intensity
    // As CRT intensity increases, increase brightness to compensate
    const brightnessValue = 1.1 + (parseFloat(value) * 0.15);
    document.documentElement.style.setProperty('--crt-brightness', brightnessValue.toFixed(2));
}

function saveCRTSettings(intensity) {
    localStorage.setItem('crt-intensity', intensity);
}

function loadCRTSettings() {
    const savedIntensity = localStorage.getItem('crt-intensity');
    
    if (savedIntensity !== null) {
        const intensitySlider = document.getElementById('crt-intensity');
        if (intensitySlider) {
            intensitySlider.value = savedIntensity;
            updateCRTIntensity(savedIntensity);
        }
    } else {
        // If no saved setting, initialize with the default higher intensity
        updateCRTIntensity(0.7);
    }
} 