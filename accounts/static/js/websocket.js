/**
 * WEBSOCKET HANDLER - Messenger App
 * 
 * Manages real-time connections to the backend using WebSocket.
 * WebSocket allows messages to be sent/received instantly without polling.
 * 
 * If WebSocket fails, the app falls back to REST API calls (see api.js).
 */

let chatSocket = null;

/**
 * Connect to WebSocket for a specific conversation
 * 
 * WebSocket gives us real-time messaging - messages appear instantly!
 * Connection: ws://localhost:8000/ws/conversations/{id}/
 * 
 * @param {number} conversationId - ID of the conversation
 * @param {function} onMessage - Callback function when message is received
 * @param {function} onClose - Callback function when connection closes
 * @param {function} onError - Callback function when error occurs
 * @returns {boolean} True if connection succeeded
 */
function connectWebSocket(
    conversationId, 
    onMessage, 
    onClose, 
    onError
) {
    // Determine if we need ws:// or wss:// (secure)
    const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    
    // Create WebSocket connection
    const socketUrl = `${scheme}://${window.location.host}/ws/conversations/${conversationId}/`;
    
    try {
        chatSocket = new WebSocket(socketUrl);
        
        // Called when connection successfully opens
        chatSocket.onopen = () => {
            console.log('WebSocket connected');
            // Enable message input when connected
            if (onMessage) onMessage({ type: 'open' });
        };
        
        // Called when server sends data
        chatSocket.onmessage = (event) => {
            try {
                const payload = JSON.parse(event.data);
                if (onMessage) onMessage(payload);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };
        
        // Called when connection closes
        chatSocket.onclose = (event) => {
            console.log('WebSocket disconnected. Code:', event.code);
            if (onClose) onClose(event);
        };
        
        // Called when connection has an error
        chatSocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            if (onError) onError(error);
        };
        
        return true;
        
    } catch (error) {
        console.error('Failed to create WebSocket:', error);
        if (onError) onError(error);
        return false;
    }
}

/**
 * Send a message through WebSocket
 * 
 * Sends JSON like: { type: 'message', content: 'Hello!' }
 * 
 * @param {string} content - Message text to send
 * @returns {boolean} True if message was sent
 */
function sendWebSocketMessage(content) {
    // Check if WebSocket exists and is open (readyState 1 = OPEN)
    if (!chatSocket || chatSocket.readyState !== WebSocket.OPEN) {
        console.warn('WebSocket not connected');
        return false;
    }
    
    try {
        chatSocket.send(JSON.stringify({
            type: 'message',
            content: content
        }));
        return true;
    } catch (error) {
        console.error('Failed to send WebSocket message:', error);
        return false;
    }
}

/**
 * Close the WebSocket connection
 * 
 * Call this when user switches conversations or logs out.
 */
function closeWebSocket() {
    if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.close();
        chatSocket = null;
        console.log('WebSocket closed');
    }
}

/**
 * Check if WebSocket is currently connected
 * 
 * @returns {boolean} True if connected and ready to send
 */
function isWebSocketConnected() {
    return chatSocket && chatSocket.readyState === WebSocket.OPEN;
}
