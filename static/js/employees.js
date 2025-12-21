// Employees JavaScript
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

const API_BASE = '';

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

// Load employees
async function loadEmployees(forceRefresh = false) {
    const res = await apiRequest('/api/employees', {}, !forceRefresh);
    if (res.success) {
        displayEmployees(res.data);
        populateEmployeeSelect(res.data);
    }
}

function displayEmployees(employees) {
    const container = document.getElementById('employeesList');
    
    if (!employees || employees.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center py-8">Xodimlar yo\'q</p>';
        return;
    }
    
    container.innerHTML = employees.map(e => `
        <div class="bg-white rounded-lg shadow p-4">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <div class="bg-blue-100 p-3 rounded-full">
                        <i class="fas fa-user text-blue-600"></i>
                    </div>
                    <div>
                        <h3 class="font-semibold">${e.name}</h3>
                        <p class="text-sm text-gray-500">
                            ${e.role === 'manager' ? 'Menejer' : 'Xodim'} 
                            ${e.is_active ? '<span class="text-green-600">• Faol</span>' : '<span class="text-red-600">• Nofaol</span>'}
                        </p>
                    </div>
                </div>
                <div class="flex space-x-2">
                    <button onclick="editEmployee(${e.id})" class="bg-blue-100 text-blue-600 px-3 py-1 rounded text-sm">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button onclick="deleteEmployee(${e.id})" class="bg-red-100 text-red-600 px-3 py-1 rounded text-sm">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

// Load tasks
async function loadTasks(status = '', forceRefresh = false) {
    const endpoint = status ? `/api/tasks?status=${status}` : '/api/tasks';
    const res = await apiRequest(endpoint, {}, !forceRefresh);
    if (res.success) {
        displayTasks(res.data);
    }
}

function displayTasks(tasks) {
    const container = document.getElementById('tasksList');
    
    if (!tasks || tasks.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center py-8">Vazifalar yo\'q</p>';
        return;
    }
    
    const statusColors = {
        'pending': 'bg-yellow-100 text-yellow-800',
        'in_progress': 'bg-blue-100 text-blue-800',
        'completed': 'bg-green-100 text-green-800',
        'cancelled': 'bg-red-100 text-red-800'
    };
    
    const statusText = {
        'pending': 'Kutilmoqda',
        'in_progress': 'Jarayonda',
        'completed': 'Bajarilgan',
        'cancelled': 'Bekor qilingan'
    };
    
    container.innerHTML = tasks.map(t => `
        <div class="bg-white rounded-lg shadow p-4">
            <div class="flex items-start justify-between">
                <div class="flex-1">
                    <h3 class="font-semibold">${t.title}</h3>
                    <p class="text-sm text-gray-600 mt-1">${t.description || ''}</p>
                    <div class="mt-2 flex items-center space-x-3 text-xs text-gray-500">
                        ${t.employee_name ? `<span><i class="fas fa-user"></i> ${t.employee_name}</span>` : ''}
                        ${t.due_date ? `<span><i class="fas fa-calendar"></i> ${new Date(t.due_date).toLocaleDateString('uz-UZ')}</span>` : ''}
                    </div>
                </div>
                <div class="flex flex-col items-end space-y-2">
                    <span class="px-2 py-1 rounded text-xs ${statusColors[t.status] || 'bg-gray-100'}">
                        ${statusText[t.status] || t.status}
                    </span>
                    <button onclick="editTask(${t.id})" class="bg-blue-100 text-blue-600 px-2 py-1 rounded text-xs">
                        <i class="fas fa-edit"></i>
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

// Employee modal
function openEmployeeModal(employeeId = null) {
    const modal = document.getElementById('employeeModal');
    const form = document.getElementById('employeeForm');
    const title = document.getElementById('employeeModalTitle');
    
    if (employeeId) {
        title.textContent = 'Xodimni tahrirlash';
        loadEmployeeData(employeeId);
    } else {
        title.textContent = 'Yangi xodim';
        form.reset();
        document.getElementById('employeeId').value = '';
        document.getElementById('employeeIsActive').checked = true;
    }
    
    modal.classList.remove('hidden');
}

function loadEmployeeData(employeeId) {
    apiRequest('/api/employees').then(res => {
        if (res.success) {
            const employee = res.data.find(e => e.id === employeeId);
            if (employee) {
                document.getElementById('employeeId').value = employee.id;
                document.getElementById('employeeName').value = employee.name;
                document.getElementById('employeeTelegramId').value = employee.telegram_id;
                document.getElementById('employeeRole').value = employee.role;
                document.getElementById('employeeIsActive').checked = employee.is_active;
            }
        }
    });
}

async function saveEmployee(e) {
    e.preventDefault();
    
    const employeeId = document.getElementById('employeeId').value;
    const data = {
        name: document.getElementById('employeeName').value,
        telegram_id: parseInt(document.getElementById('employeeTelegramId').value),
        role: document.getElementById('employeeRole').value,
        is_active: document.getElementById('employeeIsActive').checked
    };
    
    const endpoint = employeeId ? `/api/employees/${employeeId}` : '/api/employees';
    const method = employeeId ? 'PUT' : 'POST';
    
    const res = await apiRequest(endpoint, {
        method: method,
        body: JSON.stringify(data)
    });
    
    if (res.success) {
        document.getElementById('employeeModal').classList.add('hidden');
        dataCache.clear('/api/employees');
        loadEmployees(true); // Force refresh
        tg.showAlert('Xodim saqlandi!');
    } else {
        tg.showAlert('Xatolik: ' + res.error);
    }
}

function editEmployee(id) {
    openEmployeeModal(id);
}

async function deleteEmployee(id) {
    if (confirm('Xodimni o\'chirishni tasdiqlaysizmi?')) {
        const res = await apiRequest(`/api/employees/${id}`, { method: 'DELETE' }, false);
        if (res.success) {
            dataCache.clear('/api/employees');
            loadEmployees(true); // Force refresh
            tg.showAlert('Xodim o\'chirildi!');
        } else {
            tg.showAlert('Xatolik: ' + res.error);
        }
    }
}

// Task modal
function openTaskModal(taskId = null) {
    const modal = document.getElementById('taskModal');
    const form = document.getElementById('taskForm');
    const title = document.getElementById('taskModalTitle');
    
    if (taskId) {
        title.textContent = 'Vazifani tahrirlash';
        loadTaskData(taskId);
    } else {
        title.textContent = 'Yangi vazifa';
        form.reset();
        document.getElementById('taskId').value = '';
        document.getElementById('taskStatus').value = 'pending';
    }
    
    modal.classList.remove('hidden');
}

function loadTaskData(taskId) {
    apiRequest('/api/tasks').then(res => {
        if (res.success) {
            const task = res.data.find(t => t.id === taskId);
            if (task) {
                document.getElementById('taskId').value = task.id;
                document.getElementById('taskTitle').value = task.title;
                document.getElementById('taskDescription').value = task.description || '';
                document.getElementById('taskEmployeeId').value = task.employee_id || '';
                document.getElementById('taskStatus').value = task.status;
                
                if (task.due_date) {
                    const date = new Date(task.due_date);
                    document.getElementById('taskDueDate').value = date.toISOString().slice(0, 16);
                }
            }
        }
    });
}

async function saveTask(e) {
    e.preventDefault();
    
    const taskId = document.getElementById('taskId').value;
    const data = {
        title: document.getElementById('taskTitle').value,
        description: document.getElementById('taskDescription').value,
        employee_id: document.getElementById('taskEmployeeId').value || null,
        due_date: document.getElementById('taskDueDate').value || null,
        status: document.getElementById('taskStatus').value
    };
    
    const endpoint = taskId ? `/api/tasks/${taskId}` : '/api/tasks';
    const method = taskId ? 'PUT' : 'POST';
    
    const res = await apiRequest(endpoint, {
        method: method,
        body: JSON.stringify(data)
    });
    
    if (res.success) {
        document.getElementById('taskModal').classList.add('hidden');
        dataCache.clearPattern('/api/tasks');
        loadTasks('', true); // Force refresh
        tg.showAlert('Vazifa saqlandi!');
    } else {
        tg.showAlert('Xatolik: ' + res.error);
    }
}

function editTask(id) {
    openTaskModal(id);
}

function populateEmployeeSelect(employees) {
    const select = document.getElementById('taskEmployeeId');
    select.innerHTML = '<option value="">Xodim tanlash</option>';
    employees.filter(e => e.is_active).forEach(e => {
        const option = document.createElement('option');
        option.value = e.id;
        option.textContent = e.name;
        select.appendChild(option);
    });
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    loadEmployees(false); // Cache'dan olish
    loadTasks('', false); // Cache'dan olish
    
    // Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            document.querySelectorAll('.tab-btn').forEach(b => {
                b.classList.remove('active', 'border-blue-600', 'text-blue-600');
                b.classList.add('border-transparent', 'text-gray-500');
            });
            btn.classList.add('active', 'border-blue-600', 'text-blue-600');
            btn.classList.remove('border-transparent', 'text-gray-500');
            
            document.getElementById('employeesTab').classList.toggle('hidden', tab !== 'employees');
            document.getElementById('tasksTab').classList.toggle('hidden', tab !== 'tasks');
        });
    });
    
    // Employee modal
    document.getElementById('addEmployeeBtn').addEventListener('click', () => openEmployeeModal());
    document.getElementById('employeeForm').addEventListener('submit', saveEmployee);
    document.getElementById('closeEmployeeModal').addEventListener('click', () => {
        document.getElementById('employeeModal').classList.add('hidden');
    });
    document.getElementById('cancelEmployeeBtn').addEventListener('click', () => {
        document.getElementById('employeeModal').classList.add('hidden');
    });
    
    // Task modal
    document.getElementById('addTaskBtn')?.addEventListener('click', () => openTaskModal());
    document.getElementById('taskForm').addEventListener('submit', saveTask);
    document.getElementById('closeTaskModal').addEventListener('click', () => {
        document.getElementById('taskModal').classList.add('hidden');
    });
    document.getElementById('cancelTaskBtn').addEventListener('click', () => {
        document.getElementById('taskModal').classList.add('hidden');
    });
    
    // Status filter
    document.querySelectorAll('.status-filter').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.status-filter').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            loadTasks(btn.dataset.status, false); // Cache'dan olish
        });
    });
});

// Make functions global
window.editEmployee = editEmployee;
window.deleteEmployee = deleteEmployee;
window.editTask = editTask;

