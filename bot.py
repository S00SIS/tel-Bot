import random
import os
import time
import requests
import json
import sys
import math

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
START_TIME = time.time()
MAX_RUNTIME = 6 * 60 * 60

def check_time():
    if time.time() - START_TIME > MAX_RUNTIME:
        print("6 ساعت تموم شد، ربات خاموش میشه...")
        sys.exit(0)

def get_configs():
    with open('proxy.txt', 'r') as f:
        return [line.strip() for line in f if line.strip()]

def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text}
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

def pin_message(chat_id, message_id):
    """پین کردن پیام"""
    url = f"https://api.telegram.org/bot{TOKEN}/pinChatMessage"
    payload = {'chat_id': chat_id, 'message_id': message_id, 'disable_notification': True}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error pinning message: {e}")

def send_configs_in_chunks(chat_id, configs, total_count):
    """ارسال کانفیگ‌ها در گروه‌های 10 تایی"""
    chunk_size = 10
    num_chunks = math.ceil(len(configs) / chunk_size)
    
    for i in range(num_chunks):
        start = i * chunk_size
        end = start + chunk_size
        chunk = configs[start:end]
        
        if num_chunks == 1:
            message = "\n".join(chunk)
        else:
            if i == 0:
                message = f"📦 بخش {i+1} از {num_chunks} (کانفیگ {start+1} تا {min(end, total_count)}):\n\n" + "\n".join(chunk)
            else:
                message = f"\n📦 بخش {i+1} از {num_chunks} (کانفیگ {start+1} تا {min(end, total_count)}):\n\n" + "\n".join(chunk)
        
        send_message(chat_id, message)
        time.sleep(0.5)

def main():
    configs = get_configs()
    last_update_id = 0
    
    while True:
        check_time()
        
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            params = {'timeout': 30, 'offset': last_update_id + 1}
            response = requests.get(url, params=params, timeout=35)
            updates = response.json().get('result', [])
            
            for update in updates:
                check_time()
                last_update_id = update['update_id']
                
                # فقط پیام‌های واقعی رو پردازش کن (نه چیز دیگه)
                if 'message' not in update:
                    continue
                
                msg = update['message']
                
                # اگه پیام بدون متن بود، رد کن
                if 'text' not in msg:
                    continue
                
                chat_id = msg['chat']['id']
                text = msg.get('text', '')
                
                # پردازش دستور start
                if text == '/start':
                    welcome_text = f"""🎯 به ربات کانفیگ خوش آمدید!

این ربات به شما امکان دریافت کانفیگ‌های دلخواه را می‌دهد.

📌 نحوه استفاده:
✅ روی دکمه "📡 درخواست کانفیگ" که پایین صفحه قرار دارد کلیک کنید
✅ سپس تعداد کانفیگ مورد نیاز خود را وارد کنید (عدد بین 1 تا 50)

📊 آمار فعلی: {len(configs)} کانفیگ در مخزن موجود است.

⚠️ نکته: کانفیگ‌ها در گروه‌های ۱۰ تایی برای شما ارسال می‌شوند.

برای شروع، روی دکمه پایین صفحه کلیک کنید."""

                    reply_keyboard = {
                        "keyboard": [
                            [{"text": "📡 درخواست کانفیگ"}]
                        ],
                        "resize_keyboard": True,
                        "one_time_keyboard": False
                    }
                    
                    result = send_message(chat_id, welcome_text, reply_markup=reply_keyboard)
                    
                    if result and 'result' in result:
                        message_id = result['result']['message_id']
                        pin_message(chat_id, message_id)
                
                # پردازش دکمه دائمی
                elif text == "📡 درخواست کانفیگ":
                    send_message(chat_id, f"🔢 چند تا کانفیگ میخوای؟ (عدد بین 1 تا 50)\n\n📊 {len(configs)} کانفیگ در مخزن موجود است.\n\n⚠️ کانفیگ‌ها در گروه‌های ۱۰ تایی ارسال می‌شوند.")
                
                # پردازش عدد (تعداد کانفیگ)
                elif text.isdigit():
                    count = int(text)
                    if 1 <= count <= 50:
                        if count > len(configs):
                            send_message(chat_id, f"⚠️ فقط {len(configs)} کانفیگ در مخزن موجود است. همین تعداد ارسال می‌شود.")
                            count = len(configs)
                        
                        selected = random.sample(configs, count)
                        send_message(chat_id, f"✅ {count} کانفیگ درخواستی شما در حال ارسال است...")
                        time.sleep(0.5)
                        send_configs_in_chunks(chat_id, selected, count)
                        send_message(chat_id, f"✨ ارسال {count} کانفیگ به پایان رسید.")
                    else:
                        send_message(chat_id, "❌ لطفاً عددی بین 1 تا 50 وارد کنید.")
                
                # هر چیز دیگه ای (نه start، نه دکمه، نه عدد)
                else:
                    send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید.\n\nبرای شروع /start را بزنید یا از دکمه پایین صفحه استفاده کنید.")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
