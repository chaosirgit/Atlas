document.addEventListener('DOMContentLoaded', () => {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const messageList = document.getElementById('message-list');
    const debugLog = document.getElementById('debug-log');

    // Configure marked.js
    marked.setOptions({
        gfm: true,
        breaks: true,
        sanitizer: (html) => {
            // A simple sanitizer. For production, consider a more robust library like DOMPurify.
            const clean = html.replace(/<script[^>]*>([\S\s]*?)<\/script>/gmi, '');
            return clean;
        }
    });

    const addMessage = (sender, text, elementId = null) => {
        let messageEl;
        if (elementId && document.getElementById(elementId)) {
            messageEl = document.getElementById(elementId);
        } else {
            messageEl = document.createElement('div');
            messageEl.classList.add('message', sender);
            if (elementId) {
                messageEl.id = elementId;
            }
            messageList.appendChild(messageEl);
        }

        // Use marked to parse markdown content
        messageEl.innerHTML = marked.parse(text);
        messageList.scrollTop = messageList.scrollHeight;
        return messageEl;
    };
    
    const appendToDebugLog = (log) => {
        const logEl = document.createElement('p');
        logEl.textContent = log;
        debugLog.appendChild(logEl);
        debugLog.scrollTop = debugLog.scrollHeight;
    };

    const clearDebugLog = () => {
        debugLog.innerHTML = '';
    }

    const sendMessage = () => {
        const messageText = messageInput.value.trim();
        if (messageText === '') return;

        addMessage('user', messageText);
        messageInput.value = '';
        sendButton.disabled = true;
        
        clearDebugLog();
        const thinkingMessage = addMessage('atlas', '🤔', 'current-atlas-message');

        const es = new EventSource(`/chat-stream?message=${encodeURIComponent(messageText)}`);

        es.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            switch(data.type) {
                case 'log':
                    appendToDebugLog(data.data);
                    break;
                case 'final_answer':
                    addMessage('atlas', data.data, 'current-atlas-message');
                    thinkingMessage.removeAttribute('id'); 
                    es.close(); // Close the connection
                    sendButton.disabled = false; // Re-enable button
                    messageInput.focus();
                    break;
                case 'error':
                    addMessage('atlas', `抱歉, 发生了一个错误: ${data.data}`, 'current-atlas-message');
                    thinkingMessage.removeAttribute('id');
                    es.close();
                    sendButton.disabled = false;
                    break;
            }
        };

        es.onerror = function(err) {
            console.error('EventSource failed:', err);
            addMessage('atlas', '抱歉, 与服务器的连接中断了。', 'current-atlas-message');
            thinkingMessage.removeAttribute('id');
            es.close();
            sendButton.disabled = false;
        };
    };

    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    addMessage('atlas', '你好, 我是 Atlas. 你可以问我任何问题.');
});