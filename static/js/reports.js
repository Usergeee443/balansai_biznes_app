// Reports JavaScript
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

const API_BASE = '';
let categoriesChart = null;

// Global cache'dan foydalanish
const dataCache = window.dataCache || {
    get: () => null,
    set: () => {},
    clear: () => {}
};

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
        const data = await response.json();
        
        // Cache'ga saqlash
        if (useCache && data.success) {
            dataCache.set(endpoint, data);
        }
        
        return data;
    } catch (error) {
        console.error('API error:', error);
        return { success: false, error: error.message };
    }
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('uz-UZ', {
        style: 'currency',
        currency: 'UZS',
        minimumFractionDigits: 0
    }).format(amount || 0);
}

// Load reports
async function loadReports(period = 'month', forceRefresh = false) {
    const endpoint = `/api/reports/summary?period=${period}`;
    const res = await apiRequest(endpoint, {}, !forceRefresh);
    
    if (res.success && res.data) {
        const { summary, top_categories, warehouse_stats } = res.data;
        
        // Update summary
        if (summary) {
            const incomeEl = document.getElementById('reportTotalIncome') || document.getElementById('totalIncome');
            const expenseEl = document.getElementById('reportTotalExpense') || document.getElementById('totalExpense');

            if (incomeEl) incomeEl.textContent = formatCurrency(summary.total_income || 0);
            if (expenseEl) expenseEl.textContent = formatCurrency(summary.total_expense || 0);

            const profit = (summary.total_income || 0) - (summary.total_expense || 0);
            const profitEl = document.getElementById('profit');
            if (profitEl) {
                profitEl.textContent = formatCurrency(profit);
                profitEl.className = profit >= 0 ? 'text-2xl font-bold text-tg-green' : 'text-2xl font-bold text-tg-red';
            }
        }

        // Update warehouse stats
        if (warehouse_stats) {
            const productsEl = document.getElementById('reportTotalProducts') || document.getElementById('totalProducts');
            const valueEl = document.getElementById('warehouseValue');
            const lowStockEl = document.getElementById('lowStock');

            if (productsEl) productsEl.textContent = warehouse_stats.total_products || 0;
            if (valueEl) valueEl.textContent = formatCurrency(warehouse_stats.total_value || 0);
            if (lowStockEl) lowStockEl.textContent = warehouse_stats.low_stock_count || 0;
        }
        
        // Update chart
        if (top_categories && top_categories.length > 0) {
            updateChart(top_categories);
        } else {
            updateChart([]);
        }
    }
}

// Update chart
function updateChart(categories) {
    const ctx = document.getElementById('categoriesChart').getContext('2d');
    
    if (categoriesChart) {
        categoriesChart.destroy();
    }
    
    if (categories.length === 0) {
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        ctx.fillText('Ma\'lumotlar yo\'q', ctx.canvas.width / 2, ctx.canvas.height / 2);
        return;
    }
    
    categoriesChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: categories.map(c => c.category || 'Noma\'lum'),
            datasets: [{
                data: categories.map(c => parseFloat(c.total) || 0),
                backgroundColor: [
                    '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Period buttons
document.addEventListener('DOMContentLoaded', () => {
    loadReports('month', false);
    
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const period = btn.dataset.period;
            loadReports(period, false); // Cache'dan olish
        });
    });
});

