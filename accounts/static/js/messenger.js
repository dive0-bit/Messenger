/**
 * MESSENGER APP - Main Logic
 * 
 * This file contains the main logic for the messenger app.
 * It uses helper functions from:
 * - api.js (for REST API calls)
 * - websocket.js (for real-time connections)
 */

// Get current logged-in user's ID from the HTML (set by Django)
const currentUserId = window.currentUserId;

// Track which conversation is currently open
let activeConversationId = null;

/**
 * Handle incoming WebSocket messages
 * 
 * @param {object} payload - Data received from server
 */
function handleWebSocketMessage(payload) {
    // Connection opened
    if (payload.type === 'open') {
        enableMessageInput();
        document.querySelector('#message-input').focus();
        return;
    }
    
    // New message received
    if (payload.type === 'message') {
        // Only add if it's for the current conversation
        if (payload.message.conversation === activeConversationId) {
            addMessageToUI(payload.message);
            // Refresh conversation list to show latest message
            loadAndRenderConversations();
            // Show notification if message is from someone else
            showMessageNotification(payload.message);
        }
        return;
    }
    
    // Error from server
    if (payload.type === 'error') {
        alert('Error: ' + payload.detail);
        return;
    }
}

/**
 * Handle WebSocket connection closing
 * 
 * @param {event} event - Close event from WebSocket
 */
function handleWebSocketClose(event) {
    // 4403 = Authorization error (access denied)
    if (event.code === 4403) {
        alert('You do not have access to this conversation.');
        disableMessageInput();
        return;
    }
    
    // Reconnect attempts run in websocket.js; REST remains available meanwhile.
    updateChatSubtitle('Realtime connection unavailable. Messages use REST fallback.');
}

/**
 * Handle WebSocket errors
 * 
 * @param {error} error - Error object
 */
function handleWebSocketError(error) {
    console.error('WebSocket error:', error);
    updateChatSubtitle('Realtime connection unavailable. Messages use REST fallback.');
}

/**
 * Open a conversation with a specific person
 * 
 * Steps:
 * 1. Close previous connection if any
 * 2. Set active conversation
 * 3. Update UI (header, avatar, title)
 * 4. Load previous messages from server
 * 5. Connect WebSocket for real-time updates
 * 
 * @param {object} conversation - Conversation object with id, participant, etc.
 */
function selectConversation(conversation) {
    // Close previous WebSocket if any
    closeWebSocket();
    
    // Update state
    activeConversationId = conversation.id;
    
    // Update UI: Title and subtitle
    document.querySelector('#chat-title').textContent = conversation.participant;
    updateChatSubtitle('Conversation');
    
    // Update UI: Avatar
    updateChatAvatar(conversation.participant_picture, conversation.participant);
    
    // Disable input while loading
    disableMessageInput();
    
    // Mark this conversation as active in the list
    markActiveConversation(conversation.id);
    
    // Load all previous messages
    loadAndRenderMessages();
    
    // Connect WebSocket for real-time updates
    connectWebSocket(
        conversation.id,
        handleWebSocketMessage,
        handleWebSocketClose,
        handleWebSocketError
    );
}

/**
 * Load conversations from server and display them
 * 
 * Makes API call to get all conversations, then renders them in the list.
 */
async function loadAndRenderConversations() {
    try {
        const conversations = await getConversations();
        renderConversationsList(conversations);
    } catch (error) {
        showError('Failed to load conversations: ' + error.message);
    }
}

/**
 * Render conversations to the UI
 * 
 * Creates HTML elements for each conversation and adds click handlers.
 * 
 * @param {array} conversations - Array of conversation objects
 */
function renderConversationsList(conversations) {
    const listContainer = document.querySelector('#conversation-list');
    
    // Clear existing content
    listContainer.innerHTML = '';
    
    // Show message if no conversations
    if (!conversations.length) {
        listContainer.innerHTML = '<p class="status" style="padding: 12px;">No conversations yet.</p>';
        return;
    }
    
    // Create HTML for each conversation
    conversations.forEach(conversation => {
        const row = document.createElement('div');
        row.className = 'conversation-row';
        
        // Create conversation button
        const button = document.createElement('button');
        button.className = 'conversation';
        button.dataset.id = conversation.id;
        
        // Avatar HTML (picture or first letter)
        const avatarHtml = conversation.participant_picture
            ? `<img src="${conversation.participant_picture}" alt="">`
            : conversation.participant[0].toUpperCase();
        
        // Conversation content
        button.innerHTML = `
            <span class="mini-avatar">${avatarHtml}</span>
            <span class="conversation-text">
                <strong>${conversation.participant}</strong>
                <small>${conversation.last_message}</small>
            </span>
        `;
        
        // Click handler: select this conversation
        button.addEventListener('click', () => selectConversation(conversation));
        
        // Create delete button
        const deleteButton = document.createElement('button');
        deleteButton.className = 'delete-conversation';
        deleteButton.type = 'button';
        deleteButton.title = 'Delete conversation';
        deleteButton.textContent = '×';
        
        // Click handler: delete this conversation
        deleteButton.addEventListener('click', (event) => {
            event.stopPropagation(); // Don't trigger conversation select
            handleDeleteConversation(conversation.id);
        });
        
        // Add both buttons to the row
        row.appendChild(button);
        row.appendChild(deleteButton);
        listContainer.appendChild(row);
    });

    installImageFallbacks();
}

