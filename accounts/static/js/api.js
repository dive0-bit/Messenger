/**
 * API HELPER - Messenger App
 * 
 * Contains utility functions for making API calls to the backend.
 * Makes it easy to fetch data and send messages without writing fetch() every time.
 */

/**
 * Get CSRF token from browser cookies
 * CSRF (Cross-Site Request Forgery) protection - Django requires this for POST/DELETE requests
 * 
 * @returns {string} The CSRF token value
 */
function getCsrfToken() {
    const cookie = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='));
    
    return cookie ? decodeURIComponent(cookie.split('=')[1]) : '';
}

/**
 * Make an API request to the backend
 * 
 * This function handles all the boilerplate:
 * - Setting proper headers
 * - Adding CSRF token
 * - Error handling
 * - JSON parsing
 * 
 * @param {string} url - API endpoint (e.g., '/api/conversations/')
 * @param {object} options - Optional: method, body, headers
 * @returns {Promise} Response data as JSON
 * 
 * Example usage:
 *   const conversations = await makeApiCall('/api/conversations/');
 *   await makeApiCall('/api/conversations/', { 
 *       method: 'POST', 
 *       body: JSON.stringify({ recipient_id: 5 }) 
 *   });
 */
async function makeApiCall(url, options = {}) {
    // Set up headers
    const headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
        ...(options.headers || {})  // Allow custom headers too
    };

    try {
        // Make the fetch request
        const response = await fetch(url, { 
            ...options, 
            headers 
        });

        // Check if response is OK (status 200-299)
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Request failed');
        }

        // Parse and return response
        return await response.json();

    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

/**
 * Get all conversations for current user
 * 
 * @returns {Promise<Array>} List of conversation objects
 */
async function getConversations() {
    return await makeApiCall('/api/conversations/');
}

/**
 * Get all messages in a specific conversation
 * 
 * @param {number} conversationId - ID of the conversation
 * @returns {Promise<Array>} List of message objects
 */
async function getMessages(conversationId) {
    return await makeApiCall(`/api/conversations/${conversationId}/messages/`);
}

/**
 * Send a message via REST API (fallback if WebSocket fails)
 * 
 * @param {number} conversationId - ID of the conversation
 * @param {string} content - Message text
 * @returns {Promise<Object>} Message object
 */
async function sendMessage(conversationId, content) {
    return await makeApiCall(
        `/api/conversations/${conversationId}/messages/`,
        {
            method: 'POST',
            body: JSON.stringify({ content })
        }
    );
}

/**
 * Create or get a conversation with a user
 * 
 * @param {number} recipientId - ID of the user to chat with
 * @returns {Promise<Object>} Conversation object
 */
async function startConversation(recipientId) {
    return await makeApiCall('/api/conversations/', {
        method: 'POST',
        body: JSON.stringify({ recipient_id: recipientId })
    });
}

/**
 * Delete a conversation
 * 
 * @param {number} conversationId - ID of the conversation to delete
 * @returns {Promise<void>}
 */
async function deleteConversation(conversationId) {
    return await makeApiCall(
        `/api/conversations/${conversationId}/`,
        { method: 'DELETE' }
    );
}
