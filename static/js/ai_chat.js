// AI Chat JavaScript
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

const API_BASE = '';

function getAuthHeaders() {
    let initData = '';
    
    if (tg.initData) {
        initData = tg.initData;
    } else if (tg.initDataUnsafe) {
        if (typeof tg.initDataUnsafe === 'string') {
            initData = tg.initDataUnsafe;
        } else if (tg.initDataUnsafe.query_id) {
            const params = new URLSearchParams();
            for (const key in tg.initDataUnsafe) {
                if (typeof tg.initDataUnsafe[key] === 'object') {
                    params.append(key, JSON.stringify(tg.initDataUnsafe[key]));
                } else {
                    params.append(key, tg.initDataUnsafe[key]);
                }
            }
            initData = params.toString();
        }
    }
    
    return {
        'Content-Type': 'application/json',
        'X-Telegram-Init-Data': initData
    };
}

async function apiRequest(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers: {
                ...getAuthHeaders(),
                ...options.headers
            }
        });

        // Response status tekshirish
        if (!response.ok) {
            // 401 yoki 403 - autentifikatsiya xatoligi
            if (response.status === 401 || response.status === 403) {
                console.error('Autentifikatsiya xatoligi:', response.status);

                // JSON'dan redirect URL'ni olishga harakat qilish
                try {
                    const errorData = await response.json();
                    if (errorData.redirect) {
                        // Redirect qilish
                        if (window.tg && window.tg.openLink) {
                            window.tg.openLink(errorData.redirect);
                        } else {
                            window.location.href = errorData.redirect;
                        }
                    }
                    return { success: false, error: errorData.error || 'Autentifikatsiya xatoligi', status: response.status };
                } catch (e) {
                    return { success: false, error: 'Autentifikatsiya xatoligi', status: response.status };
                }
            }

            // Boshqa xatoliklar
            try {
                const errorData = await response.json();
                return { success: false, error: errorData.error || `Server xatoligi: ${response.status}`, status: response.status };
            } catch (e) {
                return { success: false, error: `Server xatoligi: ${response.status}`, status: response.status };
            }
        }

        return await response.json();
    } catch (error) {
        console.error('API error:', error);
        return { success: false, error: error.message };
    }
}

function addMessage(text, isUser = false) {
    const container = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `flex items-start space-x-2 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`;
    
    if (isUser) {
        messageDiv.innerHTML = `
            <div class="flex-1 bg-blue-600 text-white rounded-lg p-3 shadow max-w-[80%]">
                <p class="text-sm">${text}</p>
            </div>
            <div class="bg-blue-100 p-3 rounded-full">
                <i class="fas fa-user text-blue-600"></i>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="bg-blue-100 p-3 rounded-full">
                <i class="fas fa-robot text-blue-600"></i>
            </div>
            <div class="flex-1 bg-white rounded-lg p-3 shadow max-w-[80%]">
                <p class="text-sm">${text}</p>
            </div>
        `;
    }
    
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message
    addMessage(message, true);
    input.value = '';
    
    // Show typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typingIndicator';
    typingDiv.className = 'flex items-start space-x-2';
    typingDiv.innerHTML = `
        <div class="bg-blue-100 p-3 rounded-full">
            <i class="fas fa-robot text-blue-600"></i>
        </div>
        <div class="flex-1 bg-white rounded-lg p-3 shadow">
            <p class="text-sm text-gray-500">Yozilmoqda...</p>
        </div>
    `;
    document.getElementById('chatMessages').appendChild(typingDiv);
    
    // Send to API
    const res = await apiRequest('/api/ai/chat', {
        method: 'POST',
        body: JSON.stringify({ message })
    });
    
    // Remove typing indicator
    typingDiv.remove();
    
    if (res.success) {
        addMessage(res.data.response);
    } else {
        addMessage('Xatolik yuz berdi: ' + res.error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    
    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});

