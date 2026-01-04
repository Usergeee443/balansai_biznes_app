// Warehouse JavaScript
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

function formatCurrency(amount) {
    return new Intl.NumberFormat('uz-UZ', {
        style: 'currency',
        currency: 'UZS',
        minimumFractionDigits: 0
    }).format(amount || 0);
}

// Store all products globally for search
let allProducts = [];

// Load products
async function loadProducts(showLoading = true, forceRefresh = false) {
    // Cache'dan tekshirish - agar cache'da bo'lsa va loading ko'rsatmaslik kerak bo'lsa
    if (!forceRefresh) {
        const cached = dataCache.get('/api/warehouse/products');
        if (cached && cached.success) {
            allProducts = cached.data;
            displayProducts(cached.data);
            const loadingState = document.getElementById('loadingState');
            const productsList = document.getElementById('productsList');
            if (loadingState) loadingState.classList.add('hidden');
            if (productsList) productsList.classList.remove('hidden');
            return; // Cache'dan olindi, yuklash yo'q
        }
    }

    // Show loading (faqat agar cache bo'sh bo'lsa yoki force refresh bo'lsa)
    if (showLoading) {
        const loadingState = document.getElementById('loadingState');
        const productsList = document.getElementById('productsList');
        if (loadingState) loadingState.classList.remove('hidden');
        if (productsList) productsList.classList.add('hidden');
    }

    const res = await apiRequest('/api/warehouse/products', {}, true);
    if (res.success) {
        allProducts = res.data;
        displayProducts(res.data);
        const loadingState = document.getElementById('loadingState');
        const productsList = document.getElementById('productsList');
        if (loadingState) loadingState.classList.add('hidden');
        if (productsList) productsList.classList.remove('hidden');
    } else {
        const loadingState = document.getElementById('loadingState');
        if (loadingState) {
            loadingState.innerHTML =
                '<div class="text-center py-8"><i class="fas fa-exclamation-triangle text-red-500 text-3xl mb-3"></i><p class="text-red-500">Xatolik: ' + res.error + '</p></div>';
        }
    }
}

// Search products
function searchProducts(query) {
    if (!query || query.trim() === '') {
        displayProducts(allProducts);
        return;
    }

    const searchTerm = query.toLowerCase().trim();
    const filtered = allProducts.filter(product => {
        return (
            (product.name && product.name.toLowerCase().includes(searchTerm)) ||
            (product.category && product.category.toLowerCase().includes(searchTerm)) ||
            (product.barcode && product.barcode.toLowerCase().includes(searchTerm))
        );
    });

    displayProducts(filtered);
}

