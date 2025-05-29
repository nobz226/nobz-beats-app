// guides.js
document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const suggestionChips = document.querySelectorAll('.chip');
    const newChatBtn = document.getElementById('newChatBtn');
    const stopResponseBtn = document.getElementById('stopResponseBtn');

    let isWaitingForResponse = false;
    let shouldStopTyping = false;
    let currentTypewriterTimeout = null;

    // Initially disable the stop button since no response is in progress
    stopResponseBtn.disabled = true;
    
    // Scroll to bottom of chat
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Type out the message gradually with stop functionality
    function typeMessage(messageDiv, message, index = 0) {
        if (shouldStopTyping) {
            shouldStopTyping = false;
            return;
        }

        if (index < message.length) {
            messageDiv.innerHTML = message.slice(0, index + 1);
            index++;
            currentTypewriterTimeout = setTimeout(() => typeMessage(messageDiv, message, index), 50);
        } else {
            currentTypewriterTimeout = null;
            isWaitingForResponse = false;
        }
    }

    // Add message to chat
    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = isUser ? 'user-message' : 'bot-message';
        
        if (!isUser) {
            message = message.replace(/\n/g, '<br>');
            message = message.replace(/Alex/g, '<strong>Alex</strong>');
            // Convert markdown lists to HTML
            message = message.replace(/^\s*[\-\*]\s(.+)/gm, '<li>$1</li>');
            message = message.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
            // Convert numbered lists
            message = message.replace(/^\s*\d+\.\s(.+)/gm, '<li>$1</li>');
            message = message.replace(/(<li>.*<\/li>)/s, '<ol>$1</ol>');
        }

        chatMessages.appendChild(messageDiv);
        scrollToBottom();

        if (!isUser) {
            typeMessage(messageDiv, message);
        } else {
            messageDiv.innerHTML = message;
        }
    }

    // Show loading indicator
    function showLoading() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'bot-message loading';
        loadingDiv.innerHTML = 'Thinking...';
        loadingDiv.id = 'loadingMessage';
        chatMessages.appendChild(loadingDiv);
        scrollToBottom();
    }

    // Remove loading indicator
    function removeLoading() {
        const loadingMessage = document.getElementById('loadingMessage');
        if (loadingMessage) {
            loadingMessage.remove();
        }
    }

    // Send message to API
    async function sendMessage(message) {
        if (!message.trim() || isWaitingForResponse) return;

        isWaitingForResponse = true;
        shouldStopTyping = false;

        // Enable stop button when sending message
        stopResponseBtn.disabled = false;

        // Add user message to chat
        addMessage(message, true);
        chatInput.value = '';

        // Show loading indicator
        showLoading();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            
            // Remove loading indicator
            removeLoading();

            // Only add bot response if we haven't stopped
            if (!shouldStopTyping) {
                addMessage(data.answer);
            }

            // Disable stop button after response is complete
            if (!isWaitingForResponse) {
                stopResponseBtn.disabled = true;
            }

        } catch (error) {
            console.error('Error:', error);
            removeLoading();
            if (!shouldStopTyping) {
                addMessage('Sorry, I encountered an error. Please try again in a moment.');
            }
            // Disable stop button on error
            stopResponseBtn.disabled = true;
        }

        isWaitingForResponse = false;
    }

    // Event listeners
    sendBtn.addEventListener('click', () => {
        const message = chatInput.value.trim();
        if (message) {
            sendMessage(message);
        }
    });

    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const message = chatInput.value.trim();
            if (message) {
                sendMessage(message);
            }
        }
    });

    suggestionChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const question = chip.dataset.question;
            chatInput.value = question;
            sendMessage(question);
        });
    });

    // New Chat button event listener
    newChatBtn.addEventListener('click', () => {
        // Stop any ongoing typewriter effect
        if (currentTypewriterTimeout) {
            clearTimeout(currentTypewriterTimeout);
            currentTypewriterTimeout = null;
        }
        shouldStopTyping = true;
        isWaitingForResponse = false;
        stopResponseBtn.disabled = true;
        
        chatMessages.innerHTML = `
            <div class="bot-message">
                Hi! I'm <strong>Alex</strong>, your beat making and music production guide. I can help you with making some beats and have fun doing it.
            </div>
        `;
        chatInput.value = '';
        chatInput.focus();
    });

    // Stop Response button event listener
    stopResponseBtn.addEventListener('click', () => {
        // Stop the typewriter effect
        if (currentTypewriterTimeout) {
            clearTimeout(currentTypewriterTimeout);
            currentTypewriterTimeout = null;
        }
        shouldStopTyping = true;
        isWaitingForResponse = false;
        removeLoading();
        
        // Add a message indicating the response was stopped
        const messageDiv = document.createElement('div');
        messageDiv.className = 'bot-message';
        messageDiv.innerHTML = 'Response stopped.';
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
        
        // Disable stop button after stopping
        stopResponseBtn.disabled = true;
    });
});
