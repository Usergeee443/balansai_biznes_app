# GitHub'dan Xavfli Fayllarni O'chirish

Agar `.env`, `.venv` yoki `__pycache__` fayllarini GitHub'ga yuklab yuborgan bo'lsangiz, quyidagi qadamlarni bajarishingiz kerak:

## ⚠️ MUHIM: Avval Secret Key'larni o'zgartiring!

Agar `.env` fayli GitHub'ga yuklangan bo'lsa:
1. **Darhol barcha secret key'larni o'zgartiring:**
   - Database parolini o'zgartiring
   - `SECRET_KEY` ni yangi key bilan almashtiring
   - `BOT_TOKEN` ni yangi token bilan almashtiring (agar kerak bo'lsa)

## GitHub'dan Fayllarni O'chirish

### 1-usul: Git History'dan To'liq O'chirish (Tavsiya etiladi)

```bash
# Repository'ni klon qiling (agar hali klon qilmagan bo'lsangiz)
git clone https://github.com/yourusername/balansai-biznes-app.git
cd balansai-biznes-app

# Git history'dan fayllarni o'chirish
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env .venv __pycache__" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (ehtiyot bo'ling!)
git push origin --force --all
git push origin --force --tags
```

### 2-usul: BFG Repo-Cleaner (Tavsiya etiladi)

```bash
# BFG Repo-Cleaner o'rnatish
brew install bfg  # macOS
# yoki
# https://rtyley.github.io/bfg-repo-cleaner/ dan yuklab oling

# Repository'ni clone qiling (bare repository)
git clone --mirror https://github.com/yourusername/balansai-biznes-app.git

# Fayllarni o'chirish
bfg --delete-files .env
bfg --delete-files .venv
bfg --delete-folders __pycache__

# Repository'ni tozalash
cd balansai-biznes-app.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push --force
```

### 3-usul: GitHub Web Interface (Oson, lekin history saqlanadi)

1. GitHub'da repository'ga kiring
2. `.env` faylini toping
3. "Delete" tugmasini bosing
4. Commit qiling

**Eslatma:** Bu usul faqat faylni o'chiradi, lekin Git history'da saqlanib qoladi.

## .gitignore'ni Tekshirish

`.gitignore` fayli to'g'ri sozlanganligini tekshiring:

```bash
# .gitignore'ni ko'rish
cat .gitignore

# Fayllar ignore qilinganligini tekshirish
git check-ignore -v .env
git check-ignore -v .venv
git check-ignore -v __pycache__
```

## Keyingi Qadamlar

1. **Secret key'larni o'zgartiring** (muhim!)
2. **.gitignore'ni yangilang** (allaqachon qilingan)
3. **Git history'dan fayllarni o'chiring**
4. **Yangi commit qiling:**

```bash
git add .gitignore
git commit -m "Update .gitignore to exclude sensitive files"
git push
```

## Render'da Environment Variables

Render'da environment variables'ni qo'lda qo'shing (`.env` fayl emas):
- Render Dashboard → Your Service → Environment
- Har bir variable'ni qo'lda qo'shing

## Xavfsizlik Eslatmalari

- ✅ `.env` faylini hech qachon GitHub'ga yuklamang
- ✅ Secret key'larni hech qachon kodga yozmang
- ✅ Production'da environment variables ishlating
- ✅ `.gitignore` faylini doim tekshiring
- ✅ Git history'ni tozalang (agar kerak bo'lsa)

