"""
Telegram Mini App initData validatsiya
"""
import hmac
import hashlib
import json
import urllib.parse
from datetime import datetime, timedelta

def validate_telegram_init_data(init_data: str, bot_token: str) -> dict:
    """
    Telegram initData'ni validatsiya qiladi va user ma'lumotlarini qaytaradi
    
    Args:
        init_data: Telegram Mini App'dan kelgan initData string
        bot_token: Bot token (environment variable'dan olinadi)
    
    Returns:
        dict: User ma'lumotlari (user_id, username, va h.k.)
    
    Raises:
        ValueError: Agar validatsiya muvaffaqiyatsiz bo'lsa
    """
    try:
        # initData'ni parse qilish
        parsed_data = urllib.parse.parse_qs(init_data)
        
        # hash va data'ni ajratish
        received_hash = parsed_data.get('hash', [None])[0]
        if not received_hash:
            raise ValueError("Hash topilmadi")
        
        # hash'ni olib tashlash va qolgan data'ni tayyorlash
        data_check_string = []
        for key in sorted(parsed_data.keys()):
            if key != 'hash':
                value = parsed_data[key][0]
                data_check_string.append(f"{key}={value}")
        
        data_check_string = '\n'.join(data_check_string)
        
        # Secret key yaratish
        secret_key = hmac.new(
            "WebAppData".encode(),
            bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        # Hash'ni tekshirish
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if calculated_hash != received_hash:
            raise ValueError("Hash validatsiya muvaffaqiyatsiz")
        
        # Auth date'ni tekshirish (24 soatdan eski bo'lmasligi kerak)
        auth_date = int(parsed_data.get('auth_date', [0])[0])
        if auth_date:
            auth_datetime = datetime.fromtimestamp(auth_date)
            if datetime.now() - auth_datetime > timedelta(hours=24):
                raise ValueError("Auth date eskirgan")
        
        # User ma'lumotlarini parse qilish
        user_str = parsed_data.get('user', [None])[0]
        if user_str:
            user_data = json.loads(user_str)
            return {
                'user_id': user_data.get('id'),
                'username': user_data.get('username'),
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'language_code': user_data.get('language_code')
            }
        
        return {}
        
    except Exception as e:
        raise ValueError(f"Telegram auth validatsiya xatosi: {str(e)}")

