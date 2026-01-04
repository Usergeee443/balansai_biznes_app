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

# Middleware: Telegram auth tekshirish
@app.before_request
def check_telegram_auth():
    """Har bir request'da Telegram auth'ni tekshirish"""
    # Static fayllar va HTML sahifalar uchun auth talab qilinmaydi
    if (request.path.startswith('/static') or 
        request.path == '/' or
        request.path in ['/warehouse', '/reports', '/employees', '/ai-chat']):
        return None
    
    # Faqat API endpoint'lar uchun auth talab qilinadi
    if not request.path.startswith('/api/'):
        return None
    
    init_data = request.headers.get('X-Telegram-Init-Data') or request.args.get('initData')
    
    # Development mode: Agar initData bo'lmasa, test user_id bilan ishlash
    if not init_data:
        # Development uchun test user_id (production'da o'chirilishi kerak)
        if app.debug:
            test_user_id = 123456789
            ensure_test_user_exists(test_user_id)
            session['user_id'] = test_user_id
            session['username'] = 'test_user'
            return None
        return jsonify({'error': 'Telegram auth talab qilinadi'}), 401
    
    try:
        user_data = validate_telegram_init_data(init_data, BOT_TOKEN)
        session['user_id'] = user_data.get('user_id')
        session['username'] = user_data.get('username')
    except ValueError as e:
        # Development mode: Agar validatsiya muvaffaqiyatsiz bo'lsa, test user_id bilan ishlash
        if app.debug:
            test_user_id = 123456789
            ensure_test_user_exists(test_user_id)
            session['user_id'] = test_user_id
            session['username'] = 'test_user'
            return None
        return jsonify({'error': str(e)}), 401

# ==================== ROUTES ====================

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

        elif any(word in message for word in ['balans', 'hisob', 'pul', 'daromad']):
            with connection.cursor() as cursor:
                # Get financial summary
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
                    return f"Joriy oy uchun:\n💰 Kirim: {income:,.0f} UZS\n💸 Chiqim: {expense:,.0f} UZS\n📊 Balans: {balance:,.0f} UZS\n\n{'✅ Yaxshi natija!' if balance > 0 else '⚠️ Chiqimlarni kamaytiring.'}"

        elif any(word in message for word in ['ombor', 'mahsulot', 'product']):
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT COUNT(*) as total,
                       SUM(CASE WHEN quantity <= min_quantity THEN 1 ELSE 0 END) as low_stock
                       FROM warehouse_products WHERE user_id = %s""",
                    (user_id,)
                )
                result = cursor.fetchone()
                if result:
                    total = result.get('total', 0)
                    low_stock = result.get('low_stock', 0)
                    return f"📦 Omboringizda {total} ta mahsulot bor.\n{'⚠️ ' + str(low_stock) + ' ta mahsulot tugab qolmoqda!' if low_stock > 0 else '✅ Barcha mahsulotlar yetarli miqdorda.'}"

        elif any(word in message for word in ['xodim', 'employee', 'jamoa', 'team']):
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) as total FROM business_employees WHERE owner_id = %s AND is_active = TRUE",
                    (user_id,)
                )
                result = cursor.fetchone()
                if result:
                    total = result.get('total', 0)
                    return f"👥 Sizda {total} ta faol xodim bor. Jamoa boshqaruvi uchun 'Xodimlar' bo'limiga o'ting."

        elif any(word in message for word in ['vazifa', 'task', 'ish']):
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT COUNT(*) as total,
                       SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                       SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress
                       FROM business_tasks WHERE owner_id = %s""",
                    (user_id,)
                )
                result = cursor.fetchone()
                if result:
                    total = result.get('total', 0)
                    pending = result.get('pending', 0) or 0
                    in_progress = result.get('in_progress', 0) or 0
                    return f"📋 Jami vazifalar: {total}\n⏳ Kutilmoqda: {pending}\n🔄 Jarayonda: {in_progress}"

        elif any(word in message for word in ['hisobot', 'report', 'statistika']):
            return "📊 Hisobotlar bo'limida siz quyidagilarni ko'rishingiz mumkin:\n• Moliyaviy hisobotlar\n• Ombor statistikasi\n• Xodimlar faoliyati\n• Vazifalar holati\n\nHisobotlar sahifasiga o'ting!"

        elif any(word in message for word in ['yordam', 'help', 'qanday']):
            return "Men sizga quyidagi mavzularda yordam bera olaman:\n\n💰 Balans va moliya\n📦 Ombor boshqaruvi\n👥 Xodimlar va vazifalar\n📊 Hisobotlar\n\nSo'rovingizni yozing va men sizga javob beraman!"

        elif any(word in message for word in ['rahmat', 'thank', 'minnatdor']):
            return "Arzimaydi! Yana qanday yordam bera olaman? 😊"

        else:
            return ("Men sizning biznes yordamchingizman. Quyidagilar haqida so'rashingiz mumkin:\n\n"
                   "💰 Balans va moliya\n📦 Ombor mahsulotlari\n👥 Xodimlar\n📋 Vazifalar\n📊 Hisobotlar\n\n"
                   "Masalan: 'Balansim qancha?' yoki 'Omborda nechta mahsulot bor?'")

    finally:
        connection.close()

if __name__ == '__main__':
    # Production'da gunicorn ishlatiladi, bu faqat development uchun
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)

