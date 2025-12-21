-- Database schema for Business Tarifi Mini App
-- Bot bilan bir xil database'da ishlaydi

-- Transactions jadvali (biznes uchun ham)
CREATE TABLE IF NOT EXISTS transactions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    transaction_type ENUM('income', 'expense', 'debt') NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'UZS',
    category VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);

-- Warehouse_products jadvali (OMBOR)
CREATE TABLE IF NOT EXISTS warehouse_products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    barcode VARCHAR(100),
    price DECIMAL(15,2) DEFAULT 0,
    quantity INT DEFAULT 0,
    min_quantity INT DEFAULT 0,
    unit VARCHAR(50) DEFAULT 'dona',
    image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_category (category)
);

-- Warehouse_movements jadvali (OMBOR HARAKATLARI)
CREATE TABLE IF NOT EXISTS warehouse_movements (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    product_id INT NOT NULL,
    movement_type ENUM('in', 'out') NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(15,2) DEFAULT 0,
    reason VARCHAR(100) DEFAULT 'other',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_product_id (product_id),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (product_id) REFERENCES warehouse_products(id) ON DELETE CASCADE
);

-- Business_employees jadvali (XODIMLAR)
CREATE TABLE IF NOT EXISTS business_employees (
    id INT PRIMARY KEY AUTO_INCREMENT,
    owner_id BIGINT NOT NULL,
    telegram_id BIGINT NOT NULL,
    name VARCHAR(255) NOT NULL,
    role ENUM('employee', 'manager') DEFAULT 'employee',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_owner_id (owner_id),
    INDEX idx_telegram_id (telegram_id)
);

-- Business_tasks jadvali (VAZIFALAR)
CREATE TABLE IF NOT EXISTS business_tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    owner_id BIGINT NOT NULL,
    employee_id INT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    due_date DATETIME,
    status ENUM('pending', 'in_progress', 'completed', 'cancelled') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    INDEX idx_owner_id (owner_id),
    INDEX idx_employee_id (employee_id),
    INDEX idx_status (status),
    FOREIGN KEY (employee_id) REFERENCES business_employees(id) ON DELETE SET NULL
);

-- Debts jadvali (BIZNES QARZLARI)
CREATE TABLE IF NOT EXISTS debts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    debt_type ENUM('lent', 'borrowed') NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    paid_amount DECIMAL(15,2) DEFAULT 0,
    person_name VARCHAR(255),
    due_date DATE NULL,
    status ENUM('active', 'paid') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
);

