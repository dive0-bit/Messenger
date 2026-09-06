# 🔄 Messenger App - Code Flow Diagrams

## 1️⃣ App Startup Flow

```
User Opens messenger/home/
        ↓
Browser loads home.html
        ↓
CSS file (style.css) loaded → Page styled
        ↓
JavaScript files loaded in order:
   1. api.js (defines API functions)
   2. websocket.js (defines WebSocket functions)
   3. messenger.js (main logic)
        ↓
messenger.js runs → DOMContentLoaded event
        ↓
Event listeners attached to:
   - All .person buttons
   - .composer form
        ↓
loadAndRenderConversations() called
        ↓
API call: GET /api/conversations/
        ↓
Display conversations in left sidebar
        ↓
✅ App ready! User can click on person or conversation
```

---

## 2️⃣ Send Message Flow

```
User types message in input box
        ↓
User clicks "Send" button
        ↓
#composer form triggers "submit" event
        ↓
handleMessageSubmit() function called
        ↓
Get message text from input
        ↓
Validation: Check if message is not empty and conversation selected
        ↓
Check: Is WebSocket connected?
        ├─ YES: sendWebSocketMessage(content)
        │        ↓
        │        Send JSON: { type: 'message', content: 'Hello' }
        │        ↓
        │        WebSocket sends instantly to backend
        │
        └─ NO: makeApiCall() for REST fallback
                ↓
                POST /api/conversations/{id}/messages/
                ↓
                Reload messages and conversations
        ↓
Clear input box
        ↓
✅ Message sent!
```

---

## 3️⃣ Receive Message Flow (WebSocket)

```
Server sends message to user via WebSocket
        ↓
Browser receives data event
        ↓
chatSocket.onmessage triggered
        ↓
JSON.parse(event.data) to get payload
        ↓
handleWebSocketMessage(payload) called
        ↓
Check payload type:
        ├─ 'open' → enableMessageInput()
        ├─ 'message' → Check if for current conversation
        │             ↓
        │             addMessageToUI(message) - Show it!
        │             ↓
        │             loadAndRenderConversations() - Update list
        │             ↓
        │             showMessageNotification() - Notify user
        │
        └─ 'error' → alert('Error!')
        ↓
✅ Message displayed in chat!
```

---

## 4️⃣ Open Conversation Flow

```
User clicks on person/conversation
        ↓
Click event → selectConversation(conversation) called
        ↓
Close old WebSocket if exists:
    closeWebSocket()
        ↓
Update state:
    activeConversationId = conversation.id
        ↓
Update UI - Header with name, avatar, etc.
        ├─ updateChatSubtitle('Conversation')
        ├─ updateChatAvatar(picture, name)
        └─ markActiveConversation(id)
        ↓
Disable message input (while loading):
    disableMessageInput()
        ↓
Load all previous messages:
    loadAndRenderMessages()
        ├─ API call: GET /api/conversations/{id}/messages/
        ├─ renderMessagesList(messages)
        └─ Display all old messages
        ↓
Connect WebSocket for real-time:
    connectWebSocket(id, handlers...)
        ├─ WebSocket('ws://host/ws/conversations/{id}/')
        ├─ chatSocket.onopen → enableMessageInput()
        ├─ chatSocket.onmessage → handleWebSocketMessage()
        └─ chatSocket.onclose → fallback to REST
        ↓
✅ Conversation open and ready!
```

---

## 5️⃣ WebSocket Connection Lifecycle

```
connectWebSocket() called
        ↓
Create: new WebSocket('ws://...')
        ↓
Connection attempts to server
        ├─ Success: onopen event
        │           ↓
        │           Enable message input
        │           Focus on input box
        │           User can send messages
        │
        └─ Failure/Network issues
                ↓
                onerror event
                ↓
                Update subtitle: "Realtime unavailable"
                ↓
                App falls back to REST API
        ↓
Server sends messages in real-time
        ↓
onmessage event → handleWebSocketMessage()
        ↓
User clicks another conversation
        ↓
closeWebSocket() called
        ↓
chatSocket.close()
        ↓
onclose event
        ↓
Connection cleaned up
        ↓
New WebSocket created for new conversation
```

---

## 6️⃣ Delete Conversation Flow

```
User clicks "×" delete button on conversation
        ↓
handleDeleteConversation(id) called
        ↓
Show confirmation: "Delete this conversation?"
        ├─ User clicks NO → Return (do nothing)
        └─ User clicks YES → Continue
        ↓
Call API: DELETE /api/conversations/{id}/
        ↓
If this was active conversation:
    ├─ activeConversationId = null
    ├─ closeWebSocket()
    └─ resetChatUI() - Back to "Select a person"
        ↓
Reload conversation list:
    loadAndRenderConversations()
        ↓
✅ Conversation deleted!
```

