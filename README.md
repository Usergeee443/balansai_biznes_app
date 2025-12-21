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

## Eslatmalar

- Barcha API endpoint'lar Telegram auth talab qiladi
- `X-Telegram-Init-Data` header'da initData bo'lishi kerak
- Database bot bilan bir xil database bilan ishlaydi

