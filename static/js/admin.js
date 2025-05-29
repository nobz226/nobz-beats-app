function selectAllTracks() {
    const checkboxes = document.querySelectorAll('.track-checkbox');
    const areAllChecked = Array.from(checkboxes).every(cb => cb.checked);
    checkboxes.forEach(cb => cb.checked = !areAllChecked);
}

function editSelected() {
    const selectedTracks = document.querySelectorAll('.track-checkbox:checked');
    if (selectedTracks.length !== 1) {
        alert('Please select exactly one track to edit');
        return;
    }

    const trackElement = selectedTracks[0].closest('.admin-track-item');
    const trackId = trackElement.dataset.trackId;
    const trackName = trackElement.dataset.trackName;
    const trackDescription = trackElement.dataset.trackDescription;

    // Update edit form fields
    document.getElementById('edit-track-id').value = trackId;
    document.getElementById('edit-name').value = trackName;
    document.getElementById('edit-description').value = trackDescription || '';
}

function getSelectedTrackIds() {
    const checkedBoxes = document.querySelectorAll('.track-checkbox:checked');
    return Array.from(checkedBoxes).map(cb => 
        cb.closest('.admin-track-item').dataset.trackId
    );
}

    async function downloadSelected() {
        const trackIds = getSelectedTrackIds();
        if (trackIds.length === 0) {
            alert('Please select tracks to download');
            return;
        }

        try {
            const response = await fetch('/download_tracks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ track_ids: trackIds })
            });

            const data = await response.json();

            if (data.success && data.files) {
                // Download each file
                data.files.forEach(file => {
                    const link = document.createElement('a');
                    link.href = file.url;
                    link.download = file.name + '.mp3'; // Assuming MP3 format
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                });
            } else {
                alert(data.message || 'Error preparing downloads');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error downloading tracks');
        }
    }

    function deleteSelected() {
        const trackIds = getSelectedTrackIds();
        if (trackIds.length === 0) {
            alert('Please select tracks to delete');
            return;
        }

        if (confirm('Are you sure you want to delete the selected tracks?')) {
            fetch('/delete_tracks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ track_ids: trackIds })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Error deleting tracks: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error deleting tracks');
            });
        }
    }

// Add event listeners for remove artwork buttons
document.addEventListener('DOMContentLoaded', function() {
    const removeButtons = document.querySelectorAll('.remove-artwork-btn');
    removeButtons.forEach(button => {
        button.addEventListener('click', removeArtwork);
    });
});

// Function to remove artwork
async function removeArtwork(event) {
    event.stopPropagation();
    const button = event.currentTarget;
    const trackId = button.dataset.trackId;
    const artworkType = button.dataset.artworkType;
    
    if (confirm(`Are you sure you want to remove the ${artworkType} artwork?`)) {
        try {
            const response = await fetch('/remove_artwork', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    track_id: trackId, 
                    artwork_type: artworkType 
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update the UI
                const artworkContainer = button.closest(artworkType === 'primary' ? 
                    '.admin-track-artwork-small' : '.admin-track-artwork-secondary-small');
                const img = artworkContainer.querySelector('img');
                
                // Update the image source to the default "No Artwork" image
                img.src = artworkType === 'primary' ? 
                    '/static/uploads/No Artwork' : 
                    '/static/uploads/No Secondary Artwork';
                
                // Remove the button
                button.remove();
                
                // Show success message
                alert('Artwork removed successfully!');
            } else {
                alert('Error removing artwork: ' + (data.message || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error removing artwork');
        }
    }
}