---

## 7️⃣ Start Conversation with New Person Flow

```
User clicks on person name in "People" list
        ↓
Click event → handleSelectPerson(userId, username, picture)
        ↓
Create conversation via API:
    startConversation(recipientId)
    ├─ POST /api/conversations/
    ├─ body: { recipient_id: userId }
    └─ Response: new conversation object
        ↓
Reload conversation list:
    loadAndRenderConversations()
        ↓
Open newly created conversation:
    selectConversation(conversation)
        ↓
(Follows "Open Conversation Flow" above)
        ↓
✅ Chat with new person started!
```

---

## 8️⃣ Error Handling Flow

```
API call fails
        ├─ Network error
        ├─ 404 Not Found
        ├─ 500 Server Error
        └─ Timeout
        ↓
Fetch fails → response.ok is false
        ↓
Throw Error in makeApiCall():
    throw new Error(errorData.detail)
        ↓
Calling function catches error:
    try { await api(...) }
    catch (error) { alert(...) }
        ↓
User sees error message
        ↓
App continues working (graceful degradation)
```

---

## 9️⃣ Notification Flow

```
Message received from WebSocket
        ↓
handleWebSocketMessage() called
        ↓
showMessageNotification(message) called
        ↓
Check conditions:
    ├─ Is Notification API available?
    ├─ Did user grant permission?
    └─ Is message from someone else?
        ↓
If all YES:
    ├─ new Notification("New Message")
    └─ Show desktop notification
        ↓
If NO:
    └─ Silently skip (no error)
```

---

## 🔟 Full User Session Example

```
1. User opens browser → Home page loads
   └─ Conversations displayed in sidebar
   └─ "Select a person" message shown

2. User clicks "John" in people list
   └─ Conversation with John opens
   └─ Previous messages loaded
   └─ WebSocket connected

3. John sends "Hi!"
   └─ handleWebSocketMessage() receives it
   └─ "Hi!" appears in chat
   └─ Notification shown
   └─ Conversation list updated

4. User types "Hey John!"
   └─ sendWebSocketMessage() sends it
   └─ Message appears instantly
   └─ Last message in sidebar updates

5. User clicks "×" to delete conversation
   └─ Asks for confirmation
   └─ Chat cleared
   └─ Sidebar updated

6. User closes browser
   └─ WebSocket closed
   └─ Session ends
   └─ ✅ Done!
```

---

## 🔐 CSRF Token Flow

```
Django requires CSRF protection for POST/DELETE requests
        ↓
Backend sends CSRF token in cookie
        ↓
getCsrfToken() reads from cookies
        ↓
Every API call includes:
    'X-CSRFToken': csrfToken()
        ↓
Backend verifies token matches
        ├─ Valid → Request processed
        └─ Invalid → 403 Forbidden error
        ↓
Protects against cross-site attacks
```

---

## 📊 Data Flow Summary

```
┌─────────────┐
│   Browser   │
│             │
│ home.html   │
│ style.css   │
│ api.js      │
│ websocket.js│
│ messenger.js│
└──────┬──────┘
       │
       ├─→ REST API (for data fetching)
       │   POST /api/conversations/
       │   GET  /api/conversations/{id}/messages/
       │   DELETE /api/conversations/{id}/
       │
       └─→ WebSocket (for real-time)
           ws://host/ws/conversations/{id}/
           
           Exchange:
           Browser ←→ Server
           Messages flow both ways!
           
└─────────────────────────────────────────┘
         Django Backend
       (models, views, consumers)
```

---

## 🎯 Key Takeaways

1. **Startup**: Load HTML → CSS → JS files → Initialize listeners
2. **User Action**: Click/Type → Event → Handler function → API/WebSocket call
3. **Response**: Data arrives → JavaScript processes → Update DOM → Show to user
4. **Errors**: Caught → User sees message → App continues
5. **Real-time**: WebSocket preferred → REST fallback → Success!

---

## 💻 Tracing an Action

To understand how something works, trace it:

**Example: "I want to know what happens when I send a message"**

1. Search in `messenger.js` for "send" → Find `handleMessageSubmit()`
2. Read that function → See it calls `sendWebSocketMessage()`
3. Go to `websocket.js` → Read `sendWebSocketMessage()`
4. See it sends JSON to server
5. Go back to `messenger.js` → Find `handleWebSocketMessage()`
6. See how it processes the response
7. See it calls `addMessageToUI()`
8. Read `addMessageToUI()` → Understand how message appears

**Total time: 5 minutes!** That's how readable this code is. 🎉
