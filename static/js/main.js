document.addEventListener('DOMContentLoaded', () => {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const messageList = document.getElementById('message-list');
    const debugLog = document.getElementById('debug-log');

    const addMessage = (sender, text) => {
        const messageEl = document.createElement('div');
        messageEl.classList.add('message', sender);
        // A simple markdown-to-html conversion
        text = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        messageEl.innerHTML = text;
        messageList.appendChild(messageEl);
        messageList.scrollTop = messageList.scrollHeight;
    };

    const setDebugLog = (logs) => {
        debugLog.innerHTML = '';
        if (Array.isArray(logs)) {
            logs.forEach(log => {
                const logEl = document.createElement('p');
                logEl.textContent = log;
                debugLog.appendChild(logEl);
            });
        } else if (typeof logs === 'string') {
             debugLog.textContent = logs;
        }
        debugLog.scrollTop = debugLog.scrollHeight;
    };

    const sendMessage = async () => {
        const messageText = messageInput.value.trim();
        if (messageText === '') return;

        addMessage('user', messageText);
        messageInput.value = '';
        sendButton.disabled = true;
        setDebugLog('🤔 Atlas 正在思考中...');

        try {
            const response = await fetch('/think', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: messageText }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            addMessage('atlas', data.answer);
            setDebugLog(data.logs);

        } catch (error) {
            addMessage('atlas', `抱歉, 发生了一个错误: ${error.message}`);
            setDebugLog(`请求失败: ${error.stack}`);
        } finally {
            sendButton.disabled = false;
            messageInput.focus();
        }
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