/**
 * Handle conversation deletion
 * 
 * Asks for confirmation, deletes from server, updates UI.
 * 
 * @param {number} conversationId - ID of conversation to delete
 */
async function handleDeleteConversation(conversationId) {
    // Ask user for confirmation
    const confirmed = confirm('Delete this conversation for all participants?');
    if (!confirmed) return;
    
    try {
        // Call API to delete
        await deleteConversation(conversationId);
        
        // If this was the active conversation, clear it
        if (activeConversationId === conversationId) {
            activeConversationId = null;
            closeWebSocket();
            resetChatUI();
        }
        
        // Reload conversation list
        await loadAndRenderConversations();
        
    } catch (error) {
        alert('Failed to delete conversation: ' + error.message);
    }
}

/**
 * Load all messages from a conversation and display them
 * 
 * Calls API to get messages, then renders them in the chat area.
 */
async function loadAndRenderMessages() {
    try {
        const messages = await getMessages(activeConversationId);
        renderMessagesList(messages);
    } catch (error) {
        showError('Failed to load messages: ' + error.message);
    }
}

/**
 * Render messages to the chat area
 * 
 * Creates HTML for each message and displays them in order.
 * 
 * @param {array} messages - Array of message objects
 */
function renderMessagesList(messages) {
    const container = document.querySelector('#messages');
    container.innerHTML = ''; // Clear
    
    // Show empty state if no messages
    if (!messages.length) {
        container.innerHTML = '<p class="empty">No messages yet. Start the conversation!</p>';
        return;
    }
    
    // Add each message
    messages.forEach(message => addMessageToUI(message));
}

/**
 * Add a single message to the chat UI
 * 
 * Creates the message HTML and appends it to the messages container.
 * Automatically scrolls to bottom.
 * 
 * @param {object} message - Message object with content, sender, created_at
 */
function addMessageToUI(message) {
    const container = document.querySelector('#messages');
    
    // Remove empty state if this is the first message
    const emptyMessage = container.querySelector('.empty');
    if (emptyMessage) emptyMessage.remove();
    
    // Create message element
    const messageDiv = document.createElement('div');
    
    // Add "mine" class if message is from current user (align right)
    messageDiv.className = `message ${message.sender === currentUserId ? 'mine' : ''}`;
    messageDiv.textContent = message.content;
    
    // Add timestamp
    const time = document.createElement('time');
    time.textContent = new Date(message.created_at).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
    });
    messageDiv.appendChild(time);
    
    // Add to container
    container.appendChild(messageDiv);
    
    // Scroll to bottom to show new message
    container.scrollTop = container.scrollHeight;
}

/**
 * Handle form submission (send message)
 * 
 * Gets message from input, sends via WebSocket if available,
 * otherwise falls back to REST API.
 * 
 * @param {event} event - Form submit event
 */
async function handleMessageSubmit(event) {
    event.preventDefault();
    
    // Get message from input
    const input = document.querySelector('#message-input');
    const content = input.value.trim();
    
    // Validate
    if (!content || !activeConversationId) return;
    
    try {
        // Try to send via WebSocket (real-time)
        if (isWebSocketConnected() && sendWebSocketMessage(content)) {
            input.value = '';
        } else {
            // Fall back to REST API
            await sendMessage(activeConversationId, content);
            await loadAndRenderMessages();
            await loadAndRenderConversations();
            input.value = '';
        }
        
    } catch (error) {
        alert('Failed to send message: ' + error.message);
    }
}

/**
 * Handle starting a conversation with a person from the list
 * 
 * @param {number} recipientId - ID of person to chat with
 * @param {string} username - Person's username
 * @param {string} picture - Person's profile picture URL
 */
