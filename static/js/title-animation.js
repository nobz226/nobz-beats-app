document.addEventListener('DOMContentLoaded', function() {
    // Get all title elements
    const titles = document.querySelectorAll('.text-title');
    
    titles.forEach(title => {
        // Remove any existing ::after styling by adding a class
        title.classList.add('no-after-cursor');
        
        // Create a real cursor element
        const cursor = document.createElement('span');
        cursor.classList.add('terminal-cursor');
        cursor.style.position = 'absolute';
        cursor.style.width = '11.5px';  // 15% longer than 10px
        cursor.style.height = '3px';
        cursor.style.backgroundColor = '#ffffff';
        cursor.style.display = 'inline-block';
        cursor.style.left = '0px';
        cursor.style.bottom = '0.5em';
        cursor.style.animation = 'blinkCursor 0.8s step-end infinite';
        cursor.style.zIndex = '10';
        
        // Add the cursor to the title
        title.appendChild(cursor);
        
        // Get all words in the title
        const words = title.querySelectorAll('.word');
        let totalChars = 0;
        let capitalCount = 0; // Track capital letters for color alternation
        
        // Process each word
        words.forEach(word => {
            const text = word.textContent.trim();
            word.textContent = ''; // Clear the word
            
            // Create spans for each character
            for (let i = 0; i < text.length; i++) {
                const charSpan = document.createElement('span');
                charSpan.classList.add('char');
                charSpan.textContent = text[i];
                charSpan.dataset.position = totalChars; // Store position for cursor movement
                
                // Check if this is a capital letter to determine color
                if (/[A-Z]/.test(text[i])) {
                    // Alternate colors for capital letters
                    if (capitalCount % 2 === 0) {
                        charSpan.style.color = '#ffffff'; // White for even capitals
                    } else {
                        charSpan.style.color = '#fc4242'; // Red for odd capitals
                    }
                    capitalCount++;
                } else {
                    // For non-capital letters, use the color of the previous capital
                    if (capitalCount > 0) {
                        if ((capitalCount - 1) % 2 === 0) {
                            charSpan.style.color = '#ffffff'; // White
                        } else {
                            charSpan.style.color = '#fc4242'; // Red
                        }
                    } else {
                        // Default color if no capital yet
                        charSpan.style.color = '#ffffff';
                    }
                }
                
                // Calculate delay: 1s initial delay + time for previous characters
                const delay = 1 + (totalChars * 0.15); // Slower typing speed
                charSpan.style.animationDelay = `${delay}s`;
                
                word.appendChild(charSpan);
                totalChars++;
            }
            
            // Add a space after each word except the last one
            if (word !== words[words.length - 1]) {
                const space = document.createElement('span');
                space.textContent = ' ';
                space.dataset.position = totalChars;
                word.after(space);
                totalChars++;
            }
        });
        
        // Simple cursor movement function
        function updateCursor() {
            // Find all visible characters
            const chars = Array.from(title.querySelectorAll('.char'));
            const visibleChars = chars.filter(char => 
                window.getComputedStyle(char).opacity > 0
            );
            
            if (visibleChars.length > 0) {
                // Get the last visible character
                const lastChar = visibleChars[visibleChars.length - 1];
                const rect = lastChar.getBoundingClientRect();
                const titleRect = title.getBoundingClientRect();
                
                // Position cursor after the last visible character with a small offset
                const cursorLeft = rect.right - titleRect.left + 2; // 2px ahead
                cursor.style.left = `${cursorLeft}px`;
            }
        }
        
        // Update cursor position every 100ms
        const cursorInterval = setInterval(updateCursor, 100);
        
        // Stop updating after all characters have appeared
        setTimeout(() => {
            clearInterval(cursorInterval);
            
            // Final position
            const allChars = title.querySelectorAll('.char');
            if (allChars.length > 0) {
                const lastChar = allChars[allChars.length - 1];
                const rect = lastChar.getBoundingClientRect();
                const titleRect = title.getBoundingClientRect();
                const cursorLeft = rect.right - titleRect.left + 2; // 2px ahead
                cursor.style.left = `${cursorLeft}px`;
            }
        }, (totalChars * 150) + 2000);
    });
}); 