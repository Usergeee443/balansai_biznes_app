# Balans AI - Biznes Tarifi

## Yangi Funksiyalar va Yaxshilanishlar

### 🔐 Autentifikatsiya va Xavfsizlik

#### 1. **Yaxshilangan Autentifikatsiya**
- ✅ Development mode'da avtomatik test user yaratish
- ✅ Telegram initData validatsiyasi
- ✅ Session boshqaruvi
- ✅ DEBUG rejimi

#### 2. **Biznes Tarif Tekshiruvi**
- ✅ Foydalanuvchining biznes tarifini tekshirish
- ✅ Agar biznes tarif bo'lmasa, avtomatik redirect: `https://balansai-app.onrender.com`
- ✅ `/api/check-plan` endpoint orqali tarif holati tekshirish

### 📊 Kengaytirilgan Analitika

#### 3. **Moliyaviy Dashboard** (`/api/analytics/dashboard`)
Quyidagi ko'rsatkichlarni taqdim etadi:
- 💰 **Revenue** (Daromad)
- 💸 **Costs** (Xarajatlar)
- 📈 **Profit** (Foyda)
- 📊 **Profit Margin** (Foyda darajasi, %)
- 🛒 **Sales Count** (Sotuvlar soni)
- 💵 **Average Sale** (O'rtacha sotuv)
- 📅 **Daily Trends** (30 kunlik kunlik tendentsiyalar)
- 🏆 **Top Selling Products** (Eng ko'p sotilgan mahsulotlar)
- ⚠️ **Low Stock Alerts** (Kam qolgan mahsulotlar)
- 👥 **Employee Performance** (Xodimlar samaradorligi)

#### 4. **Biznes Prognozi** (`/api/analytics/forecast`)
- 📈 So'nggi 6 oylik tarixiy ma'lumotlar
- 🔮 Keyingi oy uchun daromad prognozi
- 📉 Keyingi oy uchun xarajatlar prognozi
- 💰 Keyingi oy uchun foyda prognozi
- 📊 Daromad o'sish sur'ati (%)
- 📊 Xarajatlar o'sish sur'ati (%)

**Xususiyatlar:**
- Simple moving average asosida prognoz
- Growth rate kalkulyatsiyasi
- Minimal 3 oylik ma'lumot talab qilinadi

#### 5. **Kategoriyalar Tahlili** (`/api/analytics/category-analysis`)
- 📊 Xarajatlar kategoriyalari bo'yicha:
  - Tranzaksiyalar soni
  - Umumiy summa
  - O'rtacha summa
  - Minimal summa
  - Maksimal summa
- 💰 Kirimlar kategoriyalari bo'yicha:
  - Tranzaksiyalar soni
  - Umumiy summa
  - O'rtacha summa

### 🤖 Yaxshilangan AI Yordamchi

#### 6. **Aqlli Chatbot**
AI yordamchi quyidagi so'rovlarga javob beradi:

**Moliyaviy Ma'lumotlar:**
- `"Balansim qancha?"` → Kirim, chiqim, foyda va foyda darajasini ko'rsatadi
- `"Prognoz ko'rsat"` → 3 oylik trend tahlili va o'sish sur'ati

**Mahsulotlar:**
- `"Ombor holati"` → Mahsulotlar soni, umumiy qiymati, kam qolganlar
- `"Eng ko'p sotilgan mahsulotlar"` → Top 5 mahsulotlar (30 kun)

**Jamoa:**
- `"Xodimlar haqida"` → Jami va faol xodimlar, eng samarali xodim
- `"Vazifalar"` → Vazifalar statistikasi va bajarilish foizi

**Tahlil:**
- `"Tahlil"` / `"Statistika"` → Analitika bo'limlari haqida ma'lumot

### 🎨 UI/UX Yaxshilanishlari

#### 7. **Telegram-style Dizayn**
- ✨ Modern va zamonaviy interfeys
- 🎨 Telegram ranglar sxemasi
- 🔄 Smooth animatsiyalar
- 📱 To'liq responsive dizayn
- 🎯 Haptic feedback

#### 8. **Optimallashtirish**
- ⚡ Lazy loading
- 💾 Data caching
- 🚀 Tezkor navigatsiya
- 🔄 Real-time yangilanishlar

### 🔧 Backend Yaxshilanishlari

#### 9. **Konfiguratsiya**
`.env` fayli orqali:
```env
FLASK_ENV=development
SECRET_KEY=your-secret-key
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=balansai_db
BOT_TOKEN=your_bot_token
BUSINESS_PLAN_REDIRECT_URL=https://balansai-app.onrender.com
DEBUG=True
```

#### 10. **Xavfsizlik**
- ✅ Session-based authentication
- ✅ Business plan verification
- ✅ SQL injection protection (prepared statements)
- ✅ CORS support

### 📈 Statistika va Hisobotlar

#### 11. **Kengaytirilgan Hisobotlar**
- 📊 Period filterlari (kun, hafta, oy, yil)
- 📈 Trend grafiklar
- 💰 Foyda marjasi tahlili
- 🏆 Top mahsulotlar
- 👥 Xodimlar samaradorligi
- ⚠️ Ogohlantirish tizimi (kam qolgan mahsulotlar)

### 🚀 Qo'shimcha Imkoniyatlar

#### 12. **API Endpoints**
Barcha yangi endpointlar:
- `GET /api/check-plan` - Biznes tarif tekshiruvi
- `GET /api/analytics/dashboard` - Kengaytirilgan dashboard
- `GET /api/analytics/forecast` - Biznes prognozi
- `GET /api/analytics/category-analysis` - Kategoriyalar tahlili
- `POST /api/ai/chat` - Yaxshilangan AI chat

### 📝 Ishlatish

#### Development Mode'da Ishga Tushirish:
```bash
# .env faylini yaratish
cp .env.example .env

# .env faylida ma'lumotlarni to'ldirish
# DEBUG=True bo'lishi kerak

# Virtual environment yaratish
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# yoki
.venv\Scripts\activate     # Windows

# Dependencies o'rnatish
pip install -r requirements.txt

# Serverni ishga tushirish
python3 app.py
```

Server `http://127.0.0.1:5000` da ishga tushadi.

#### Production Mode:
```bash
# .env faylida
DEBUG=False
FLASK_ENV=production

# Gunicorn bilan ishga tushirish
gunicorn app:app --bind 0.0.0.0:5000
```

### 🔍 Muammolar va Yechimlar

#### 401 Unauthorized Errors
**Sabab:** Debug mode o'chiq va Telegram initData yo'q

**Yechim:** .env faylida `DEBUG=True` qiling

#### Database Connection Error
**Yechim:** `.env` faylida database ma'lumotlarini tekshiring

### 📞 Yordam

Muammolaringiz bo'lsa:
1. `.env` faylini tekshiring
2. `DEBUG=True` qilib ko'ring
3. Database connection'ni tekshiring
4. `requirements.txt` dan barcha paketlar o'rnatilganligini tekshiring

---

**Versiya:** 2.0
**Oxirgi Yangilanish:** 2026-01-06
**Muallif:** Balans AI Team