// Display products
function displayProducts(products) {
    const container = document.getElementById('productsList');
    
    if (!products || products.length === 0) {
        container.innerHTML = `
            <div class="text-center py-12">
                <i class="fas fa-box-open text-gray-300 text-5xl mb-4"></i>
                <p class="text-gray-500 text-lg mb-2">Mahsulotlar yo'q</p>
                <p class="text-gray-400 text-sm">Yangi mahsulot qo'shish uchun "Qo'shish" tugmasini bosing</p>
            </div>
        `;
        return;
    }

    container.innerHTML = products.map(p => {
        const isLowStock = p.quantity <= p.min_quantity;
        const stockBg = isLowStock ? 'bg-red-50 border-red-200' : 'bg-white border-gray-100';
        
        return `
            <div class="${stockBg} rounded-xl shadow-md p-4 border hover:shadow-lg transition-all">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <div class="flex items-center space-x-2 mb-2">
                            <h3 class="font-bold text-lg text-gray-800">${p.name}</h3>
                            ${isLowStock ? '<span class="bg-red-100 text-red-600 text-xs px-2 py-1 rounded-full"><i class="fas fa-exclamation-triangle"></i> Kam</span>' : ''}
                        </div>
                        <p class="text-sm text-gray-500 mb-3">${p.category || 'Kategoriya yo\'q'}</p>
                        <div class="grid grid-cols-2 gap-3 mb-2">
                            <div class="bg-gray-50 rounded-lg p-2">
                                <p class="text-xs text-gray-500">Miqdor</p>
                                <p class="font-semibold text-gray-800">${p.quantity} ${p.unit}</p>
                            </div>
                            <div class="bg-gray-50 rounded-lg p-2">
                                <p class="text-xs text-gray-500">Narx</p>
                                <p class="font-semibold text-gray-800">${formatCurrency(p.price)}</p>
                            </div>
                        </div>
                        ${p.barcode ? `<p class="text-xs text-gray-400"><i class="fas fa-barcode"></i> ${p.barcode}</p>` : ''}
                    </div>
                    <div class="flex flex-col space-y-2 ml-3">
                        <button onclick="editProduct(${p.id})" class="bg-blue-100 hover:bg-blue-200 text-blue-600 px-3 py-2 rounded-lg text-sm transition">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="addMovement(${p.id})" class="bg-green-100 hover:bg-green-200 text-green-600 px-3 py-2 rounded-lg text-sm transition">
                            <i class="fas fa-exchange-alt"></i>
                        </button>
                        <button onclick="deleteProduct(${p.id})" class="bg-red-100 hover:bg-red-200 text-red-600 px-3 py-2 rounded-lg text-sm transition">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Add/Edit Product
function openProductModal(productId = null) {
    const modal = document.getElementById('productModal');
    const form = document.getElementById('productForm');
    const title = document.getElementById('modalTitle');
    
    if (productId) {
        title.textContent = 'Mahsulotni tahrirlash';
        loadProductData(productId);
    } else {
        title.textContent = 'Yangi mahsulot';
        form.reset();
        document.getElementById('productId').value = '';
    }
    
    modal.classList.remove('hidden');
}

function loadProductData(productId) {
    apiRequest(`/api/warehouse/products`).then(res => {
        if (res.success) {
            const product = res.data.find(p => p.id === productId);
            if (product) {
                document.getElementById('productId').value = product.id;
                document.getElementById('productName').value = product.name;
                document.getElementById('productCategory').value = product.category || '';
                document.getElementById('productPrice').value = product.price || 0;
                document.getElementById('productQuantity').value = product.quantity || 0;
                document.getElementById('productMinQuantity').value = product.min_quantity || 0;
                document.getElementById('productUnit').value = product.unit || 'dona';
                document.getElementById('productBarcode').value = product.barcode || '';
                document.getElementById('productImageUrl').value = product.image_url || '';
            }
        }
    });
}

async function saveProduct(e) {
    e.preventDefault();
    
    const productId = document.getElementById('productId').value;
    const data = {
        name: document.getElementById('productName').value,
        category: document.getElementById('productCategory').value,
        price: parseFloat(document.getElementById('productPrice').value) || 0,
        quantity: parseInt(document.getElementById('productQuantity').value) || 0,
        min_quantity: parseInt(document.getElementById('productMinQuantity').value) || 0,
        unit: document.getElementById('productUnit').value,
        barcode: document.getElementById('productBarcode').value,
        image_url: document.getElementById('productImageUrl').value
    };
    
    const endpoint = productId ? 
        `/api/warehouse/products/${productId}` : 
        '/api/warehouse/products';
    const method = productId ? 'PUT' : 'POST';
    
    const res = await apiRequest(endpoint, {
        method: method,
        body: JSON.stringify(data)
    });
    
    if (res.success) {
        document.getElementById('productModal').classList.add('hidden');
        dataCache.clear('/api/warehouse/products'); // Clear cache
        loadProducts(true, true); // Force refresh
        tg.showAlert('Mahsulot saqlandi!');
    } else {
        tg.showAlert('Xatolik: ' + res.error);
    }
}

function editProduct(id) {
    openProductModal(id);
}

async function deleteProduct(id) {
    if (confirm('Mahsulotni o\'chirishni tasdiqlaysizmi?')) {
        const res = await apiRequest(`/api/warehouse/products/${id}`, { method: 'DELETE' }, false);
        if (res.success) {
            dataCache.clear('/api/warehouse/products'); // Clear cache
            loadProducts(true, true); // Force refresh
            tg.showAlert('Mahsulot o\'chirildi!');
        } else {
            tg.showAlert('Xatolik: ' + res.error);
        }
    }
}

// Movement functions
function addMovement(productId) {
    document.getElementById('movementProductId').value = productId;
    document.getElementById('movementModal').classList.remove('hidden');
}

async function saveMovement(e) {
    e.preventDefault();
    
    const data = {
        product_id: parseInt(document.getElementById('movementProductId').value),
        movement_type: document.getElementById('movementType').value,
        quantity: parseInt(document.getElementById('movementQuantity').value),
        price: parseFloat(document.getElementById('movementPrice').value) || 0,
        reason: document.getElementById('movementReason').value
    };
    
    const res = await apiRequest('/api/warehouse/movements', {
        method: 'POST',
        body: JSON.stringify(data)
    });
    
    if (res.success) {
        document.getElementById('movementModal').classList.add('hidden');
        document.getElementById('movementForm').reset();
        dataCache.clear('/api/warehouse/products'); // Clear cache
        loadProducts(true, true); // Force refresh
        tg.showAlert('Harakat saqlandi!');
    } else {
        tg.showAlert('Xatolik: ' + res.error);
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
    
    document.getElementById('addProductBtn').addEventListener('click', () => openProductModal());
    document.getElementById('productForm').addEventListener('submit', saveProduct);
    document.getElementById('closeModal').addEventListener('click', () => {
        document.getElementById('productModal').classList.add('hidden');
    });
    document.getElementById('cancelBtn').addEventListener('click', () => {
        document.getElementById('productModal').classList.add('hidden');
    });
    
    document.getElementById('movementForm').addEventListener('submit', saveMovement);
    document.getElementById('closeMovementModal').addEventListener('click', () => {
        document.getElementById('movementModal').classList.add('hidden');
    });
    document.getElementById('cancelMovementBtn').addEventListener('click', () => {
        document.getElementById('movementModal').classList.add('hidden');
    });
    
    // Search
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            searchProducts(e.target.value);
        });
    }
});

// Make functions global
window.editProduct = editProduct;
window.deleteProduct = deleteProduct;
window.addMovement = addMovement;

