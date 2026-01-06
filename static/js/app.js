// Asosiy JavaScript - Telegram Mini App
const tg = window.Telegram.WebApp;

// Telegram WebApp'ni ishga tushirish
tg.ready();
tg.expand();

// API base URL
const API_BASE = '';

// Global cache'dan foydalanish
const dataCache = window.dataCache || {
    get: () => null,
    set: () => {},
    clear: () => {}
};

// Telegram initData'ni header'ga qo'shish
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

// Global qilish (index.html'da ishlatish uchun)
window.getAuthHeaders = getAuthHeaders;

// API request funksiyasi
async function apiRequest(endpoint, options = {}, useCache = true) {
    // Cache tekshirish
    if (useCache) {
        const cached = dataCache.get(endpoint);
        if (cached) {
            return cached;
        }
    }

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

        const data = await response.json();

        // Cache'ga saqlash
        if (useCache && data.success) {
            dataCache.set(endpoint, data);
        }

        return data;
    } catch (error) {
        console.error('API request error:', error);
        return { success: false, error: error.message };
    }
}

// Format number to UZS
function formatCurrency(amount) {
    return new Intl.NumberFormat('uz-UZ', {
        style: 'currency',
        currency: 'UZS',
        minimumFractionDigits: 0
    }).format(amount || 0);
}

