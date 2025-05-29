document.addEventListener("DOMContentLoaded", function () {
  // DOM Elements
  const urlInput = document.getElementById("youtube-url");
  const fetchBtn = document.getElementById("fetch-btn");
  const videoList = document.querySelector(".video-list");
  const videoItems = document.querySelector(".video-items");
  const selectAllCheckbox = document.getElementById("select-all");
  const selectedCount = document.querySelector(".selected-count");
  const convertBtn = document.getElementById("convert-btn");
  const conversionControls = document.querySelector(".conversion-controls");
  const formatBtns = document.querySelectorAll(".format-btn");
  const progressBar = document.querySelector(".youtube-progress-bar");
  const statusText = document.querySelector(".youtube-status-text");
  const conversionStatus = document.querySelector(".conversion-status");

  // State
  let selectedFormat = null;
  let videos = [];
  let isConverting = false;
  let currentSessionId = null; // Track the current session ID

  // Format selection
  formatBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      formatBtns.forEach((b) => b.classList.remove("selected"));
      btn.classList.add("selected");
      selectedFormat = btn.dataset.format;
      updateConvertButton();
    });
  });

  // URL input validation
  urlInput.addEventListener("input", () => {
    const url = urlInput.value.trim();
    fetchBtn.disabled = !isValidYouTubeUrl(url);
  });

  // Select All Functionality
  selectAllCheckbox.addEventListener("change", () => {
    const checkboxes = document.querySelectorAll(".video-checkbox");
    checkboxes.forEach((checkbox) => {
      checkbox.checked = selectAllCheckbox.checked;
    });
    updateSelectedCount();
  });

  // Fetch Video Information
  fetchBtn.addEventListener("click", async () => {
    const url = urlInput.value.trim();
    if (!isValidYouTubeUrl(url)) return;

    try {
      fetchBtn.disabled = true;
      progressBar.style.width = "50%";
      conversionStatus.style.display = "block";
      statusText.textContent = "Fetching video information...";

      const response = await fetch("/youtube/fetch", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const data = await response.json();
      videos = data.videos;

      // Populate video list
      videoItems.innerHTML = "";
      videos.forEach((video, index) => {
        videoItems.appendChild(createVideoElement(video, index));
      });

      videoList.style.display = "block";
      conversionControls.style.display = "block";
      progressBar.style.width = "100%";
      statusText.textContent = "Videos fetched successfully!";

      setTimeout(() => {
        conversionStatus.style.display = "none";
        progressBar.style.width = "0%";
      }, 2000);
    } catch (error) {
      console.error("Error:", error);
      statusText.textContent = `Error: ${error.message}`;
      progressBar.style.width = "0%";
    } finally {
      fetchBtn.disabled = false;
    }
  });

  // Convert Selected Videos
  convertBtn.addEventListener("click", async () => {
    if (isConverting) return;

    const selectedVideos = Array.from(
      document.querySelectorAll(".video-checkbox:checked")
    ).map((checkbox) => videos[parseInt(checkbox.dataset.index)]);

    if (selectedVideos.length === 0 || !selectedFormat) return;

    try {
      isConverting = true;
      convertBtn.disabled = true;
      conversionStatus.style.display = "block";
      statusText.textContent = "Starting conversion...";
      progressBar.style.width = "0%";

      // Create a conversion session
      const sessionResponse = await fetch("/youtube/create-session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          videos: selectedVideos,
          format: selectedFormat,
        }),
      });

      if (!sessionResponse.ok) {
        throw new Error("Failed to create conversion session");
      }

      const sessionData = await sessionResponse.json();
      if (!sessionData.success) {
        throw new Error(sessionData.error || "Failed to create session");
      }

      currentSessionId = sessionData.sessionId;
      console.log(`Created session: ${currentSessionId}`);
      
      // Update video elements with session ID
      selectedVideos.forEach(video => {
        const videoElement = document.querySelector(`[data-video-id="${video.id}"]`);
        if (videoElement) {
          videoElement.setAttribute('data-session-id', currentSessionId);
        }
      });

      // Convert each video
      for (let i = 0; i < selectedVideos.length; i++) {
        const video = selectedVideos[i];
        const progress = (i / selectedVideos.length) * 100;

        statusText.textContent = `Converting ${i + 1}/${
          selectedVideos.length
        }: ${video.title}`;
        progressBar.style.width = `${progress}%`;

        const convertResponse = await fetch("/youtube/convert", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            sessionId: currentSessionId,
            videoId: video.id,
            format: selectedFormat,
          }),
        });

        if (!convertResponse.ok) {
          throw new Error(`Failed to convert: ${video.title}`);
        }

        const convertData = await convertResponse.json();

        // Trigger download
        const link = document.createElement("a");
        link.href = convertData.downloadUrl;
        link.download = convertData.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }

      statusText.textContent = "All conversions completed!";
      progressBar.style.width = "100%";

      setTimeout(() => {
        conversionStatus.style.display = "none";
        progressBar.style.width = "0%";
      }, 3000);

      // Reset selections
      selectAllCheckbox.checked = false;
      document
        .querySelectorAll(".video-checkbox")
        .forEach((cb) => (cb.checked = false));
      updateSelectedCount();
    } catch (error) {
      console.error("Conversion error:", error);
      statusText.textContent = `Error: ${error.message}`;
      progressBar.style.width = "0%";
    } finally {
      isConverting = false;
      convertBtn.disabled = false;
    }
  });

  // Utility Functions
  function isValidYouTubeUrl(url) {
    const pattern = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$/;
    return pattern.test(url);
  }

  function updateConvertButton() {
    const hasSelectedVideos =
      document.querySelectorAll(".video-checkbox:checked").length > 0;
    convertBtn.disabled = !(hasSelectedVideos && selectedFormat);
  }

  function updateSelectedCount() {
    const checkboxes = document.querySelectorAll(".video-checkbox");
    const checkedCount = Array.from(checkboxes).filter(
      (cb) => cb.checked
    ).length;
    selectedCount.textContent = `${checkedCount} selected`;
    updateConvertButton();
  }

  function createVideoElement(video, index) {
    const div = document.createElement("div");
    div.className = "video-item";
    div.setAttribute('data-video-id', video.id);
    
    // Add session ID if available
    if (currentSessionId) {
      div.setAttribute('data-session-id', currentSessionId);
    }
    
    div.innerHTML = `
            <input type="checkbox" class="video-checkbox" data-index="${index}">
            <div class="video-thumbnail">
                <img src="${video.thumbnail}" alt="Video thumbnail">
            </div>
            <div class="video-info">
                <div class="video-title">${video.title}</div>
                <div class="video-uploader">${video.uploader}</div>
            </div>
        `;

    const checkbox = div.querySelector(".video-checkbox");
    checkbox.addEventListener("change", () => {
      updateSelectedCount();
      if (!checkbox.checked) {
        selectAllCheckbox.checked = false;
      }
    });
    return div;
  }

  // Cleanup on page unload
  window.addEventListener("beforeunload", async () => {
    try {
      console.log("Running cleanup on page unload");
      
      // Get all active session IDs
      const sessionIds = [];
      document.querySelectorAll('[data-session-id]').forEach(el => {
        const sessionId = el.getAttribute('data-session-id');
        if (sessionId) {
          sessionIds.push(sessionId);
        }
      });
      
      if (sessionIds.length > 0) {
        console.log(`Cleaning up sessions: ${sessionIds.join(', ')}`);
        
        // Use sendBeacon for reliable delivery during page unload
        const formData = new FormData();
        formData.append('cleanAll', 'true');
        
        // Add each session ID
        sessionIds.forEach(sessionId => {
          formData.append('sessionId', sessionId);
        });
        
        const success = navigator.sendBeacon("/youtube/cleanup", formData);
        console.log(`Cleanup beacon sent: ${success}`);
      } else {
        console.log("No active sessions to clean up");
        const success = navigator.sendBeacon("/youtube/cleanup", new FormData());
        console.log(`General cleanup beacon sent: ${success}`);
      }
    } catch (error) {
      console.error("Cleanup error:", error);
    }
  });
});
