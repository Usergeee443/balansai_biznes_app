"""
Flask server - Biznes tarifi Mini App backend
"""
from flask import Flask, render_template, request, jsonify, session, make_response
from flask_cors import CORS
import os
from dotenv import load_dotenv
from database import get_db_connection, execute_query
from telegram_auth import validate_telegram_init_data

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
CORS(app)

BOT_TOKEN = os.getenv('BOT_TOKEN', '')
BUSINESS_PLAN_REDIRECT_URL = os.getenv('BUSINESS_PLAN_REDIRECT_URL', 'https://balansai-app.onrender.com')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Test user yaratish funksiyasi (development uchun)
def ensure_test_user_exists(user_id):
    """Test user_id'ni users jadvaliga qo'shadi (agar mavjud bo'lmasa)"""
    if not app.debug:
        return
    
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # User mavjudligini tekshirish
            cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
            if cursor.fetchone():
                connection.close()
                return
            
            # User yaratish
            try:
                cursor.execute(
                    """INSERT INTO users (user_id, username, first_name, created_at) 
                       VALUES (%s, %s, %s, NOW()) 
                       ON DUPLICATE KEY UPDATE username = username""",
                    (user_id, 'test_user', 'Test User')
                )
                connection.commit()
            except Exception as e:
                # Agar users jadvali mavjud bo'lmasa yoki boshqa xatolik bo'lsa, ignore qilish
                print(f"Test user yaratishda xatolik (ehtimol users jadvali mavjud emas): {e}")
                connection.rollback()
        connection.close()
    except Exception as e:
        # Database xatoliklarini ignore qilish (development uchun)
        print(f"Test user tekshirishda xatolik: {e}")

# User business plan tekshirish
def check_business_plan(user_id):
    """User'ning business plan'i borligini tekshirish"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT subscription_type FROM users WHERE user_id = %s",
                (user_id,)
            )
            result = cursor.fetchone()
        connection.close()

        if result:
            return result.get('subscription_type') == 'business'
        return False
    except Exception as e:
        print(f"Business plan tekshirishda xatolik: {e}")
        # Development mode'da hamma user'ga ruxsat berish
        return DEBUG

# Middleware: Telegram auth tekshirish
@app.before_request
def check_telegram_auth():
    """Har bir request'da Telegram auth'ni tekshirish"""
    # Static fayllar va HTML sahifalar uchun auth talab qilinmaydi
    if (request.path.startswith('/static') or
        request.path == '/' or
        request.path == '/api/check-plan' or
        request.path in ['/warehouse', '/reports', '/employees', '/ai-chat']):
        return None

    # Faqat API endpoint'lar uchun auth talab qilinadi
    if not request.path.startswith('/api/'):
        return None

    init_data = request.headers.get('X-Telegram-Init-Data') or request.args.get('initData')

    # Development mode: Agar initData bo'lmasa, test user_id bilan ishlash
    if not init_data:
        # Development uchun test user_id (production'da o'chirilishi kerak)
        if DEBUG or app.debug:
            test_user_id = 123456789
            ensure_test_user_exists(test_user_id)
            session['user_id'] = test_user_id
            session['username'] = 'test_user'
            session['has_business_plan'] = True  # Development'da hamma ruxsat
            return None
        return jsonify({'error': 'Telegram auth talab qilinadi'}), 401

    try:
        user_data = validate_telegram_init_data(init_data, BOT_TOKEN)
        user_id = user_data.get('user_id')
        session['user_id'] = user_id
        session['username'] = user_data.get('username')

        # Business plan tekshirish
        has_business_plan = check_business_plan(user_id)
        session['has_business_plan'] = has_business_plan

        # Agar business plan bo'lmasa, faqat check-plan endpoint'ga ruxsat
        if not has_business_plan and request.path != '/api/check-plan':
            return jsonify({
                'error': 'Business plan talab qilinadi',
                'redirect': BUSINESS_PLAN_REDIRECT_URL
            }), 403

    except ValueError as e:
        # Development mode: Agar validatsiya muvaffaqiyatsiz bo'lsa, test user_id bilan ishlash
        if DEBUG or app.debug:
            test_user_id = 123456789
            ensure_test_user_exists(test_user_id)
            session['user_id'] = test_user_id
            session['username'] = 'test_user'
            session['has_business_plan'] = True
            return None
        return jsonify({'error': str(e)}), 401

# ==================== ROUTES ====================

@app.route('/api/check-plan', methods=['GET'])
def check_plan():
    """User'ning business plan'ini tekshirish"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'has_business_plan': False, 'redirect': BUSINESS_PLAN_REDIRECT_URL}), 200

    has_plan = check_business_plan(user_id)
    return jsonify({
        'has_business_plan': has_plan,
        'redirect': BUSINESS_PLAN_REDIRECT_URL if not has_plan else None
    })

