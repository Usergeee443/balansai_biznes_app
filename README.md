# BALANS AI — BIZNES TARIFI MINI ILOVA

Telegram Mini App orqali biznesni boshqarish: ombor, hisobotlar, xodimlar va AI chat.

## Texnologiyalar

- **Backend**: Python Flask
- **Frontend**: HTML + Tailwind CSS + JavaScript
- **Database**: MySQL (bot bilan bir xil database)
- **Integratsiya**: Telegram Mini App API

## O'rnatish

### 1. Paketlarni o'rnatish

```bash
pip install -r requirements.txt
```

### 2. Environment variables

`.env` faylini yarating:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=balansai_db
BOT_TOKEN=your_telegram_bot_token
SECRET_KEY=your_secret_key
```

### 3. Database jadvallarini yaratish

MySQL'da `database_schema.sql` faylini bajarish:

```bash
mysql -u root -p balansai_db < database_schema.sql
```

### 4. Serverni ishga tushirish

```bash
python app.py
```

Server `http://localhost:5000` da ishga tushadi.

## Struktura

```
.
├── app.py              # Flask server
├── database.py         # Database connection
├── telegram_auth.py    # Telegram initData validatsiya
├── database_schema.sql # Database jadvallari
├── requirements.txt    # Python paketlar
├── templates/          # HTML shablonlar
│   ├── index.html
│   ├── warehouse.html
│   ├── reports.html
│   ├── employees.html
│   └── ai_chat.html
└── static/
    └── js/
        ├── app.js
        ├── warehouse.js
        ├── reports.js
        ├── employees.js
        └── ai_chat.js
```

## API Endpoints

### Warehouse
- `GET /api/warehouse/products` - Barcha mahsulotlar
- `POST /api/warehouse/products` - Yangi mahsulot
- `PUT /api/warehouse/products/<id>` - Mahsulotni yangilash
- `DELETE /api/warehouse/products/<id>` - Mahsulotni o'chirish
- `GET /api/warehouse/movements` - Ombor harakatlari
- `POST /api/warehouse/movements` - Yangi harakat

### Reports
- `GET /api/reports/summary?period=<period>` - Hisobotlar summary

### Employees
- `GET /api/employees` - Barcha xodimlar
- `POST /api/employees` - Yangi xodim
- `PUT /api/employees/<id>` - Xodimni yangilash
- `DELETE /api/employees/<id>` - Xodimni o'chirish
- `GET /api/tasks` - Vazifalar
- `POST /api/tasks` - Yangi vazifa
- `PUT /api/tasks/<id>` - Vazifani yangilash

### AI Chat
- `POST /api/ai/chat` - AI chat xabari

## Telegram Mini App sozlash

Telegram bot'da Mini App'ni sozlash:

1. BotFather'da `/newapp` buyrug'ini bajarish
2. Bot'ni tanlash
3. App title va description berish
4. Web App URL: `https://your-domain.com/`
5. Web App icon yuklash

## Render'ga Deploy Qilish

### 1. GitHub'ga yuklash

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/balansai-biznes-app.git
git push -u origin main
```

### 2. Render'da yangi Web Service yaratish

1. [Render Dashboard](https://dashboard.render.com/) ga kiring
2. "New +" → "Web Service" ni tanlang
3. GitHub repository'ni ulang
4. Quyidagi sozlamalarni kiriting:
   - **Name**: `balansai-biznes-app`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

### 3. Environment Variables qo'shish

Render Dashboard'da "Environment" bo'limiga quyidagi o'zgaruvchilarni qo'shing:

```
DB_HOST=your_mysql_host
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=your_database_name
BOT_TOKEN=your_telegram_bot_token
SECRET_KEY=your-strong-secret-key-here
FLASK_ENV=production
```

**Muhim**: 
- `SECRET_KEY` - kuchli random string bo'lishi kerak (masalan: `openssl rand -hex 32`)
- Database - Render'da MySQL service yaratish yoki tashqi MySQL server ishlatish

### 4. Database sozlash

Agar Render'da MySQL service yaratmoqchi bo'lsangiz:

1. "New +" → "MySQL" ni tanlang
2. Database yarating
3. `database_schema.sql` faylini bajarish:
   ```bash
   mysql -h <host> -u <user> -p <database> < database_schema.sql
   ```
4. Database connection ma'lumotlarini environment variables'ga qo'shing

### 5. Telegram Mini App URL'ni yangilash

Deploy qilingan URL'ni Telegram bot'ga qo'shing:

1. BotFather'da `/newapp` yoki `/editapp`
2. Web App URL: `https://your-app-name.onrender.com/`

### 6. Custom Domain (ixtiyoriy)

Agar custom domain ishlatmoqchi bo'lsangiz:

1. Render Dashboard'da "Settings" → "Custom Domain"
2. Domain'ni qo'shing va DNS sozlamalarini bajarish

## Production Sozlamalari

- `FLASK_ENV=production` - Debug mode o'chiriladi
- `SECRET_KEY` - Kuchli secret key ishlatilishi kerak
- Database - Production-ready MySQL server
- HTTPS - Render avtomatik HTTPS ta'minlaydi

## Eslatmalar

- Barcha API endpoint'lar Telegram auth talab qiladi
- `X-Telegram-Init-Data` header'da initData bo'lishi kerak
- Database bot bilan bir xil database bilan ishlaydi
- Render'da free tier'da app 15 daqiqa ishlatilmaganda uxlaydi (cold start ~30 soniya)