async function handleSelectPerson(recipientId, username, picture) {
    try {
        // Create/get conversation with this person
        const conversation = await startConversation(recipientId);
        
        // Reload conversation list
        await loadAndRenderConversations();
        
        // Open this conversation
        selectConversation(conversation);
        
    } catch (error) {
        alert('Failed to start conversation: ' + error.message);
    }
}

/**
 * Show notification for new messages
 * 
 * Uses browser's Notification API to alert user.
 * Only shows if:
 * - Browser supports notifications
 * - User granted permission
 * - Message is from someone else (not current user)
 * 
 * @param {object} message - Message object
 */
function showMessageNotification(message) {
    // Check if Notification API is available
    if (!('Notification' in window)) {
        return;
    }
    
    // Check if user gave permission
    if (Notification.permission !== 'granted') {
        return;
    }
    
    // Don't notify if message is from current user
    if (message.sender === currentUserId) {
        return;
    }
    
    // Show notification
    new Notification('New Message', {
        body: message.content,
        icon: '/static/icon.png' // Optional: add an icon
    });
}

/**
 * Request permission for browser notifications
 * 
 * Ask user if we can show desktop notifications.
 * Safe to call - user can decline.
 */
function requestNotificationPermission() {
    if (!('Notification' in window)) {
        return; // Not supported
    }
    
    if (Notification.permission === 'granted') {
        return; // Already granted
    }
    
    if (Notification.permission !== 'denied') {
        // Ask user for permission
        Notification.requestPermission();
    }
}

/**
 * ========== UI HELPER FUNCTIONS ==========
 */

/**
 * Update chat header subtitle
 */
function updateChatSubtitle(text) {
    document.querySelector('#chat-subtitle').textContent = text;
}

/**
 * Update chat header avatar
 */
function updateChatAvatar(pictureUrl, name) {
    const avatar = document.querySelector('#chat-avatar');
    if (pictureUrl) {
        avatar.innerHTML = `<img src="${pictureUrl}" alt="${name} profile picture" data-fallback="${name[0].toUpperCase()}">`;
        installImageFallbacks();
    } else {
        avatar.textContent = name[0].toUpperCase();
    }
}

function installImageFallbacks() {
    document.querySelectorAll('img[data-fallback]').forEach(image => {
        const replaceWithFallback = () => {
            const fallback = document.createElement('span');
            fallback.textContent = image.dataset.fallback;
            image.replaceWith(fallback);
        };

        image.addEventListener('error', replaceWithFallback, { once: true });
        if (image.complete && image.naturalWidth === 0) {
            replaceWithFallback();
        }
    });
}

/**
 * Mark a conversation as active in the list
 */
function markActiveConversation(conversationId) {
    document.querySelectorAll('.conversation').forEach(el => {
        el.classList.toggle('active', Number(el.dataset.id) === conversationId);
    });
}

/**
 * Enable message input
 */
function enableMessageInput() {
    document.querySelector('#message-input').disabled = false;
    document.querySelector('.send').disabled = false;
}

/**
 * Disable message input
 */
function disableMessageInput() {
    document.querySelector('#message-input').disabled = true;
    document.querySelector('.send').disabled = true;
}

/**
 * Reset chat UI to default state
 */
function resetChatUI() {
    document.querySelector('#chat-title').textContent = 'Select a person';
    document.querySelector('#chat-subtitle').textContent = 'Choose someone from the People list to begin.';
    document.querySelector('#messages').innerHTML = '<p class="empty">Your messages will appear here. Start a conversation from the left.</p>';
    disableMessageInput();
}

/**
 * Show error message
 */
function showError(message) {
    const container = document.querySelector('#conversation-list');
    container.innerHTML = `<p class="status" style="padding: 12px;">${message}</p>`;
}

/**
 * ========== INITIALIZATION ==========
 * 
 * Run when page loads
 */
document.addEventListener('DOMContentLoaded', () => {
    // Set up event listeners
    
    // Person list: click to start conversation
    document.querySelectorAll('.person').forEach(button => {
        button.addEventListener('click', () => {
            handleSelectPerson(
                button.dataset.userId,
                button.dataset.username,
                button.dataset.picture
            );
        });
    });
    
    // Message form: submit to send message
    document.querySelector('#composer').addEventListener('submit', handleMessageSubmit);
    
    // Load initial conversations
    loadAndRenderConversations().catch(error => {
        showError('Failed to load conversations: ' + error.message);
    });

    installImageFallbacks();
    
    // Request notification permission
    requestNotificationPermission();
});