@app.route('/')
@app.route('/warehouse')
@app.route('/reports')
@app.route('/employees')
@app.route('/ai-chat')
def index():
    """SPA - Barcha sahifalar bitta HTML faylda"""
    response = make_response(render_template('index.html'))
    # SPA uchun cache control
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

# ==================== API ENDPOINTS ====================

# ===== WAREHOUSE API =====

@app.route('/api/warehouse/products', methods=['GET'])
def get_products():
    """Barcha mahsulotlarni olish"""
    user_id = session.get('user_id')
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM warehouse_products WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,)
            )
            products = cursor.fetchall()
        connection.close()
        return jsonify({'success': True, 'data': products})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/warehouse/products', methods=['POST'])
def create_product():
    """Yangi mahsulot yaratish"""
    user_id = session.get('user_id')
    data = request.json
    
    try:
        product_id = execute_query(
            """INSERT INTO warehouse_products 
               (user_id, name, category, barcode, price, quantity, min_quantity, unit, image_url)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (user_id, data.get('name'), data.get('category'), data.get('barcode'),
             data.get('price', 0), data.get('quantity', 0), data.get('min_quantity', 0),
             data.get('unit', 'dona'), data.get('image_url'))
        )
        return jsonify({'success': True, 'data': {'id': product_id}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/warehouse/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Mahsulotni yangilash"""
    user_id = session.get('user_id')
    data = request.json
    
    try:
        execute_query(
            """UPDATE warehouse_products 
               SET name = %s, category = %s, barcode = %s, price = %s, 
                   quantity = %s, min_quantity = %s, unit = %s, image_url = %s,
                   updated_at = NOW()
               WHERE id = %s AND user_id = %s""",
            (data.get('name'), data.get('category'), data.get('barcode'),
             data.get('price'), data.get('quantity'), data.get('min_quantity'),
             data.get('unit'), data.get('image_url'), product_id, user_id)
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/warehouse/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Mahsulotni o'chirish"""
    user_id = session.get('user_id')
    
    try:
        execute_query(
            "DELETE FROM warehouse_products WHERE id = %s AND user_id = %s",
            (product_id, user_id)
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/warehouse/movements', methods=['GET'])
def get_movements():
    """Ombor harakatlarini olish"""
    user_id = session.get('user_id')
    product_id = request.args.get('product_id')
    
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            if product_id:
                cursor.execute(
                    """SELECT wm.*, wp.name as product_name 
                       FROM warehouse_movements wm
                       JOIN warehouse_products wp ON wm.product_id = wp.id
                       WHERE wm.user_id = %s AND wm.product_id = %s
                       ORDER BY wm.created_at DESC""",
                    (user_id, product_id)
                )
            else:
                cursor.execute(
                    """SELECT wm.*, wp.name as product_name 
                       FROM warehouse_movements wm
                       JOIN warehouse_products wp ON wm.product_id = wp.id
                       WHERE wm.user_id = %s
                       ORDER BY wm.created_at DESC
                       LIMIT 100""",
                    (user_id,)
                )
            movements = cursor.fetchall()
        connection.close()
        return jsonify({'success': True, 'data': movements})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/warehouse/movements', methods=['POST'])
def create_movement():
    """Yangi ombor harakati yaratish"""
    user_id = session.get('user_id')
    data = request.json
    
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Movement yaratish
            cursor.execute(
                """INSERT INTO warehouse_movements 
                   (user_id, product_id, movement_type, quantity, price, reason)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (user_id, data.get('product_id'), data.get('movement_type'),
                 data.get('quantity'), data.get('price', 0), data.get('reason', 'other'))
            )
            
            # Product quantity'ni yangilash
            if data.get('movement_type') == 'in':
                cursor.execute(
                    "UPDATE warehouse_products SET quantity = quantity + %s WHERE id = %s AND user_id = %s",
                    (data.get('quantity'), data.get('product_id'), user_id)
                )
            else:  # out
                cursor.execute(
                    "UPDATE warehouse_products SET quantity = quantity - %s WHERE id = %s AND user_id = %s",
                    (data.get('quantity'), data.get('product_id'), user_id)
                )
            
            connection.commit()
        connection.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== TRANSACTIONS API =====

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """Tranzaksiyalarni olish"""
    user_id = session.get('user_id')
    limit = request.args.get('limit', 50, type=int)
    
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT * FROM transactions 
                   WHERE user_id = %s 
                   ORDER BY created_at DESC 
                   LIMIT %s""",
                (user_id, limit)
            )
            transactions = cursor.fetchall()
        connection.close()
        return jsonify({'success': True, 'data': transactions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== REPORTS API =====

@app.route('/api/reports/summary', methods=['GET'])
def get_reports_summary():
    """Hisobotlar summary"""
    user_id = session.get('user_id')
    period = request.args.get('period', 'month')  # day, week, month, year
    
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Period uchun date filter
            date_filters = {
                'day': "DATE(created_at) = CURDATE()",
                'week': "YEARWEEK(created_at) = YEARWEEK(NOW())",
                'month': "YEAR(created_at) = YEAR(NOW()) AND MONTH(created_at) = MONTH(NOW())",
                'year': "YEAR(created_at) = YEAR(NOW())"
            }
            date_filter = date_filters.get(period, date_filters['month'])
            
            # Income va Expense
            cursor.execute(
                f"""SELECT 
                    SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as total_income,
                    SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) as total_expense,
                    COUNT(*) as transaction_count
                   FROM transactions
                   WHERE user_id = %s AND {date_filter}""",
                (user_id,)
            )
            summary = cursor.fetchone()
            
            # Top categories
            cursor.execute(
                f"""SELECT category, SUM(amount) as total
                   FROM transactions
                   WHERE user_id = %s AND transaction_type = 'expense' AND {date_filter}
                   GROUP BY category
                   ORDER BY total DESC
                   LIMIT 5""",
                (user_id,)
            )
            top_categories = cursor.fetchall()
            
            # Warehouse stats
            cursor.execute(
                """SELECT 
                    COUNT(*) as total_products,
                    SUM(quantity * price) as total_value,
                    SUM(CASE WHEN quantity <= min_quantity THEN 1 ELSE 0 END) as low_stock_count
                   FROM warehouse_products
                   WHERE user_id = %s""",
                (user_id,)
            )
            warehouse_stats = cursor.fetchone()
            
        connection.close()
        
        return jsonify({
            'success': True,
            'data': {
                'summary': summary,
                'top_categories': top_categories,
                'warehouse_stats': warehouse_stats
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== EMPLOYEES API =====

@app.route('/api/employees', methods=['GET'])
def get_employees():
    """Barcha xodimlarni olish"""
    user_id = session.get('user_id')
    
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM business_employees WHERE owner_id = %s ORDER BY created_at DESC",
                (user_id,)
            )
            employees = cursor.fetchall()
        connection.close()
        return jsonify({'success': True, 'data': employees})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/employees', methods=['POST'])
def create_employee():
    """Yangi xodim qo'shish"""
    user_id = session.get('user_id')
    data = request.json
    
    try:
        employee_id = execute_query(
            """INSERT INTO business_employees (owner_id, telegram_id, name, role)
               VALUES (%s, %s, %s, %s)""",
            (user_id, data.get('telegram_id'), data.get('name'), data.get('role', 'employee'))
        )
        return jsonify({'success': True, 'data': {'id': employee_id}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/employees/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    """Xodimni yangilash"""
    user_id = session.get('user_id')
    data = request.json
    
    try:
        execute_query(
            """UPDATE business_employees 
               SET name = %s, role = %s, is_active = %s, updated_at = NOW()
               WHERE id = %s AND owner_id = %s""",
            (data.get('name'), data.get('role'), data.get('is_active', True), employee_id, user_id)
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/employees/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    """Xodimni o'chirish"""
    user_id = session.get('user_id')
    
    try:
        execute_query(
            "DELETE FROM business_employees WHERE id = %s AND owner_id = %s",
            (employee_id, user_id)
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Vazifalarni olish"""
    user_id = session.get('user_id')
    status = request.args.get('status')
    
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            if status:
                cursor.execute(
                    """SELECT t.*, e.name as employee_name
                       FROM business_tasks t
                       LEFT JOIN business_employees e ON t.employee_id = e.id
                       WHERE t.owner_id = %s AND t.status = %s
                       ORDER BY t.created_at DESC""",
                    (user_id, status)
                )
            else:
                cursor.execute(
                    """SELECT t.*, e.name as employee_name
                       FROM business_tasks t
                       LEFT JOIN business_employees e ON t.employee_id = e.id
                       WHERE t.owner_id = %s
                       ORDER BY t.created_at DESC""",
                    (user_id,)
                )
            tasks = cursor.fetchall()
        connection.close()
        return jsonify({'success': True, 'data': tasks})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Yangi vazifa yaratish"""
    user_id = session.get('user_id')
    data = request.json
    
    try:
        task_id = execute_query(
            """INSERT INTO business_tasks (owner_id, employee_id, title, description, due_date, status)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (user_id, data.get('employee_id'), data.get('title'), data.get('description'),
             data.get('due_date'), data.get('status', 'pending'))
        )
        return jsonify({'success': True, 'data': {'id': task_id}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Vazifani yangilash"""
    user_id = session.get('user_id')
    data = request.json

    try:
        completed_at = "NOW()" if data.get('status') == 'completed' else "NULL"
        execute_query(
            f"""UPDATE business_tasks
               SET title = %s, description = %s, due_date = %s, status = %s,
                   employee_id = %s, completed_at = {completed_at}
               WHERE id = %s AND owner_id = %s""",
            (data.get('title'), data.get('description'), data.get('due_date'),
             data.get('status'), data.get('employee_id'), task_id, user_id)
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Vazifani o'chirish"""
    user_id = session.get('user_id')

    try:
        execute_query(
            "DELETE FROM business_tasks WHERE id = %s AND owner_id = %s",
            (task_id, user_id)
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== ADVANCED ANALYTICS API =====

@app.route('/api/analytics/dashboard', methods=['GET'])
def get_analytics_dashboard():
    """Kengaytirilgan analitika dashboard"""
    user_id = session.get('user_id')
    period = request.args.get('period', 'month')

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Period filter
            date_filters = {
                'day': "DATE(created_at) = CURDATE()",
                'week': "YEARWEEK(created_at) = YEARWEEK(NOW())",
                'month': "YEAR(created_at) = YEAR(NOW()) AND MONTH(created_at) = MONTH(NOW())",
                'year': "YEAR(created_at) = YEAR(NOW())"
            }
            date_filter = date_filters.get(period, date_filters['month'])

            # Profit margins
            cursor.execute(
                f"""SELECT
                    SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as revenue,
                    SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) as costs,
                    SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) -
                    SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) as profit,
                    COUNT(CASE WHEN transaction_type = 'income' THEN 1 END) as sales_count,
                    AVG(CASE WHEN transaction_type = 'income' THEN amount END) as avg_sale
                FROM transactions
                WHERE user_id = %s AND {date_filter}""",
                (user_id,)
            )
            financial_metrics = cursor.fetchone()

            # Daily trends (last 30 days)
            cursor.execute(
                """SELECT
                    DATE(created_at) as date,
                    SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as daily_income,
                    SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) as daily_expense
                FROM transactions
                WHERE user_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                GROUP BY DATE(created_at)
                ORDER BY date DESC
                LIMIT 30""",
                (user_id,)
            )
            daily_trends = cursor.fetchall()

            # Top selling products
            cursor.execute(
                """SELECT
                    wp.name,
                    wp.category,
                    SUM(wm.quantity) as total_sold,
                    SUM(wm.quantity * wm.price) as total_revenue
                FROM warehouse_movements wm
                JOIN warehouse_products wp ON wm.product_id = wp.id
                WHERE wm.user_id = %s AND wm.movement_type = 'out'
                    AND wm.reason = 'sale'
                    AND wm.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                GROUP BY wm.product_id, wp.name, wp.category
                ORDER BY total_revenue DESC
                LIMIT 10""",
                (user_id,)
            )
            top_products = cursor.fetchall()

            # Low stock alerts
            cursor.execute(
                """SELECT name, category, quantity, min_quantity, price
                FROM warehouse_products
                WHERE user_id = %s AND quantity <= min_quantity
                ORDER BY (quantity - min_quantity)
                LIMIT 10""",
                (user_id,)
            )
            low_stock_alerts = cursor.fetchall()

            # Employee performance
            cursor.execute(
                """SELECT
                    e.name as employee_name,
                    COUNT(t.id) as total_tasks,
                    SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN t.status = 'pending' THEN 1 ELSE 0 END) as pending_tasks
                FROM business_employees e
                LEFT JOIN business_tasks t ON e.id = t.employee_id
                WHERE e.owner_id = %s AND e.is_active = TRUE
                GROUP BY e.id, e.name
                ORDER BY completed_tasks DESC
                LIMIT 10""",
                (user_id,)
            )
            employee_performance = cursor.fetchall()

        connection.close()

        # Calculate profit margin
        revenue = financial_metrics.get('revenue') or 0
        costs = financial_metrics.get('costs') or 0
        profit = financial_metrics.get('profit') or 0
        profit_margin = (profit / revenue * 100) if revenue > 0 else 0

        return jsonify({
            'success': True,
            'data': {
                'financial_metrics': {
                    **financial_metrics,
                    'profit_margin': round(profit_margin, 2)
                },
                'daily_trends': daily_trends,
                'top_products': top_products,
                'low_stock_alerts': low_stock_alerts,
                'employee_performance': employee_performance
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analytics/forecast', methods=['GET'])
def get_forecast():
    """Bashorat - daromad va chiqim prognozi"""
    user_id = session.get('user_id')

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Last 6 months data
            cursor.execute(
                """SELECT
                    DATE_FORMAT(created_at, '%Y-%m') as month,
                    SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as income,
                    SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) as expense
                FROM transactions
                WHERE user_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
                GROUP BY DATE_FORMAT(created_at, '%Y-%m')
                ORDER BY month DESC
                LIMIT 6""",
                (user_id,)
            )
            historical_data = cursor.fetchall()

        connection.close()

        # Simple forecast (average growth)
        if historical_data and len(historical_data) >= 3:
            incomes = [row.get('income', 0) or 0 for row in historical_data]
            expenses = [row.get('expense', 0) or 0 for row in historical_data]

            avg_income = sum(incomes) / len(incomes)
            avg_expense = sum(expenses) / len(expenses)

            # Growth rate calculation
            if len(incomes) >= 2 and incomes[-1] > 0:
                income_growth = ((incomes[0] - incomes[-1]) / incomes[-1]) / len(incomes)
            else:
                income_growth = 0

            if len(expenses) >= 2 and expenses[-1] > 0:
                expense_growth = ((expenses[0] - expenses[-1]) / expenses[-1]) / len(expenses)
            else:
                expense_growth = 0

            # Next month forecast
            forecast_income = avg_income * (1 + income_growth)
            forecast_expense = avg_expense * (1 + expense_growth)
            forecast_profit = forecast_income - forecast_expense

            return jsonify({
                'success': True,
                'data': {
                    'historical': historical_data,
                    'forecast': {
                        'next_month_income': round(forecast_income, 2),
                        'next_month_expense': round(forecast_expense, 2),
                        'next_month_profit': round(forecast_profit, 2),
                        'income_growth_rate': round(income_growth * 100, 2),
                        'expense_growth_rate': round(expense_growth * 100, 2)
                    }
                }
            })
        else:
            return jsonify({
                'success': True,
                'data': {
                    'historical': historical_data,
                    'forecast': {
                        'message': 'Prognoz uchun yetarli ma\'lumot yo\'q. Kamida 3 oylik ma\'lumot kerak.'
                    }
                }
            })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analytics/category-analysis', methods=['GET'])
def get_category_analysis():
    """Kategoriyalar bo'yicha batafsil tahlil"""
    user_id = session.get('user_id')

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Expense by category
            cursor.execute(
                """SELECT
                    category,
                    COUNT(*) as transaction_count,
                    SUM(amount) as total_amount,
                    AVG(amount) as avg_amount,
                    MIN(amount) as min_amount,
                    MAX(amount) as max_amount
                FROM transactions
                WHERE user_id = %s AND transaction_type = 'expense'
                    AND created_at >= DATE_SUB(NOW(), INTERVAL 3 MONTH)
                GROUP BY category
                ORDER BY total_amount DESC""",
                (user_id,)
            )
            expense_categories = cursor.fetchall()

            # Income by category
            cursor.execute(
                """SELECT
                    category,
                    COUNT(*) as transaction_count,
                    SUM(amount) as total_amount,
                    AVG(amount) as avg_amount
                FROM transactions
                WHERE user_id = %s AND transaction_type = 'income'
                    AND created_at >= DATE_SUB(NOW(), INTERVAL 3 MONTH)
                GROUP BY category
                ORDER BY total_amount DESC""",
                (user_id,)
            )
            income_categories = cursor.fetchall()

        connection.close()

        return jsonify({
            'success': True,
            'data': {
                'expense_categories': expense_categories,
                'income_categories': income_categories
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== AI CHAT API =====

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat_api():
    """AI chat endpoint - Biznes ma'lumotlarini tahlil qiladi"""
    user_id = session.get('user_id')
    data = request.json
    message = data.get('message', '').lower()

    try:
        # Simple AI responses based on keywords
        response = generate_ai_response(user_id, message)

        return jsonify({
            'success': True,
            'data': {
                'response': response
            }
        })
    except Exception as e:
        return jsonify({
            'success': True,
            'data': {
                'response': f"Kechirasiz, sizning so'rovingizni tushunmadim. Iltimos, boshqa tarzda so'rang."
            }
        })

def generate_ai_response(user_id, message):
    """Generate intelligent responses based on business data"""
    connection = get_db_connection()

    try:
        # Keyword-based responses
        if any(word in message for word in ['salom', 'assalom', 'hello', 'hi']):
            return "Assalomu alaykum! Men sizning biznes yordamchingizman. Qanday yordam bera olaman?"

        elif any(word in message for word in ['balans', 'hisob', 'pul', 'daromad', 'foyda']):
            with connection.cursor() as cursor:
                # Get financial summary with profit margin
                cursor.execute(
                    """SELECT
                        SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as income,
                        SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) as expense
                       FROM transactions
                       WHERE user_id = %s AND YEAR(created_at) = YEAR(NOW()) AND MONTH(created_at) = MONTH(NOW())""",
                    (user_id,)
                )
                result = cursor.fetchone()
                if result:
                    income = result.get('income', 0) or 0
                    expense = result.get('expense', 0) or 0
                    balance = income - expense
                    profit_margin = (balance / income * 100) if income > 0 else 0

                    return f"Joriy oy uchun:\n💰 Kirim: {income:,.0f} UZS\n💸 Chiqim: {expense:,.0f} UZS\n📊 Sof foyda: {balance:,.0f} UZS\n📈 Foyda darajasi: {profit_margin:.1f}%\n\n{'✅ Ajoyib natija!' if profit_margin > 30 else '✅ Yaxshi natija!' if profit_margin > 15 else '⚠️ Chiqimlarni optimallashtiring.' if profit_margin > 0 else '🚨 Zararda ishlayapsiz!'}"

        elif any(word in message for word in ['prognoz', 'bashorat', 'forecast', 'kelajak']):
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT
                        DATE_FORMAT(created_at, '%Y-%m') as month,
                        SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as income,
                        SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) as expense
                    FROM transactions
                    WHERE user_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 3 MONTH)
                    GROUP BY DATE_FORMAT(created_at, '%Y-%m')
                    ORDER BY month DESC
                    LIMIT 3""",
                    (user_id,)
                )
                data = cursor.fetchall()
                if data and len(data) >= 2:
                    incomes = [row.get('income', 0) or 0 for row in data]
                    avg_income = sum(incomes) / len(incomes)
                    growth = ((incomes[0] - incomes[-1]) / incomes[-1] * 100) if incomes[-1] > 0 else 0

                    return f"📊 So'nggi 3 oy tahlili:\n💰 O'rtacha kirim: {avg_income:,.0f} UZS\n📈 O'sish sur'ati: {growth:+.1f}%\n\n{'🚀 Biznesingiz rivojlanmoqda!' if growth > 5 else '⚠️ O'sish sur\'atini oshirish tavsiya etiladi.' if growth > 0 else '🚨 Kirimlar kamaymoqda, strategiyani ko\'rib chiqing!'}"

        elif any(word in message for word in ['eng', 'top', 'yaxshi', 'ko\'p sotilgan']):
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT
                        wp.name,
                        SUM(wm.quantity) as total_sold,
                        SUM(wm.quantity * wm.price) as revenue
                    FROM warehouse_movements wm
                    JOIN warehouse_products wp ON wm.product_id = wp.id
                    WHERE wm.user_id = %s AND wm.movement_type = 'out'
                        AND wm.reason = 'sale'
                        AND wm.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                    GROUP BY wm.product_id, wp.name
                    ORDER BY revenue DESC
                    LIMIT 5""",
                    (user_id,)
                )
                products = cursor.fetchall()
                if products:
                    response = "🏆 Eng ko'p sotilgan mahsulotlar (30 kun):\n\n"
                    for i, p in enumerate(products, 1):
                        response += f"{i}. {p['name']}: {p['total_sold']} ta, {p['revenue']:,.0f} UZS\n"
                    return response
                else:
                    return "📦 Hali sotuvlar ro'yxati mavjud emas."

        elif any(word in message for word in ['ombor', 'mahsulot', 'product', 'stock']):
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT COUNT(*) as total,
                       SUM(CASE WHEN quantity <= min_quantity THEN 1 ELSE 0 END) as low_stock,
                       SUM(quantity * price) as total_value
                       FROM warehouse_products WHERE user_id = %s""",
                    (user_id,)
                )
                result = cursor.fetchone()
                if result:
                    total = result.get('total', 0)
                    low_stock = result.get('low_stock', 0)
                    total_value = result.get('total_value', 0) or 0
                    return f"📦 Ombor holati:\n• Jami mahsulotlar: {total} ta\n• Umumiy qiymati: {total_value:,.0f} UZS\n• {'⚠️ Kam qolganlar: ' + str(low_stock) + ' ta' if low_stock > 0 else '✅ Barcha mahsulotlar yetarli'}"

        elif any(word in message for word in ['xodim', 'employee', 'jamoa', 'team']):
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) as active
                    FROM business_employees WHERE owner_id = %s""",
                    (user_id,)
                )
                emp_result = cursor.fetchone()

                cursor.execute(
                    """SELECT
                        e.name,
                        COUNT(t.id) as total_tasks,
                        SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed
                    FROM business_employees e
                    LEFT JOIN business_tasks t ON e.id = t.employee_id
                    WHERE e.owner_id = %s AND e.is_active = TRUE
                    GROUP BY e.id, e.name
                    ORDER BY completed DESC
                    LIMIT 1""",
                    (user_id,)
                )
                top_employee = cursor.fetchone()

                total = emp_result.get('total', 0)
                active = emp_result.get('active', 0)
                response = f"👥 Jamoa:\n• Jami xodimlar: {total} ta\n• Faollar: {active} ta\n"

                if top_employee and top_employee.get('completed', 0) > 0:
                    response += f"\n⭐ Eng samarali: {top_employee['name']} ({top_employee['completed']} ta vazifa)"

                return response

        elif any(word in message for word in ['vazifa', 'task', 'ish']):
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT COUNT(*) as total,
                       SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                       SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                       SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
                       FROM business_tasks WHERE owner_id = %s""",
                    (user_id,)
                )
                result = cursor.fetchone()
                if result:
                    total = result.get('total', 0)
                    pending = result.get('pending', 0) or 0
                    in_progress = result.get('in_progress', 0) or 0
                    completed = result.get('completed', 0) or 0
                    completion_rate = (completed / total * 100) if total > 0 else 0

                    return f"📋 Vazifalar:\n• Jami: {total} ta\n• ⏳ Kutilmoqda: {pending}\n• 🔄 Jarayonda: {in_progress}\n• ✅ Bajarilgan: {completed}\n\n📊 Bajarilish foizi: {completion_rate:.0f}%"

        elif any(word in message for word in ['tahlil', 'analiz', 'analytics', 'statistics']):
            return "📊 Kengaytirilgan analitika:\n\n• 💰 Moliyaviy ko'rsatkichlar\n• 📈 Daromad prognozi\n• 🏆 Eng yaxshi mahsulotlar\n• 📉 Trend tahlili\n• 👥 Xodimlar samaradorligi\n\n'Hisobotlar' bo'limida batafsil ma'lumot!"

        elif any(word in message for word in ['hisobot', 'report']):
            return "📊 Hisobotlar bo'limida:\n• Moliyaviy hisobotlar\n• Ombor statistikasi\n• Foyda tahlili\n• Trend grafiklar\n• Xodimlar faoliyati\n\nHisobotlar sahifasiga o'ting!"

        elif any(word in message for word in ['yordam', 'help', 'qanday']):
            return "🤖 Men sizga yordam bera olaman:\n\n💰 Moliyaviy tahlil va prognoz\n📦 Ombor boshqaruvi\n👥 Xodimlar samaradorligi\n📊 Biznes statistikasi\n🎯 Eng yaxshi mahsulotlar\n\nSavolingizni yozing!"

        elif any(word in message for word in ['rahmat', 'thank', 'minnatdor']):
            return "Marhamat! Biznesingiz rivojlansin! 🚀"

        else:
            return ("🤖 Men sizning AI biznes yordamchingizman. So'rashingiz mumkin:\n\n"
                   "💰 'Balansim qancha?'\n📈 'Prognoz ko'rsat'\n🏆 'Eng ko\'p sotilgan mahsulotlar'\n"
                   "📦 'Ombor holati'\n👥 'Xodimlar haqida'\n📊 'Tahlil'\n\nYoki o'z savolingizni yozing!")

    finally:
        connection.close()

if __name__ == '__main__':
    # Production'da gunicorn ishlatiladi, bu faqat development uchun
    port = int(os.environ.get('PORT', 5000))
    debug = DEBUG or os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)

