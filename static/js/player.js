document.addEventListener("DOMContentLoaded", () => {
  // Player elements
  const player = {
    audio: document.getElementById("global-audio"),
    playBtn: document.querySelector(".global-play-btn"),
    stopBtn: document.querySelector(".global-stop-btn"),
    restartBtn: document.querySelector(".global-restart-btn"),
    repeatBtn: document.querySelector(".global-repeat-btn"),
    prevBtn: document.querySelector(".global-prev-btn"),
    nextBtn: document.querySelector(".global-next-btn"),
    toggleBtn: document.querySelector(".global-toggle-btn"),
    progressBar: document.querySelector(".progress-bar"),
    progressContainer: document.querySelector(".progress-container"),
    trackName: document.querySelector(".track-name"),
    currentTime: document.querySelector(".current-time"),
    totalTime: document.querySelector(".total-time"),
    artworkImage: document.querySelector(".track-artwork"),
    artworkPlaceholder: document.querySelector(".artwork-placeholder"),
    playerContainer: document.getElementById("global-audio-player"),
  };

  // Configure audio element
  player.audio.preload = "auto";

  // State
  let currentTrackIndex = -1;
  let isRepeatEnabled = false;
  let isPlayerHidden = true; // Default state is hidden
  let trackList = [];
  let wasPlaying = false;

  // Function to check if current device is mobile
  function isMobileDevice() {
    return window.innerWidth <= 768; // Consider devices up to 768px wide as mobile
  }

  // Initialize repeat button state
  player.repeatBtn.style.opacity = "0.5";

  // Initialize toggle button icon
  updateToggleButtonIcon();
  
  // Add scroll event listener to ensure player visibility on mobile
  if (isMobileDevice()) {
    window.addEventListener('scroll', () => {
      ensurePlayerVisibility();
    });
  }
  
  // Function to ensure player and toggle button visibility on mobile
  function ensurePlayerVisibility() {
    if (!isMobileDevice()) return;
    
    // Make sure toggle button is always visible
    if (player.toggleBtn) {
      player.toggleBtn.style.display = 'flex';
      player.toggleBtn.style.visibility = 'visible';
      player.toggleBtn.style.opacity = '1';
      player.toggleBtn.style.position = 'fixed';
      player.toggleBtn.style.zIndex = '951';
      
      // Position differently based on player state
      if (isPlayerHidden) {
        player.toggleBtn.style.bottom = '0';
        player.toggleBtn.style.left = '50%';
        player.toggleBtn.style.transform = 'translateX(-50%)';
      } else {
        // Use different position based on screen size
        if (window.innerWidth <= 480) {
          player.toggleBtn.style.bottom = '90px';
          player.toggleBtn.style.right = '15px';
        } else {
          player.toggleBtn.style.bottom = '70px';
          player.toggleBtn.style.right = '15px';
        }
        player.toggleBtn.style.transform = 'translateX(0)';
      }
    }
    
    // Make sure player is always visible when active
    if (player.playerContainer && player.playerContainer.classList.contains('active')) {
      player.playerContainer.style.position = 'fixed';
      player.playerContainer.style.bottom = '0';
      player.playerContainer.style.zIndex = '950';
      
      if (isPlayerHidden) {
        // Different transform based on screen size
        if (window.innerWidth <= 480) {
          player.playerContainer.style.transform = 'translateY(calc(100% - 25px))';
        } else {
          player.playerContainer.style.transform = 'translateY(calc(100% - 35px))';
        }
      } else {
        player.playerContainer.style.transform = 'translateY(0)';
      }
    }
  }

  // Function to update toggle button icon based on player state
  function updateToggleButtonIcon() {
    if (player.toggleBtn) {
      if (isPlayerHidden) {
        player.toggleBtn.innerHTML = '<i class="fas fa-chevron-up"></i>';
        player.toggleBtn.title = "Show Player";
      } else {
        player.toggleBtn.innerHTML = '<i class="fas fa-chevron-down"></i>';
        player.toggleBtn.title = "Hide Player";
      }
      
      // Ensure visibility
      player.toggleBtn.style.display = 'flex';
      player.toggleBtn.style.opacity = '1';
    }
    
    // Ensure player visibility on mobile
    if (isMobileDevice()) {
      ensurePlayerVisibility();
    }
  }

  // Toggle player visibility
  player.toggleBtn.addEventListener("click", (e) => {
    e.preventDefault(); // Prevent any default behavior
    e.stopPropagation(); // Prevent event bubbling
    
    // Always allow the user to show/hide the player even if no track is loaded
    if (isPlayerHidden) {
      // Unhide player
      player.playerContainer.classList.add("active");
      player.playerContainer.classList.remove("hidden");
      isPlayerHidden = false;
    } else {
      // Hide player
      player.playerContainer.classList.add("hidden");
      isPlayerHidden = true;
    }
    
    updateToggleButtonIcon();
    saveState();
    
    // Ensure visibility on mobile
    if (isMobileDevice()) {
      ensurePlayerVisibility();
    }
  });

  // Function to check if artwork should spin (has 'vinyl' in the name)
  const shouldArtworkSpin = (artworkElement) => {
    const artworkSrc =
      artworkElement.src || artworkElement.querySelector("img")?.src || "";
    return artworkSrc.toLowerCase().includes("vinyl");
  };

  // Function to manage artwork spinning
  const updateArtworkSpinning = (isPlaying) => {
    // Check if we have an artwork element
    const artworkElement = document.querySelector('.track-artwork');
    if (!artworkElement) return;
    
    // Only apply spinning animation on desktop
    if (!isMobileDevice()) {
      if (isPlaying) {
        artworkElement.classList.add('spinning');
        artworkElement.classList.remove('paused');
      } else {
        artworkElement.classList.add('paused');
        artworkElement.classList.remove('spinning');
      }
    } else {
      // On mobile, remove all spinning/paused classes
      artworkElement.classList.remove('spinning', 'paused');
    }
  };

  // Function to stop all artwork spinning
  const stopAllArtworkSpinning = () => {
    // Stop primary artworks
    const allArtworks = document.querySelectorAll(".track-artwork");
    allArtworks.forEach((artwork) => {
      artwork.classList.remove("spinning", "paused");
    });
    
    // Stop secondary artworks
    const secondaryArtworks = document.querySelectorAll(".track-artwork-secondary");
    secondaryArtworks.forEach((artwork) => {
      artwork.classList.remove("spinning", "paused");
    });
    
    // Stop global player artwork
    const globalArtwork = document.querySelector(".global-player-info .track-artwork");
    if (globalArtwork) {
      globalArtwork.classList.remove("spinning", "paused");
    }
  };

  // Store track list
  const storeTrackList = () => {
    const trackButtons = document.querySelectorAll(".play-track-btn");
    if (trackButtons.length > 0) {
      trackList = Array.from(trackButtons).map((button) => ({
        url: button.dataset.trackUrl,
        name: button.dataset.trackName,
        artwork: button.dataset.trackArtwork,
        artworkSecondary: button.dataset.trackArtworkSecondary,
      }));
      sessionStorage.setItem("trackList", JSON.stringify(trackList));
    }
  };

  // Save current state
  const saveState = () => {
    if (player.audio.src) {
      const state = {
        src: player.audio.src,
        trackName: player.trackName.textContent,
        currentTime: player.audio.currentTime,
        isPlaying: !player.audio.paused,
        isRepeatEnabled: isRepeatEnabled,
        isPlayerHidden: isPlayerHidden,
        currentTrackIndex: currentTrackIndex,
        artworkSrc: player.artworkImage.style.display !== "none" ? player.artworkImage.src : "",
      };
      sessionStorage.setItem("audioState", JSON.stringify(state));
    } else {
      sessionStorage.removeItem("audioState");
    }
  };

  // Handle visibility change
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      wasPlaying = !player.audio.paused;
      saveState();
    }
  });

  // Restore state
  const restoreState = () => {
    // Restore track list first
    const savedTrackList = sessionStorage.getItem("trackList");
    if (savedTrackList) {
      trackList = JSON.parse(savedTrackList);
    }

    const savedState = sessionStorage.getItem("audioState");
    if (savedState) {
      const state = JSON.parse(savedState);

      // Restore track and metadata
      player.audio.src = state.src;
      player.trackName.textContent = state.trackName;
      currentTrackIndex = state.currentTrackIndex;
      isRepeatEnabled = state.isRepeatEnabled;
      isPlayerHidden = state.isPlayerHidden !== undefined ? state.isPlayerHidden : true;
      player.repeatBtn.style.opacity = isRepeatEnabled ? "1" : "0.5";

      // Restore artwork if available and on desktop
      if (state.artworkSrc && !isMobileDevice()) {
        player.artworkImage.src = state.artworkSrc;
        player.artworkImage.style.display = "block";
        
        // Ensure proper scaling and dimensions
        player.artworkImage.style.width = "100%";
        player.artworkImage.style.height = "100%";
        player.artworkImage.style.objectFit = "contain";
        player.artworkImage.style.borderRadius = "50%";
        
        if (player.artworkPlaceholder) {
          player.artworkPlaceholder.style.display = "none";
        }
      }

      // Show player if there was a track
      if (state.src) {
        player.playerContainer.classList.add("active");
        
        // Apply hidden state if needed
        if (isPlayerHidden) {
          player.playerContainer.classList.add("hidden");
        } else {
          player.playerContainer.classList.remove("hidden");
        }
        
        updateToggleButtonIcon();
      }

      // Function to handle playback restoration
      const restorePlayback = () => {
        player.audio.currentTime = state.currentTime;
        if (state.isPlaying) {
          player.audio.play().then(() => {
            updateArtworkSpinning(true);
            player.playBtn.classList.add("playing");
            player.playBtn.querySelector("i").classList.remove("fa-play");
            player.playBtn.querySelector("i").classList.add("fa-pause");
          }).catch(error => {
            console.log("Auto-play prevented by browser:", error);
          });
        }
      };

      // Wait for audio to be ready before restoring playback
      if (player.audio.readyState > 1) {
        restorePlayback();
      } else {
        player.audio.addEventListener("canplay", restorePlayback, {
          once: true,
        });
      }
    }
  };

  // Function to set proper artwork styling
  const setProperArtworkStyling = (artworkElement) => {
    if (!artworkElement) return;
    
    // Ensure proper scaling and dimensions
    artworkElement.style.width = "100%";
    artworkElement.style.height = "100%";
    artworkElement.style.objectFit = "cover";
    artworkElement.style.borderRadius = "50%";
    artworkElement.style.margin = "0";
    artworkElement.style.padding = "0";
    artworkElement.style.display = "block";
  };

  // Track card play buttons
  document.querySelectorAll(".play-track-btn").forEach((button, index) => {
    button.addEventListener("click", () => {
      stopAllArtworkSpinning();
      currentTrackIndex = index;
      const trackUrl = button.dataset.trackUrl;
      const trackName = button.dataset.trackName;
      const trackArtwork = button.dataset.trackArtwork;

      player.audio.src = trackUrl;
      player.trackName.textContent = trackName;
      
      // Only load and display artwork on desktop
      if (!isMobileDevice() && trackArtwork) {
        player.artworkImage.src = trackArtwork;
        player.artworkImage.style.display = "block";
        
        // Ensure proper scaling and dimensions
        player.artworkImage.style.width = "100%";
        player.artworkImage.style.height = "100%";
        player.artworkImage.style.objectFit = "contain";
        player.artworkImage.style.borderRadius = "50%";
        
        if (player.artworkPlaceholder) {
          player.artworkPlaceholder.style.display = "none";
        }
      }

      // Show the player and unhide it when a track is loaded
      player.playerContainer.classList.add("active");
      player.playerContainer.classList.remove("hidden");
      isPlayerHidden = false;
      updateToggleButtonIcon();

      // Update play button icon
      player.playBtn.classList.add("playing");
      player.playBtn.querySelector("i").classList.remove("fa-play");
      player.playBtn.querySelector("i").classList.add("fa-pause");

      player.audio.play().then(() => {
        updateArtworkSpinning(true);
      }).catch(error => {
        console.log("Auto-play prevented by browser:", error);
        // Still show the player even if autoplay is blocked
        player.playerContainer.classList.add("active");
      });
      updatePlayerLayout();
      storeTrackList();
      saveState();
    });
  });

  // Play/Pause
  player.playBtn.addEventListener("click", () => {
    if (!player.audio.src) return;
    if (player.audio.paused) {
      player.audio.play().then(() => {
        updateArtworkSpinning(true);
        player.playBtn.classList.add("playing");
        player.playBtn.querySelector("i").classList.remove("fa-play");
        player.playBtn.querySelector("i").classList.add("fa-pause");
        player.progressBar.classList.add("playing");
      }).catch(error => {
        console.log("Play prevented by browser:", error);
      });
    } else {
      player.audio.pause();
      updateArtworkSpinning(false);
      player.playBtn.classList.remove("playing");
      player.playBtn.querySelector("i").classList.remove("fa-pause");
      player.playBtn.querySelector("i").classList.add("fa-play");
      player.progressBar.classList.remove("playing");
    }
    saveState();
  });

  // Stop
  player.stopBtn.addEventListener("click", () => {
    if (!player.audio.src) return;
    player.audio.pause();
    player.audio.currentTime = 0;
    player.playBtn.classList.remove("playing");
    player.playBtn.querySelector("i").classList.remove("fa-pause");
    player.playBtn.querySelector("i").classList.add("fa-play");
    stopAllArtworkSpinning();
    saveState();
  });

  // Restart
  player.restartBtn.addEventListener("click", () => {
    if (!player.audio.src) return;
    player.audio.currentTime = 0;
    player.audio.play().then(() => {
      updateArtworkSpinning(true);
      player.playBtn.classList.add("playing");
      player.playBtn.querySelector("i").classList.remove("fa-play");
      player.playBtn.querySelector("i").classList.add("fa-pause");
    }).catch(error => {
      console.log("Play prevented by browser:", error);
    });
    saveState();
  });

  // Repeat
  player.repeatBtn.addEventListener("click", () => {
    isRepeatEnabled = !isRepeatEnabled;
    player.repeatBtn.style.opacity = isRepeatEnabled ? "1" : "0.5";
    saveState();
  });

  // Previous track
  player.prevBtn.addEventListener("click", () => {
    if (trackList.length === 0 || currentTrackIndex === -1) return;
    stopAllArtworkSpinning();
    currentTrackIndex =
      (currentTrackIndex - 1 + trackList.length) % trackList.length;
    const track = trackList[currentTrackIndex];
    player.audio.src = track.url;
    player.trackName.textContent = track.name;
    
    // Only show artwork on desktop
    if (!isMobileDevice()) {
      player.artworkImage.src = track.artwork;
      player.artworkImage.style.display = "block";
      
      // Ensure proper scaling and dimensions
      player.artworkImage.style.width = "100%";
      player.artworkImage.style.height = "100%";
      player.artworkImage.style.objectFit = "contain";
      player.artworkImage.style.borderRadius = "50%";
      
      if (player.artworkPlaceholder) {
        player.artworkPlaceholder.style.display = "none";
      }
    }
    
    // Update play button icon
    player.playBtn.classList.add("playing");
    player.playBtn.querySelector("i").classList.remove("fa-play");
    player.playBtn.querySelector("i").classList.add("fa-pause");
    
    player.audio.play().then(() => {
      updateArtworkSpinning(true);
    }).catch(error => {
      console.log("Play prevented by browser:", error);
    });
    updatePlayerLayout();
    saveState();
  });

  // Next track
  player.nextBtn.addEventListener("click", () => {
    if (trackList.length === 0 || currentTrackIndex === -1) return;
    stopAllArtworkSpinning();
    currentTrackIndex = (currentTrackIndex + 1) % trackList.length;
    const track = trackList[currentTrackIndex];
    player.audio.src = track.url;
    player.trackName.textContent = track.name;
    
    // Only show artwork on desktop
    if (!isMobileDevice()) {
      player.artworkImage.src = track.artwork;
      player.artworkImage.style.display = "block";
      
      // Ensure proper scaling and dimensions
      player.artworkImage.style.width = "100%";
      player.artworkImage.style.height = "100%";
      player.artworkImage.style.objectFit = "contain";
      player.artworkImage.style.borderRadius = "50%";
      
      if (player.artworkPlaceholder) {
        player.artworkPlaceholder.style.display = "none";
      }
    }
    
    // Update play button icon
    player.playBtn.classList.add("playing");
    player.playBtn.querySelector("i").classList.remove("fa-play");
    player.playBtn.querySelector("i").classList.add("fa-pause");
    
    player.audio.play().then(() => {
      updateArtworkSpinning(true);
    }).catch(error => {
      console.log("Play prevented by browser:", error);
    });
    updatePlayerLayout();
    saveState();
  });

  // Progress bar click
  player.progressContainer.addEventListener("click", (e) => {
    if (!player.audio.src) return;
    const rect = player.progressContainer.getBoundingClientRect();
    const pos = (e.clientX - rect.left) / rect.width;
    player.audio.currentTime = pos * player.audio.duration;
    saveState();
  });

  // Audio time update
  player.audio.addEventListener("timeupdate", () => {
    if (!player.audio.duration) return;
    const progress = (player.audio.currentTime / player.audio.duration) * 100;
    player.progressBar.style.width = `${progress}%`;
    player.currentTime.textContent = formatTime(player.audio.currentTime);
  });

  // Audio loaded metadata
  player.audio.addEventListener("loadedmetadata", () => {
    player.totalTime.textContent = formatTime(player.audio.duration);
  });

  // Audio ended
  player.audio.addEventListener("ended", () => {
    if (isRepeatEnabled) {
      player.audio.currentTime = 0;
      player.audio.play().then(() => {
        updateArtworkSpinning(true);
      }).catch(error => {
        console.log("Play prevented by browser:", error);
      });
    } else if (currentTrackIndex < trackList.length - 1) {
      // Play next track
      player.nextBtn.click();
    } else {
      // End of playlist
      player.playBtn.classList.remove("playing");
      player.playBtn.querySelector("i").classList.remove("fa-pause");
      player.playBtn.querySelector("i").classList.add("fa-play");
      stopAllArtworkSpinning();
    }
  });

  // Update player layout
  const updatePlayerLayout = () => {
    // Show player when a track is loaded
    if (player.audio.src) {
      player.playerContainer.classList.add("active");
    } else {
      player.playerContainer.classList.remove("active");
    }

    // Update play button icon
    if (!player.audio.paused) {
      player.playBtn.classList.add("playing");
      player.playBtn.querySelector("i").classList.remove("fa-play");
      player.playBtn.querySelector("i").classList.add("fa-pause");
    } else {
      player.playBtn.classList.remove("playing");
      player.playBtn.querySelector("i").classList.remove("fa-pause");
      player.playBtn.querySelector("i").classList.add("fa-play");
    }
  };

  // Format time (seconds to MM:SS)
  function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}:${secs < 10 ? "0" : ""}${secs}`;
  }

  // Initialize
  storeTrackList();
  restoreState();
  updatePlayerLayout();
  
  // Initialize audio visualizer only on desktop
  if (!isMobileDevice()) {
    initAudioVisualizer();
  } else {
    console.log("Mobile device detected, skipping audio visualizer initialization");
  }
  
  // Add resize listener to handle device transitions
  window.addEventListener('resize', function() {
    // If device switches between mobile and desktop, refresh the page to reinitialize components
    const wasMobile = isMobileDevice();
    
    // Add debounce to avoid multiple quick triggers
    clearTimeout(window.resizeTimeout);
    window.resizeTimeout = setTimeout(function() {
      const isMobileNow = isMobileDevice();
      if (wasMobile !== isMobileNow) {
        // Device has switched between mobile and desktop mode
        // We could reload the page, but for a smoother experience, we'll just update components
        
        // Reinitialize visualizer if we're now on desktop
        if (!isMobileNow) {
          initAudioVisualizer();
        }
      }
    }, 250);
  });
  
  // Function to initialize the audio visualizer
  function initAudioVisualizer() {
    const visualizerContainer = document.getElementById('audio-visualizer');
    if (!visualizerContainer) return;
    
    // Clear any existing bars
    visualizerContainer.innerHTML = '';
    
    // Create even more bars for the visualizer (increased from 100 to 150)
    const barCount = 150;
    for (let i = 0; i < barCount; i++) {
      const bar = document.createElement('div');
      bar.className = 'visualizer-bar';
      visualizerContainer.appendChild(bar);
    }
    
    // Start the animation when audio is playing, pause when paused
    player.audio.addEventListener('play', startVisualizer);
    player.audio.addEventListener('pause', pauseVisualizer);
    player.audio.addEventListener('ended', pauseVisualizer);
    
    // If audio is already playing, start the visualizer
    if (!player.audio.paused && player.audio.src) {
      startVisualizer();
    }
  }
  
  // Function to start the visualizer animation
  function startVisualizer() {
    const bars = document.querySelectorAll('.visualizer-bar');
    if (!bars.length) return;
    
    // Calculate the width of each bar to ensure they fill the container with no gaps
    const visualizerContainer = document.getElementById('audio-visualizer');
    if (visualizerContainer) {
      // Always show visualizer when playing
      visualizerContainer.style.opacity = '1';
      
      // Calculate the exact width needed to fill the container with no gaps
      const containerWidth = visualizerContainer.offsetWidth;
      const barWidth = containerWidth / bars.length;
      
      // Apply the calculated width to each bar
      bars.forEach(bar => {
        // Set exact width with no margins or padding
        bar.style.width = `${barWidth}px`;
        bar.style.margin = '0';
        bar.style.padding = '0';
        bar.style.boxSizing = 'border-box';
      });
    }
    
    // Add playing class to progress bar
    player.progressBar.classList.add("playing");
    
    // Calculate the maximum bar height (85% of the visualizer container height)
    const maxBarHeight = Math.round(visualizerContainer.offsetHeight * 0.85);
    
    // Check if bars already have animation (were paused)
    const barsHaveAnimation = bars[0].style.animation && bars[0].style.animation !== 'none';
    
    if (barsHaveAnimation) {
      // If bars already have animation, just resume it
      bars.forEach(bar => {
        bar.style.animationPlayState = 'running';
      });
    } else {
      // Animate each bar with a random height and duration
      bars.forEach((bar, index) => {
        // Random height between 5px and maxBarHeight
        const height = 5 + Math.random() * (maxBarHeight - 5);
        // Random duration between 0.4s and 1.2s
        const duration = 0.4 + Math.random() * 0.8;
        // Random delay to create a more natural effect
        const delay = Math.random() * 0.3;
        
        // Set custom properties for the animation
        bar.style.setProperty('--bar-height', `${height}px`);
        bar.style.animation = `equalizer ${duration}s ease-in-out ${delay}s infinite`;
        bar.style.animationPlayState = 'running';
        
        // Consistent opacity for cleaner look
        bar.style.opacity = '0.9';
      });
    }
  }
  
  // Function to pause the visualizer animation
  function pauseVisualizer() {
    const bars = document.querySelectorAll('.visualizer-bar');
    if (!bars.length) return;
    
    // Keep the visualizer container visible
    const visualizerContainer = document.getElementById('audio-visualizer');
    if (visualizerContainer) {
      // Keep it visible
      visualizerContainer.style.opacity = '1';
    }
    
    // Remove playing class from progress bar
    player.progressBar.classList.remove("playing");
    
    // Pause the animation for each bar (don't hide them)
    bars.forEach(bar => {
      // Pause the animation instead of stopping it
      bar.style.animationPlayState = 'paused';
      
      // Keep the current height
      // Don't set height to 0 or remove the animation
    });
  }
});