// Format date
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('uz-UZ', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Format relative time
function formatRelativeTime(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (minutes < 1) return 'Hozir';
    if (minutes < 60) return `${minutes} daqiqa oldin`;
    if (hours < 24) return `${hours} soat oldin`;
    if (days < 7) return `${days} kun oldin`;
    return formatDate(dateString);
}

// Loading overlay'ni yashirish (removed - no longer needed)
function hideLoading() {
    // Loading overlay removed
}

// Loading overlay'ni ko'rsatish (removed - no longer needed)
function showLoading() {
    // Loading overlay removed
}

// Load dashboard data
async function loadDashboard(showLoadingOverlay = false, forceRefresh = false) {
    // Cache'dan tekshirish - agar barcha ma'lumotlar cache'da bo'lsa, loading ko'rsatmaslik
    const summaryCached = dataCache.get('/api/reports/summary?period=month');
    const transactionsCached = dataCache.get('/api/transactions?limit=5');
    
    if (!forceRefresh && summaryCached && transactionsCached && !showLoadingOverlay) {
        // Barcha ma'lumotlar cache'da - faqat ko'rsatish, yuklash yo'q
        updateDashboardDisplay(summaryCached, transactionsCached);
        return;
    }

    try {
        // Parallel requests (cache'dan olish, agar forceRefresh bo'lmasa)
        const [summaryRes, transactionsRes, statsRes] = await Promise.all([
            apiRequest('/api/reports/summary?period=month', {}, !forceRefresh),
            apiRequest('/api/transactions?limit=5', {}, !forceRefresh),
            loadQuickStats(!forceRefresh)
        ]);

        // Update dashboard display
        updateDashboardDisplay(summaryRes, transactionsRes);

        // Update last update time
        const lastUpdateEl = document.getElementById('lastUpdate');
        if (lastUpdateEl) {
            lastUpdateEl.textContent = `Yangilandi: ${new Date().toLocaleTimeString('uz-UZ')}`;
        }

        // Update cache timestamp
        dataCache.lastUpdate = Date.now();

    } catch (error) {
        console.error('Dashboard load error:', error);
        tg.showAlert('Ma\'lumotlarni yuklashda xatolik yuz berdi');
    }
}

// Update dashboard display (cache'dan yoki API'dan kelgan ma'lumotlar bilan)
function updateDashboardDisplay(summaryRes, transactionsRes) {
    // Update summary
    if (summaryRes && summaryRes.success && summaryRes.data && summaryRes.data.summary) {
        const summary = summaryRes.data.summary;
        const income = summary.total_income || 0;
        const expense = summary.total_expense || 0;
        const balance = income - expense;

        const incomeEl = document.getElementById('totalIncome');
        const expenseEl = document.getElementById('totalExpense');
        const balanceEl = document.getElementById('totalBalance');
        
        if (incomeEl) incomeEl.textContent = formatCurrency(income);
        if (expenseEl) expenseEl.textContent = formatCurrency(expense);
        if (balanceEl) {
            balanceEl.textContent = formatCurrency(balance);
            balanceEl.className = balance >= 0 
                ? 'text-3xl font-bold text-green-200' 
                : 'text-3xl font-bold text-red-200';
        }
    }

    // Update transactions
    if (transactionsRes && transactionsRes.success && transactionsRes.data) {
        displayRecentActivity(transactionsRes.data);
    }
}

// Load quick stats
async function loadQuickStats(useCache = true) {
    try {
        const [productsRes, employeesRes, tasksRes] = await Promise.all([
            apiRequest('/api/warehouse/products', {}, useCache),
            apiRequest('/api/employees', {}, useCache),
            apiRequest('/api/tasks', {}, useCache)
        ]);

        if (productsRes.success) {
            document.getElementById('totalProducts').textContent = productsRes.data?.length || 0;
        }
        if (employeesRes.success) {
            document.getElementById('totalEmployees').textContent = employeesRes.data?.length || 0;
        }
        if (tasksRes.success) {
            const activeTasks = tasksRes.data?.filter(t => t.status !== 'completed' && t.status !== 'cancelled').length || 0;
            document.getElementById('totalTasks').textContent = activeTasks;
        }
    } catch (error) {
        console.error('Quick stats load error:', error);
    }
}

// Display recent activity
function displayRecentActivity(transactions) {
    const container = document.getElementById('recentActivity');
    
    if (!transactions || transactions.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8">
                <i class="fas fa-inbox text-gray-300 text-4xl mb-3"></i>
                <p class="text-gray-500">Hech qanday faoliyat yo'q</p>
            </div>
        `;
        return;
    }

    container.innerHTML = transactions.map(t => {
        const icon = t.transaction_type === 'income' 
            ? '<i class="fas fa-arrow-down text-green-600"></i>'
            : '<i class="fas fa-arrow-up text-red-600"></i>';
        const bgColor = t.transaction_type === 'income' 
            ? 'bg-green-50 border-green-200' 
            : 'bg-red-50 border-red-200';
        
        return `
            <div class="flex items-center justify-between p-3 rounded-lg border ${bgColor} hover:shadow-md transition">
                <div class="flex items-center space-x-3 flex-1">
                    <div class="bg-white p-2 rounded-lg shadow-sm">
                        ${icon}
                    </div>
                    <div class="flex-1 min-w-0">
                        <p class="font-semibold text-gray-800 truncate">${t.description || t.category || 'Tranzaksiya'}</p>
                        <p class="text-xs text-gray-500">${formatRelativeTime(t.created_at)}</p>
                    </div>
                </div>
                <p class="font-bold ${t.transaction_type === 'income' ? 'text-green-700' : 'text-red-700'} ml-3">
                    ${t.transaction_type === 'income' ? '+' : '-'}${formatCurrency(t.amount)}
                </p>
            </div>
        `;
    }).join('');
}

// Refresh button
document.getElementById('refreshBtn')?.addEventListener('click', () => {
    // Clear all cache
    dataCache.clear();
    
    // Reload with loading (force refresh)
    loadDashboard(true, true);
    
    // Button animation
    const btn = document.getElementById('refreshBtn');
    btn.classList.add('loading-spinner');
    setTimeout(() => {
        btn.classList.remove('loading-spinner');
    }, 1000);
});

// View all button
document.getElementById('viewAllBtn')?.addEventListener('click', () => {
    // Navigate to transactions page or show all
    tg.showAlert('Barcha tranzaksiyalar sahifasi keyinchalik qo\'shiladi');
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Avtomatik yuklash (loading overlay bilan)
    loadDashboard(true);
    
    // Auto refresh har 60 soniyada
    setInterval(() => {
        loadDashboard(false);
    }, 60000);
});

// Page visibility API - sahifa ko'rinadigan bo'lganda yangilash
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        // Cache eskirgan bo'lsa, yangilash
        const summaryCache = dataCache.get('/api/reports/summary?period=month');
        if (!summaryCache) {
            loadDashboard(false, false);
        }
    }
});
